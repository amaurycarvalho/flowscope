"""Cache condicional com validadores plugáveis (change conditional-cache-fundamentus-cvm).

Separa as políticas de *frescor* (idade máxima para servir sem rede),
*revalidação* (checagem barata contra a fonte remota, com coalescência) e
*retenção* (quando evictar do armazenamento). Os validadores decidem se o
valor remoto permanece igual, mudou ou não pôde ser verificado, e o resultado
de cada consulta é reportado ao chamador via ``CacheOutcome``.

Os tipos e validadores vivem em módulos próprios e são reexportados aqui para
preservar o caminho de importação histórico.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import (
    _RETENTION_PADRAO,
    _ZERO,
    CONTENT_LENGTH,
    DATA_ULTIMA_COTACAO,
    ETAG,
    LAST_MODIFIED,
    REVALIDATED_AT,
    CacheOutcome,
    CacheRecord,
    CacheResult,
    Fetched,
    FileCacheResult,
    RemoteResponse,
    RevalidationResult,
    RevalidationStatus,
    Validator,
    _atomic_write_bytes,
    _parse_datetime,
    headers_to_validators,
)
from flowscope.infrastructure.conditional_cache_validators import (
    DateValidator,
    HttpValidator,
)

logger = logging.getLogger("flowscope")


class ConditionalCache:
    """Cache em disco com revalidação condicional e políticas independentes."""

    def __init__(
        self: ConditionalCache,
        cache: CacheManager | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        """Inicializa o cache condicional com o armazenamento e o relógio."""
        self._cache = cache
        self._now = now or (lambda: datetime.now(timezone.utc))

    @property
    def cache(self: ConditionalCache) -> CacheManager:
        """Retorna o ``CacheManager`` subjacente, criando-o quando necessário."""
        if self._cache is None:
            self._cache = CacheManager()
        return self._cache

    def get_or_revalidate(
        self: ConditionalCache,
        key: str,
        *,
        fetch: Callable[[], Fetched],
        validators: Sequence[Validator] = (),
        parser_version: str = "",
        freshness: timedelta = _ZERO,
        revalidate_after: timedelta = _ZERO,
        retention: timedelta = _RETENTION_PADRAO,
        safety_ttl: timedelta | None = None,
        force_refresh: bool = False,
    ) -> CacheResult:
        """Devolve o valor, revalidando a fonte conforme as políticas."""
        record = self._load(key, parser_version, retention)
        if force_refresh or record is None:
            outcome = CacheOutcome.UPDATED if record is not None else CacheOutcome.MISS
            return self._fetch_and_store(
                key, fetch, parser_version, outcome=outcome
            )

        agora = self._now()
        if agora - record.fetched_at <= freshness:
            return CacheResult(record.payload, CacheOutcome.HIT)

        if safety_ttl is not None and agora - record.fetched_at > safety_ttl:
            return self._fetch_and_store(
                key, fetch, parser_version, outcome=CacheOutcome.UPDATED
            )

        revalidado_em = _parse_datetime(record.validators.get(REVALIDATED_AT))
        if (
            revalidado_em is not None
            and agora - revalidado_em < revalidate_after
        ):
            return CacheResult(record.payload, CacheOutcome.HIT)

        resultado = self._run_validators(record, validators)
        if resultado is not None:
            if resultado.status is RevalidationStatus.CHANGED:
                payload = (
                    resultado.payload if resultado.payload is not None else record.payload
                )
                return self._store(
                    key,
                    Fetched(payload, resultado.validators),
                    parser_version,
                    CacheOutcome.UPDATED,
                )
            return self._touch(key, record, resultado.validators)

        try:
            return self._fetch_and_store(
                key, fetch, parser_version, outcome=CacheOutcome.UPDATED
            )
        except Exception:  # revalidação indisponível: serve o cache local
            logger.warning(
                "Revalidação indisponível para %s; servindo cache", key, exc_info=True
            )
            return CacheResult(record.payload, CacheOutcome.HIT)

    def get_file_or_revalidate(
        self: ConditionalCache,
        path: Path,
        *,
        fetch: Callable[[], tuple[bytes, Mapping[str, str]]],
        probe: Callable[[Mapping[str, str]], RevalidationResult] | None = None,
        read_validators: Callable[[], Mapping[str, str]] | None = None,
        write_metadata: Callable[[bytes, Mapping[str, str], datetime], None] | None = None,
        revalidate_after: timedelta = _ZERO,
        force_refresh: bool = False,
    ) -> FileCacheResult:
        """Devolve o arquivo, revalidando a fonte remota antes de reutilizá-lo."""
        caminho = Path(path)
        armazenados = dict(read_validators() if read_validators else {})
        existe = caminho.exists()

        if force_refresh or not existe:
            data, validators = fetch()
            _atomic_write_bytes(caminho, data)
            if write_metadata is not None:
                write_metadata(data, validators, self._now())
            outcome = CacheOutcome.UPDATED if existe else CacheOutcome.MISS
            return FileCacheResult(data, outcome, validators)

        if probe is None:
            return FileCacheResult(caminho.read_bytes(), CacheOutcome.HIT, armazenados)

        revalidado_em = _parse_datetime(armazenados.get(REVALIDATED_AT))
        if revalidado_em is not None and self._now() - revalidado_em < revalidate_after:
            return FileCacheResult(caminho.read_bytes(), CacheOutcome.HIT, armazenados)

        try:
            resultado = probe(armazenados)
        except Exception:  # falha de rede: stale-on-failure
            logger.warning(
                "Falha ao revalidar %s; usando arquivo local", caminho, exc_info=True
            )
            return FileCacheResult(caminho.read_bytes(), CacheOutcome.HIT, armazenados)

        if resultado.status is RevalidationStatus.CHANGED:
            data, validators = fetch()
            _atomic_write_bytes(caminho, data)
            if write_metadata is not None:
                write_metadata(data, validators, self._now())
            return FileCacheResult(data, CacheOutcome.UPDATED, validators)

        mesclados = {**armazenados, **resultado.validators}
        if resultado.status is RevalidationStatus.UNCHANGED:
            if write_metadata is not None:
                write_metadata(caminho.read_bytes(), mesclados, self._now())
            return FileCacheResult(
                caminho.read_bytes(), CacheOutcome.REVALIDATED, mesclados
            )
        return FileCacheResult(caminho.read_bytes(), CacheOutcome.HIT, mesclados)

    def _load(
        self: ConditionalCache, key: str, parser_version: str, retention: timedelta
    ) -> CacheRecord | None:
        """Carrega o registro, tratando versão divergente, retenção ou corrupção como miss."""
        dados = self.cache.read_meta(key)
        if dados is None:
            return None
        try:
            record = CacheRecord(
                payload=dados["payload"],
                validators=dict(dados.get("validators") or {}),
                fetched_at=_parse_datetime(dados.get("fetched_at"))
                or datetime.now(timezone.utc),
                parser_version=str(dados.get("parser_version") or ""),
            )
        except (KeyError, TypeError, ValueError):
            return None
        if record.parser_version != parser_version:
            return None
        if self._now() - record.fetched_at > retention:
            self.cache.invalidate(key)
            return None
        return record

    def _run_validators(
        self: ConditionalCache,
        record: CacheRecord,
        validators: Sequence[Validator],
    ) -> RevalidationResult | None:
        """Executa os validadores e devolve o primeiro resultado definitivo."""
        for validador in validators:
            resultado = validador.revalidate(record)
            if resultado.status is not RevalidationStatus.UNKNOWN:
                return resultado
        return None

    def _fetch_and_store(
        self: ConditionalCache,
        key: str,
        fetch: Callable[[], Fetched],
        parser_version: str,
        *,
        outcome: CacheOutcome,
    ) -> CacheResult:
        """Obtém o valor da fonte, armazena e devolve o resultado."""
        return self._store(key, fetch(), parser_version, outcome)

    def _store(
        self: ConditionalCache,
        key: str,
        fetched: Fetched,
        parser_version: str,
        outcome: CacheOutcome,
    ) -> CacheResult:
        """Grava um novo registro com os validadores informados."""
        agora = self._now()
        validators = {**fetched.validators, REVALIDATED_AT: agora.isoformat()}
        self.cache.write_meta(
            key,
            {
                "payload": fetched.payload,
                "validators": validators,
                "fetched_at": agora.isoformat(),
                "parser_version": parser_version,
            },
        )
        return CacheResult(fetched.payload, outcome)

    def _touch(
        self: ConditionalCache,
        key: str,
        record: CacheRecord,
        validators: Mapping[str, str],
    ) -> CacheResult:
        """Atualiza apenas os metadados de revalidação, preservando o conteúdo."""
        agora = self._now()
        mesclados = {
            **record.validators,
            **validators,
            REVALIDATED_AT: agora.isoformat(),
        }
        self.cache.write_meta(
            key,
            {
                "payload": record.payload,
                "validators": mesclados,
                "fetched_at": record.fetched_at.isoformat(),
                "parser_version": record.parser_version,
            },
        )
        return CacheResult(record.payload, CacheOutcome.REVALIDATED)


__all__ = [
    "CONTENT_LENGTH",
    "DATA_ULTIMA_COTACAO",
    "ETAG",
    "LAST_MODIFIED",
    "REVALIDATED_AT",
    "CacheOutcome",
    "CacheRecord",
    "CacheResult",
    "ConditionalCache",
    "DateValidator",
    "Fetched",
    "FileCacheResult",
    "HttpValidator",
    "RemoteResponse",
    "RevalidationResult",
    "RevalidationStatus",
    "Validator",
    "headers_to_validators",
]
