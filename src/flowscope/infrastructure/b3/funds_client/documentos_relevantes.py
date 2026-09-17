"""Listagem de documentos relevantes (PDF) e download dos arquivos."""

import logging
from datetime import date

import requests

from flowscope.domain.structured import CATEGORIAS_RELEVANTES
from flowscope.infrastructure.b3.funds_client.constants import (
    _PAGE_SIZE,
    _TIMEOUT_DOCUMENTO,
    _URL_DOCUMENTO_PDF,
    TTL_DOCUMENTOS_RELEVANTES_DIAS,
)

logger = logging.getLogger(__name__)


class FundosDocumentosRelevantesMixin:
    """Mixin com listagem paginada e download de documentos relevantes."""

    def listar_documentos_relevantes(
        self: "FundosDocumentosRelevantesMixin",
        id_fnet: str | None,
        data_inicio: date,
        data_fim: date,
        category: int | str,
    ) -> list[dict]:
        """Lista os documentos relevantes de uma categoria, paginando tudo.

        Retorna lista vazia quando o ticker não foi resolvido (``id_fnet``
        nulo). O resultado bruto é cacheado por 1 dia por categoria e período.
        """
        if not id_fnet:
            return []
        codigo = int(category)
        key = (
            f"fund_docs_relevantes_{id_fnet}_{codigo}_"
            f"{data_inicio.isoformat()}_{data_fim.isoformat()}"
        )

        def _fetch() -> dict[str, object]:
            itens = self._coletar_paginas_relevantes(
                id_fnet, data_inicio, data_fim, codigo
            )
            return {"results": itens}

        payload = self._cache_com_fallback(
            key, TTL_DOCUMENTOS_RELEVANTES_DIAS, _fetch
        )
        resultados = payload.get("results") or []
        documentos = [item for item in resultados if isinstance(item, dict)]
        for documento in documentos:
            documento.setdefault("category", str(codigo))
        return documentos

    def listar_todos_documentos_relevantes(
        self: "FundosDocumentosRelevantesMixin",
        id_fnet: str | None,
        data_inicio: date,
        data_fim: date,
    ) -> list[dict]:
        """Lista as 4 categorias, tolerando falha isolada por categoria."""
        documentos: list[dict] = []
        for codigo in CATEGORIAS_RELEVANTES:
            try:
                documentos.extend(
                    self.listar_documentos_relevantes(
                        id_fnet, data_inicio, data_fim, codigo
                    )
                )
            except requests.RequestException:
                logger.warning(
                    "Falha ao listar documentos relevantes da categoria %s",
                    codigo,
                    exc_info=True,
                )
        return documentos

    def baixar_pdf_documento(
        self: "FundosDocumentosRelevantesMixin", id_documento: str
    ) -> bytes | None:
        """Baixa o PDF do documento, rejeitando conteúdo sem assinatura ``%PDF``."""
        url = f"{_URL_DOCUMENTO_PDF}?id={id_documento}"
        logger.info("Baixando PDF do documento %s via %s", id_documento, url)
        resposta = self._requisicao_get(url, timeout=_TIMEOUT_DOCUMENTO)
        conteudo = resposta.content
        if not conteudo.startswith(b"%PDF"):
            logger.warning("Conteúdo não-PDF no documento %s", id_documento)
            return None
        return conteudo

    def _coletar_paginas_relevantes(
        self: "FundosDocumentosRelevantesMixin",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
        codigo: int,
    ) -> list[dict]:
        """Coleta os itens brutos de todas as páginas do ``GetReportsRelevants``."""
        resultados: list[dict] = []
        page_number = 1
        while True:
            dados = self._get_json(
                "GetReportsRelevants",
                {
                    "language": "pt-br",
                    "dataInicial": data_inicio.isoformat(),
                    "dataFinal": data_fim.isoformat(),
                    "pageNumber": page_number,
                    "pageSize": _PAGE_SIZE,
                    "idFNET": id_fnet,
                    "typeFund": "FII",
                    "category": codigo,
                },
            )
            itens = dados.get("results") if isinstance(dados, dict) else []
            if isinstance(itens, list):
                resultados.extend(item for item in itens if isinstance(item, dict))
            pagina = dados.get("page", {}) if isinstance(dados, dict) else {}
            total_pages = int(pagina.get("totalPages", 1) or 1) if pagina else 1
            if page_number >= total_pages:
                break
            page_number += 1
        return resultados
