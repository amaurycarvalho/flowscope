"""Listagem de material facts (fatos relevantes e avisos) da B3."""

import logging
from datetime import date

import requests

from flowscope.domain.structured import CategoriaMaterialFact, DocumentoMaterialFact
from flowscope.infrastructure.b3.funds_client.constants import (
    _PAGE_SIZE,
    TTL_MATERIAL_FACTS_DIAS,
)
from flowscope.infrastructure.b3.funds_client.material_facts_convert import (
    _codigo_categoria,
    _converter_item_material_fact,
)

logger = logging.getLogger(__name__)


class FundosMaterialFactsMixin:
    """Mixin com listagem paginada de material facts por categoria."""

    def listar_fatos_relevantes(
        self: "FundosMaterialFactsMixin",
        code_cvm: str,
        categoria: CategoriaMaterialFact | str,
        data_inicio: date,
        data_fim: date,
        ticker: str = "",
    ) -> list[DocumentoMaterialFact]:
        """Lista documentos do ``GetMaterialFacts`` paginando todas as páginas.

        A categoria é validada antes de qualquer requisição HTTP. O resultado
        é cacheado por 1 dia usando a chave composta por ``codeCVM``,
        ``categoria`` e período.
        """
        codigo_categoria = _codigo_categoria(categoria)
        key = (
            f"matfacts_{code_cvm}_{codigo_categoria}_"
            f"{data_inicio.isoformat()}_{data_fim.isoformat()}"
        )

        def _fetch() -> dict[str, object]:
            itens = self._coletar_paginas_material_facts(
                code_cvm, codigo_categoria, data_inicio, data_fim
            )
            return {"results": itens}

        try:
            payload = self._cache.get_or_fetch(key, ttl_days=TTL_MATERIAL_FACTS_DIAS, fetch_fn=_fetch)
        except requests.RequestException:
            logger.warning(
                "Falha ao listar fatos relevantes do codeCVM %s", code_cvm,
                exc_info=True,
            )
            return []
        resultados = payload.get("results") or []
        return [
            _converter_item_material_fact(item, ticker=ticker, code_cvm=code_cvm)
            for item in resultados
            if isinstance(item, dict)
        ]

    def _coletar_paginas_material_facts(
        self: "FundosMaterialFactsMixin",
        code_cvm: str,
        codigo_categoria: str,
        data_inicio: date,
        data_fim: date,
    ) -> list[dict]:
        """Coleta os itens brutos de todas as páginas do ``GetMaterialFacts``."""
        resultados: list[dict] = []
        page_number = 1
        while True:
            dados = self._get_listed_json(
                "GetMaterialFacts",
                {
                    "language": "pt-br",
                    "codeCVM": code_cvm,
                    "year": data_inicio.year,
                    "dateInitial": data_inicio.isoformat(),
                    "dateFinal": data_fim.isoformat(),
                    "category": codigo_categoria,
                    "pageNumber": page_number,
                    "pageSize": _PAGE_SIZE,
                },
            )
            pagina = dados.get("page", {}) if isinstance(dados, dict) else {}
            itens = dados.get("results") if isinstance(dados, dict) else []
            if isinstance(itens, list):
                resultados.extend(item for item in itens if isinstance(item, dict))
            total_pages = int(pagina.get("totalPages", 1) or 1) if pagina else 1
            if page_number >= total_pages:
                break
            page_number += 1
        return resultados
