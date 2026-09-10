"""Provider de histórico de proventos do Fundamentus.

Implementa a porta ``DividendHistoryProvider`` lendo a página
``proventos.php?papel={TICKER}`` e normalizando as linhas em
``DividendoConsolidado`` com a origem Fundamentus.
"""

import logging
from collections.abc import Callable
from datetime import date

from flowscope.domain.fii.dividends import DividendoConsolidado
from flowscope.infrastructure.cache import CacheManager

from .client import FundamentusClient
from .parser import parse_proventos
from .provider import FONTE_FUNDAMENTUS

logger = logging.getLogger("flowscope")

#: TTL padrão do cache do histórico de proventos, em dias.
_TTL_DIAS = 1


class FundamentusDividendHistoryProvider:
    """Fornece o histórico de proventos de um ticker a partir do Fundamentus."""

    def __init__(
        self: "FundamentusDividendHistoryProvider",
        loader: Callable[[str], str] | None = None,
        client: FundamentusClient | None = None,
        cache: CacheManager | None = None,
        ttl_days: int = _TTL_DIAS,
    ) -> None:
        """Inicializa o provider com o loader, o cliente e o cache opcional."""
        self._client = client or FundamentusClient()
        self._loader = loader or self._client.fetch_proventos
        self._cache = cache
        self._ttl_days = ttl_days

    def obter_dividendos(
        self: "FundamentusDividendHistoryProvider",
        ticker: str,
        reference_date: date,
    ) -> list[DividendoConsolidado]:
        """Retorna os dividendos do ticker até a data de referência."""
        html = self._carregar(ticker)
        if not html:
            return []
        return [
            dividendo
            for dividendo in parse_proventos(html, FONTE_FUNDAMENTUS)
            if dividendo.data_base is None
            or dividendo.data_base <= reference_date
        ]

    def _carregar(
        self: "FundamentusDividendHistoryProvider", ticker: str
    ) -> str:
        """Carrega o HTML dos proventos, usando cache quando disponível."""
        normalizado = ticker.strip().upper()
        if self._cache is None:
            return self._loader(normalizado)

        def _fetch() -> dict[str, object]:
            return {"html": self._loader(normalizado) or ""}

        payload = self._cache.get_or_fetch(
            f"fundamentus_proventos_{normalizado}",
            self._ttl_days,
            _fetch,
        )
        return str(payload.get("html") or "")
