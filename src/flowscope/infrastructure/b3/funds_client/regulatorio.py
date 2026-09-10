"""Listagem de censuras públicas e condições excepcionais da B3."""

import logging

import requests

from flowscope.infrastructure.b3.funds_client.constants import (
    _CENSURAS_URL,
    _CONDICOES_URL,
    TTL_PAGINA_ESTATICA_DIAS,
)
from flowscope.infrastructure.b3.structured_parser import (
    extrair_censuras,
    extrair_condicoes_excepcionais,
)

logger = logging.getLogger(__name__)


class FundosRegulatorioMixin:
    """Mixin com listagem de páginas estáticas regulatórias da B3."""

    def listar_censuras(self: "FundosRegulatorioMixin") -> list:
        """Lista as censuras públicas da página da B3, com cache de 7 dias."""
        html = self._html_cacheado(
            "censuras_publicas", _CENSURAS_URL, "página de censuras públicas"
        )
        return extrair_censuras(html)

    def listar_condicoes_excepcionais(self: "FundosRegulatorioMixin") -> list:
        """Lista as condições excepcionais da página da B3, com cache de 7 dias."""
        html = self._html_cacheado(
            "condicoes_excepcionais",
            _CONDICOES_URL,
            "página de condições excepcionais",
        )
        return extrair_condicoes_excepcionais(html)

    def _html_cacheado(self: "FundosRegulatorioMixin", key: str, url: str, descricao: str) -> str:
        """Baixa e cacheia o HTML de uma página estática da B3 por 7 dias."""
        def _fetch() -> dict[str, object]:
            logger.info("Baixando %s", url)
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return {"html": resp.text}

        try:
            payload = self._cache.get_or_fetch(key, ttl_days=TTL_PAGINA_ESTATICA_DIAS, fetch_fn=_fetch)
        except requests.RequestException as e:
            raise RuntimeError(f"Não foi possível acessar a {descricao}: {e}") from e
        return str(payload.get("html") or "")
