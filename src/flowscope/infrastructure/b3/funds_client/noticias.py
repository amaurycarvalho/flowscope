"""Listagem de notícias do Plantão B3."""

import logging
from datetime import date, datetime, timedelta, timezone

import requests

from flowscope.domain.structured import NoticiaB3
from flowscope.infrastructure.b3.funds_client.constants import (
    _AGENCIA_PADRAO,
    _NOTICIAS_URL,
    TTL_NOTICIAS_DIAS,
)
from flowscope.infrastructure.b3.funds_client.noticias_convert import (
    _converter_item_noticia,
    _itens_de_noticias,
)

logger = logging.getLogger(__name__)


class FundosNoticiasMixin:
    """Mixin com listagem paginada de notícias do Plantão B3."""

    def listar_noticias(
        self: "FundosNoticiasMixin",
        agencia: str = _AGENCIA_PADRAO,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        palavra: str | None = None,
    ) -> list[NoticiaB3]:
        """Lista notícias do Plantão B3 no período e com filtro informados.

        Sem período informado, consulta os últimos 30 dias. O resultado é
        cacheado por cerca de 1 hora, usando o horário na chave de cache.
        """
        hoje = datetime.now(timezone.utc).date()
        data_inicial = data_inicio or hoje - timedelta(days=30)
        data_final = data_fim or hoje
        palavra_filtro = palavra or ""
        hora = datetime.now(timezone.utc).strftime("%Y%m%d%H")
        key = (
            f"noticias_{agencia}_{data_inicial.isoformat()}_"
            f"{data_final.isoformat()}_{palavra_filtro}_{hora}"
        )

        def _fetch() -> dict[str, object]:
            itens = self._coletar_noticias(
                agencia, data_inicial, data_final, palavra_filtro
            )
            return {"noticias": itens}

        try:
            payload = self._cache.get_or_fetch(key, ttl_days=TTL_NOTICIAS_DIAS, fetch_fn=_fetch)
        except requests.RequestException:
            logger.warning("Falha ao listar notícias da B3", exc_info=True)
            return []
        itens = payload.get("noticias") or []
        return [
            _converter_item_noticia(item, agencia=agencia)
            for item in itens
            if isinstance(item, dict)
        ]

    def _coletar_noticias(
        self: "FundosNoticiasMixin",
        agencia: str,
        data_inicial: date,
        data_final: date,
        palavra: str,
    ) -> list[dict]:
        """Coleta as notícias brutas, paginando quando a API informar páginas."""
        parametros: dict[str, object] = {
            "agencia": agencia,
            "palavra": palavra,
            "dataInicial": data_inicial.isoformat(),
            "dataFinal": data_final.isoformat(),
        }

        def _buscar() -> object:
            logger.info("Consultando %s", _NOTICIAS_URL)
            resp = requests.get(_NOTICIAS_URL, params=parametros, timeout=30)
            resp.raise_for_status()
            return resp.json()

        dados = _buscar()
        itens = _itens_de_noticias(dados)
        pagina = dados.get("page", {}) if isinstance(dados, dict) else {}
        total_pages = int(pagina.get("totalPages", 1) or 1) if pagina else 1
        for page_number in range(2, total_pages + 1):
            parametros["pageNumber"] = page_number
            itens.extend(_itens_de_noticias(_buscar()))
        return itens
