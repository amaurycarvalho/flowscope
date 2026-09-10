"""Provider de dados fundamentalistas do Fundamentus (RFC-011)."""

import logging
from collections.abc import Callable

from flowscope.domain.fii.fundamentus import AtivoFundamental
from flowscope.infrastructure.cache import CacheManager

from .client import FundamentusClient
from .parser import parse_ativo

logger = logging.getLogger("flowscope")

#: Fonte registrada nos objetos produzidos pelo provider.
FONTE_FUNDAMENTUS = "FUNDAMENTUS"

#: TTL do cache da página de detalhes.
_TTL_DIAS = 7


class FundamentusProvider:
    """Extrai o ``AtivoFundamental`` de um ticker a partir do Fundamentus."""

    def __init__(
        self: "FundamentusProvider",
        loader: Callable[[str], str] | None = None,
        cache: CacheManager | None = None,
        client: FundamentusClient | None = None,
    ) -> None:
        """Inicializa o provider com o loader, o cache e o cliente HTTP."""
        self._client = client or FundamentusClient()
        self._loader = loader or self._client.fetch
        self._cache = cache

    def get(self: "FundamentusProvider", ticker: str) -> AtivoFundamental:
        """Obtém e parseia os dados do ticker, propagando erros tipados."""
        html = self._carregar(ticker)
        return parse_ativo(ticker, html)

    def _carregar(self: "FundamentusProvider", ticker: str) -> str:
        """Carrega a página, usando o cache quando disponível."""
        normalizado = ticker.strip().upper()
        if self._cache is None:
            return self._loader(normalizado) or ""
        payload = self._cache.get_or_fetch(
            f"fundamentus_{normalizado}",
            ttl_days=_TTL_DIAS,
            fetch_fn=lambda: {"conteudo": self._loader(normalizado) or ""},
        )
        return str(payload.get("conteudo", ""))
