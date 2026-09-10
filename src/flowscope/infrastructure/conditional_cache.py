"""Cache condicional com validadores plugáveis (change conditional-cache-fundamentus-cvm).

Separa as políticas de *frescor* (idade máxima para servir sem rede),
*revalidação* (checagem barata contra a fonte remota, com coalescência) e
*retenção* (quando evictar do armazenamento). Os validadores decidem se o
valor remoto permanece igual, mudou ou não pôde ser verificado, e o resultado
de cada consulta é reportado ao chamador via ``CacheOutcome``.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Protocol

from flowscope.infrastructure.cache import CacheManager

logger = logging.getLogger("flowscope")

#: Chaves de validação HTTP reconhecidas pelos validadores e metadados.
ETAG = "etag"
LAST_MODIFIED = "last_modified"
CONTENT_LENGTH = "content_length"
DATA_ULTIMA_COTACAO = "data_ultima_cotacao"
REVALIDATED_AT = "revalidated_at"

#: Políticas padrão do cache condicional.
_ZERO = timedelta(0)
_RETENTION_PADRAO = timedelta(days=30)


class RevalidationStatus(Enum):
    """Resultado da checagem de um validador contra a fonte remota."""

    UNCHANGED = "unchanged"
    CHANGED = "changed"
    UNKNOWN = "unknown"


class CacheOutcome(Enum):
    """Resultado de uma consulta ao cache condicional."""

    HIT = "hit"
    REVALIDATED = "revalidated"
    UPDATED = "updated"
    MISS = "miss"


@dataclass(frozen=True)
class RevalidationResult:
    """Decisão de um validador e os validadores atualizados."""

    status: RevalidationStatus
    payload: object | None = None
    validators: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Fetched:
    """Conteúdo recém-obtido da fonte e os validadores que o acompanham."""

    payload: object
    validators: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CacheRecord:
    """Registro armazenado, com conteúdo, validadores e versão do parser."""

    payload: object
    validators: Mapping[str, str] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    parser_version: str = ""


@dataclass(frozen=True)
class CacheResult:
    """Valor devolvido pelo cache e o resultado da consulta."""

    value: object
    outcome: CacheOutcome


@dataclass(frozen=True)
class FileCacheResult:
    """Arquivo devolvido pelo cache condicional de arquivos."""

    data: bytes
    outcome: CacheOutcome
    validators: Mapping[str, str] = field(default_factory=dict)


class RemoteResponse(Protocol):
    """Resposta mínima de uma requisição HTTP usada pelos validadores."""

    status_code: int
    text: str
    headers: Mapping[str, str]


class Validator(Protocol):
    """Contrato de um validador de cache."""

    def revalidate(self: Validator, record: CacheRecord) -> RevalidationResult:
        """Compara o registro armazenado com a fonte remota."""
        ...


def headers_to_validators(headers: Mapping[str, str]) -> dict[str, str]:
    """Extrai os validadores HTTP relevantes dos cabeçalhos de resposta."""
    validators: dict[str, str] = {}
    if headers.get("ETag"):
        validators[ETAG] = str(headers["ETag"])
    if headers.get("Last-Modified"):
        validators[LAST_MODIFIED] = str(headers["Last-Modified"])
    if headers.get("Content-Length"):
        validators[CONTENT_LENGTH] = str(headers["Content-Length"])
    return validators


def _parse_iso_date(valor: object) -> date | None:
    """Interpreta uma data ISO armazenada em validadores, ou ``None``."""
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _parse_datetime(valor: object) -> datetime | None:
    """Interpreta um instante ISO, normalizando para UTC, ou ``None``."""
    if not valor:
        return None
    try:
        instante = datetime.fromisoformat(str(valor))
    except ValueError:
        return None
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=timezone.utc)
    return instante.astimezone(timezone.utc)


class HttpValidator:
    """Revalida por ``ETag``/``Last-Modified``, tratando ``304`` como inalterado."""

    def __init__(
        self: HttpValidator,
        fetch: Callable[[Mapping[str, str]], RemoteResponse],
    ) -> None:
        """Inicializa o validador com a função de requisição condicional."""
        self._fetch = fetch

    def revalidate(self: HttpValidator, record: CacheRecord) -> RevalidationResult:
        """Consulta a fonte e decide se o registro permanece válido."""
        if not record.validators.get(ETAG) and not record.validators.get(LAST_MODIFIED):
            return RevalidationResult(RevalidationStatus.UNKNOWN)
        try:
            response = self._fetch(record.validators)
        except Exception:  # falha de rede: verificação indisponível
            logger.warning("Falha ao revalidar cache via HTTP", exc_info=True)
            return RevalidationResult(RevalidationStatus.UNKNOWN)
        validators = headers_to_validators(response.headers)
        if response.status_code == 304:
            return RevalidationResult(
                RevalidationStatus.UNCHANGED, validators=validators
            )
        if 200 <= response.status_code < 300:
            return RevalidationResult(
                RevalidationStatus.CHANGED,
                payload=response.text,
                validators=validators,
            )
        return RevalidationResult(RevalidationStatus.UNKNOWN)


class DateValidator:
    """Compara a data de cotação remota com a data armazenada no registro."""

    def __init__(
        self: DateValidator,
        fetch: Callable[[Mapping[str, str]], RemoteResponse],
        extract_date: Callable[[str], date | None],
    ) -> None:
        """Inicializa o validador com a requisição e o extrator de data."""
        self._fetch = fetch
        self._extract_date = extract_date

    def revalidate(self: DateValidator, record: CacheRecord) -> RevalidationResult:
        """Consulta a fonte e compara a data de cotação com a armazenada."""
        try:
            response = self._fetch(record.validators)
        except Exception:  # falha de rede: verificação indisponível
            logger.warning("Falha ao revalidar cache pela data", exc_info=True)
            return RevalidationResult(RevalidationStatus.UNKNOWN)
        validators = headers_to_validators(response.headers)
        if response.status_code == 304:
            return RevalidationResult(
                RevalidationStatus.UNCHANGED, validators=validators
            )
        if not 200 <= response.status_code < 300:
            return RevalidationResult(RevalidationStatus.UNKNOWN)
        remota = self._extract_date(response.text)
        armazenada = _parse_iso_date(record.validators.get(DATA_ULTIMA_COTACAO))
        if remota is None or armazenada is None:
            return RevalidationResult(
                RevalidationStatus.UNKNOWN,
                payload=response.text,
                validators=validators,
            )
        validators = {**validators, DATA_ULTIMA_COTACAO: remota.isoformat()}
        if remota <= armazenada:
            return RevalidationResult(
                RevalidationStatus.UNCHANGED, validators=validators
            )
        return RevalidationResult(
            RevalidationStatus.CHANGED,
            payload=response.text,
            validators=validators,
        )


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


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """Grava bytes de forma atômica, com arquivo temporário e rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.rename(path)
