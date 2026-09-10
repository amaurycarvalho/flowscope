"""Validadores HTTP e por data do cache condicional."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from datetime import date

from flowscope.infrastructure.conditional_cache_types import (
    DATA_ULTIMA_COTACAO,
    ETAG,
    LAST_MODIFIED,
    CacheRecord,
    RemoteResponse,
    RevalidationResult,
    RevalidationStatus,
    _parse_iso_date,
    headers_to_validators,
)

logger = logging.getLogger("flowscope")


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
