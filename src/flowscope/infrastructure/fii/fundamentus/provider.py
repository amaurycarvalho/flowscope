"""Provider de dados fundamentalistas do Fundamentus (RFC-011).

Usa cache condicional (change conditional-cache-fundamentus-cvm) quando um
``CacheManager`` é fornecido: revalida o snapshot pela ``Data últ cot``
(primário) e por validadores HTTP (secundário), com coalescência e TTL de
segurança. Sem cache, o comportamento é o de sempre: baixar e parsear.
"""

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from flowscope.domain.fii.fundamentus import AtivoFundamental
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache import (
    DATA_ULTIMA_COTACAO,
    ETAG,
    LAST_MODIFIED,
    CacheOutcome,
    ConditionalCache,
    DateValidator,
    Fetched,
    HttpValidator,
)

from .client import FundamentusClient
from .parser import extrair_data_ultima_cotacao, parse_ativo

logger = logging.getLogger("flowscope")

#: Fonte registrada nos objetos produzidos pelo provider.
FONTE_FUNDAMENTUS = "FUNDAMENTUS"

#: Versão do parser do Fundamentus, usada para invalidar caches antigos.
PARSER_VERSION = "fundamentus-v1"

#: Políticas de cache condicional do Fundamentus.
_FRESHNESS = timedelta(hours=1)
_REVALIDATE_AFTER = timedelta(hours=1)
_SAFETY_TTL = timedelta(hours=24)
_RETENTION = timedelta(days=30)


@dataclass(frozen=True)
class _SimpleResponse:
    """Resposta mínima usada quando um loader textual é injetado nos testes."""

    status_code: int
    text: str
    headers: Mapping[str, str]


class FundamentusProvider:
    """Extrai o ``AtivoFundamental`` de um ticker a partir do Fundamentus."""

    def __init__(
        self: "FundamentusProvider",
        loader: Callable[[str], str] | None = None,
        cache: CacheManager | None = None,
        client: FundamentusClient | None = None,
        conditional_cache: ConditionalCache | None = None,
        parser_version: str = PARSER_VERSION,
        freshness: timedelta = _FRESHNESS,
        revalidate_after: timedelta = _REVALIDATE_AFTER,
        safety_ttl: timedelta | None = _SAFETY_TTL,
        retention: timedelta = _RETENTION,
    ) -> None:
        """Inicializa o provider com o loader, o cache e o cliente HTTP."""
        self._client = client or FundamentusClient()
        self._custom_loader = loader is not None
        self._loader = loader or self._client.fetch
        self._cache = cache
        self._conditional = conditional_cache
        if self._conditional is None and cache is not None:
            self._conditional = ConditionalCache(cache=cache)
        self._parser_version = parser_version
        self._freshness = freshness
        self._revalidate_after = revalidate_after
        self._safety_ttl = safety_ttl
        self._retention = retention

    def get(self: "FundamentusProvider", ticker: str) -> AtivoFundamental:
        """Obtém e parseia os dados do ticker, propagando erros tipados."""
        ativo, _ = self.get_with_outcome(ticker)
        return ativo

    def get_with_outcome(
        self: "FundamentusProvider", ticker: str, force_refresh: bool = False
    ) -> tuple[AtivoFundamental, CacheOutcome]:
        """Obtém o ativo e o resultado do cache (hit/revalidado/atualizado)."""
        html, resultado = self._carregar_com_resultado(ticker, force_refresh)
        return parse_ativo(ticker.strip().upper(), html), resultado

    def _carregar(self: "FundamentusProvider", ticker: str) -> str:
        """Carrega a página, usando o cache condicional quando disponível."""
        html, _ = self._carregar_com_resultado(ticker, force_refresh=False)
        return html

    def _carregar_com_resultado(
        self: "FundamentusProvider", ticker: str, force_refresh: bool
    ) -> tuple[str, CacheOutcome]:
        """Carrega a página e reporta o resultado do cache."""
        normalizado = ticker.strip().upper()
        if self._conditional is None:
            return self._loader(normalizado) or "", CacheOutcome.MISS
        resultado = self._conditional.get_or_revalidate(
            f"fundamentus_{normalizado}",
            fetch=lambda: self._fetch_fresh(normalizado),
            validators=self._validators(normalizado),
            parser_version=self._parser_version,
            freshness=self._freshness,
            revalidate_after=self._revalidate_after,
            safety_ttl=self._safety_ttl,
            retention=self._retention,
            force_refresh=force_refresh,
        )
        return str(resultado.value), resultado.outcome

    def _validators(self: "FundamentusProvider", ticker: str) -> list:
        """Monta os validadores: data de cotação (primário) e HTTP (secundário)."""
        fetch = self._remote_fetch(ticker)
        return [DateValidator(fetch, extrair_data_ultima_cotacao), HttpValidator(fetch)]

    def _remote_fetch(
        self: "FundamentusProvider", ticker: str
    ) -> Callable[[Mapping[str, str]], object]:
        """Devolve a função de requisição condicional usada pelos validadores."""
        if self._custom_loader:

            def _fetch(_validators: Mapping[str, str]) -> _SimpleResponse:
                return _SimpleResponse(200, self._loader(ticker) or "", {})

            return _fetch

        def _fetch(validators: Mapping[str, str]) -> object:
            return self._client.fetch_response(
                ticker,
                etag=validators.get(ETAG),
                last_modified=validators.get(LAST_MODIFIED),
            )

        return _fetch

    def _fetch_fresh(self: "FundamentusProvider", ticker: str) -> Fetched:
        """Obtém o HTML da fonte e os validadores que o acompanham."""
        if self._custom_loader:
            html = self._loader(ticker) or ""
            return Fetched(html, self._validators_do_html(html))
        resposta = self._client.fetch_response(ticker)
        return Fetched(resposta.text, self._validators_da_resposta(resposta))

    @staticmethod
    def _validators_do_html(html: str) -> dict[str, str]:
        """Extrai a data de cotação do HTML como validador."""
        data = extrair_data_ultima_cotacao(html)
        return _validadores_de_data(data)

    @staticmethod
    def _validators_da_resposta(resposta: object) -> dict[str, str]:
        """Extrai validadores HTTP e a data de cotação de uma resposta."""
        headers = getattr(resposta, "headers", {}) or {}
        validators: dict[str, str] = {}
        if headers.get("ETag"):
            validators[ETAG] = str(headers["ETag"])
        if headers.get("Last-Modified"):
            validators[LAST_MODIFIED] = str(headers["Last-Modified"])
        data = extrair_data_ultima_cotacao(getattr(resposta, "text", "") or "")
        validators.update(_validadores_de_data(data))
        return validators


def _validadores_de_data(data: date | None) -> dict[str, str]:
    """Extrai o validador de data de cotação, quando presente."""
    if data is None:
        return {}
    return {DATA_ULTIMA_COTACAO: data.isoformat()}
