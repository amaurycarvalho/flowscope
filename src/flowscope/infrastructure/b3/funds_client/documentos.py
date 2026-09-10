"""Listagem de relatórios estruturados e download do HTML dos documentos."""

import logging
from datetime import date

import requests

from flowscope.infrastructure.b3.funds_client.constants import (
    _PAGE_SIZE,
    _PREFIXO_DOCUMENTO_HTML,
    _TIPO_PROVENTOS,
    TTL_DOCUMENTO_HTML_DIAS,
    TTL_DOCUMENTOS_LISTA_DIAS,
)

logger = logging.getLogger(__name__)


class FundosDocumentosMixin:
    """Mixin com listagem paginada e download de documentos estruturados."""

    def listar_documentos(
        self: "FundosDocumentosMixin",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
        tipo: int = _TIPO_PROVENTOS,
        type_fund: str = "FII",
        tolerante: bool = True,
    ) -> list[dict]:
        """Lista os relatórios estruturados do tipo informado, paginando quando necessário."""
        documentos: list[dict] = []
        page_number = 1
        while True:
            pagina = self._listar_pagina(
                id_fnet,
                data_inicio,
                data_fim,
                tipo,
                type_fund,
                page_number,
                tolerante=tolerante,
            )
            resultados = pagina.get("results", [])
            if isinstance(resultados, list):
                documentos.extend(resultados)
            total_pages = int(pagina.get("page", {}).get("totalPages", 1) or 1)
            if page_number >= total_pages:
                break
            page_number += 1
        return documentos

    def _listar_pagina(
        self: "FundosDocumentosMixin",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
        tipo: int,
        type_fund: str,
        page_number: int,
        tolerante: bool = True,
    ) -> dict[str, object]:
        """Busca uma página da listagem de relatórios, com cache de 1 dia."""
        key = (
            f"fund_docs_{id_fnet}_{tipo}_{data_inicio.isoformat()}_"
            f"{data_fim.isoformat()}_{page_number}"
        )

        def _fetch() -> dict[str, object]:
            return self._get_json(
                "GetStructuredReports",
                {
                    "language": "pt-br",
                    "dataInicial": data_inicio.isoformat(),
                    "dataFinal": data_fim.isoformat(),
                    "pageNumber": page_number,
                    "pageSize": _PAGE_SIZE,
                    "idFNET": id_fnet,
                    "typeFund": type_fund,
                    "type": tipo,
                },
            )

        try:
            return self._cache.get_or_fetch(key, ttl_days=TTL_DOCUMENTOS_LISTA_DIAS, fetch_fn=_fetch)
        except requests.RequestException:
            if not tolerante:
                raise
            logger.warning(
                "Falha ao listar documentos do idFNET %s (página %d)",
                id_fnet,
                page_number,
                exc_info=True,
            )
            return {"results": [], "page": {"totalPages": 1, "totalRecords": 0}}

    def buscar_html_documento(self: "FundosDocumentosMixin", id_documento: str) -> str:
        """Baixa e retorna o HTML do documento de provento informado.

        O HTML é cacheado pelo identificador do documento e compartilhado entre
        proventos (``type=41``) e informe mensal (``type=40``). Em falha de rede,
        o conteúdo armazenado é servido quando existir.
        """
        chave = self._chave_cache(_PREFIXO_DOCUMENTO_HTML, id_documento)

        def _fetch() -> dict[str, object]:
            url = (
                "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento"
                f"?id={id_documento}"
            )
            logger.info("Baixando documento %s via %s", id_documento, url)
            resp = self._requisicao_get(url)
            resp.encoding = resp.apparent_encoding or "utf-8"
            return {"html": resp.text}

        payload = self._cache_com_fallback(
            chave, TTL_DOCUMENTO_HTML_DIAS, _fetch
        )
        return str(payload.get("html") or "")
