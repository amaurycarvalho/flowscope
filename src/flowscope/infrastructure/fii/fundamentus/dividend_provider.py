"""Provider de histórico de proventos do Fundamentus.

Implementa a porta ``DividendHistoryProvider`` lendo a página de ações
``proventos.php?papel={TICKER}`` e, quando ela não retornar proventos, a página
de FII/FIAGRO ``fii_proventos.php?papel={TICKER}``, normalizando as linhas em
``DividendoConsolidado`` com a origem Fundamentus.
"""

import logging
from collections.abc import Callable
from datetime import date

from flowscope.domain.fii.dividends import DividendoConsolidado
from flowscope.infrastructure.cache import CacheManager

from .client import FundamentusClient
from .parser import parse_proventos, parse_proventos_fii
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
        fii_loader: Callable[[str], str] | None = None,
    ) -> None:
        """Inicializa o provider com os loaders, o cliente e o cache opcional."""
        self._client = client or FundamentusClient()
        self._loader = loader or self._client.fetch_proventos
        self._fii_loader = fii_loader or self._client.fetch_fii_proventos
        self._cache = cache
        self._ttl_days = ttl_days

    def obter_dividendos(
        self: "FundamentusDividendHistoryProvider",
        ticker: str,
        reference_date: date,
    ) -> list[DividendoConsolidado]:
        """Retorna os dividendos do ticker até a data de referência.

        Consulta primeiro a página de ações e, se ela não retornar proventos,
        consulta a página de rendimentos de FII/FIAGRO.
        """
        dividendos = self._parse(self._carregar(ticker), parse_proventos)
        if not dividendos:
            dividendos = self._parse(
                self._carregar_fii(ticker), parse_proventos_fii
            )
        return [
            dividendo
            for dividendo in dividendos
            if dividendo.data_base is None
            or dividendo.data_base <= reference_date
        ]

    def _parse(
        self: "FundamentusDividendHistoryProvider",
        html: str,
        parser: Callable[[str, str], list[DividendoConsolidado]],
    ) -> list[DividendoConsolidado]:
        """Interpreta o HTML quando presente, ou retorna lista vazia."""
        if not html:
            return []
        return parser(html, FONTE_FUNDAMENTUS)

    def _carregar(
        self: "FundamentusDividendHistoryProvider", ticker: str
    ) -> str:
        """Carrega o HTML dos proventos de ações, usando cache quando disponível."""
        return self._carregar_pagina(ticker, "proventos", self._loader)

    def _carregar_fii(
        self: "FundamentusDividendHistoryProvider", ticker: str
    ) -> str:
        """Carrega o HTML dos rendimentos de FII, usando cache quando disponível."""
        return self._carregar_pagina(ticker, "fii_proventos", self._fii_loader)

    def _carregar_pagina(
        self: "FundamentusDividendHistoryProvider",
        ticker: str,
        sufixo: str,
        loader: Callable[[str], str],
    ) -> str:
        """Carrega uma página do Fundamentus, usando cache quando disponível."""
        normalizado = ticker.strip().upper()
        if self._cache is None:
            return loader(normalizado)

        def _fetch() -> dict[str, object]:
            return {"html": loader(normalizado) or ""}

        payload = self._cache.get_or_fetch(
            f"fundamentus_{sufixo}_{normalizado}",
            self._ttl_days,
            _fetch,
        )
        return str(payload.get("html") or "")
