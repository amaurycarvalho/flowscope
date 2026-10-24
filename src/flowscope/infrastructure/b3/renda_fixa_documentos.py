"""Listagem de avisos aos debenturistas como links de documentos relacionados."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, timedelta

from flowscope.domain.renda_fixa import DocumentoRelacionado
from flowscope.domain.structured import CategoriaMaterialFact

logger = logging.getLogger("flowscope")

#: Janela de consulta dos avisos aos debenturistas.
_JANELA = timedelta(days=730)


def criar_listador_documentos(
    client: object,
) -> Callable[[str, date, str], list[DocumentoRelacionado]]:
    """Cria o listador de avisos aos debenturistas a partir do cliente B3."""

    def listar(
        ticker: str, reference_date: date, _cnpj: str = ""
    ) -> list[DocumentoRelacionado]:
        """Lista os links da categoria 48 sem baixar PDF."""
        return listar_avisos_debenturistas(client, ticker, reference_date)

    return listar


def listar_avisos_debenturistas(
    client: object, ticker: str, reference_date: date
) -> list[DocumentoRelacionado]:
    """Lista os avisos aos debenturistas do ticker como documentos relacionados."""
    resolver = getattr(client, "resolver_code_cvm", None)
    listar = getattr(client, "listar_fatos_relevantes", None)
    if not callable(resolver) or not callable(listar):
        return []
    code_cvm = resolver(ticker)
    if not code_cvm:
        return []
    try:
        documentos = listar(
            code_cvm,
            CategoriaMaterialFact.AVISO_DEBENTURISTAS,
            reference_date - _JANELA,
            reference_date,
            ticker=ticker,
        )
    except Exception:  # listagem de links não bloqueia a aquisição
        logger.warning(
            "Falha ao listar avisos aos debenturistas de %s",
            ticker,
            exc_info=True,
        )
        return []
    return [
        item
        for documento in documentos
        if (item := _documento_relacionado(documento)) is not None
    ]


def _documento_relacionado(documento: object) -> DocumentoRelacionado | None:
    """Monta o link de um material fact, omitindo os que não têm URL."""
    url = getattr(documento, "url_documento", None) or getattr(
        documento, "url_download", None
    )
    if not url:
        return None
    return DocumentoRelacionado(
        descricao=getattr(documento, "assunto", "") or "Aviso aos Debenturistas",
        url=url,
        fonte="B3",
        data=getattr(documento, "data_referencia", ""),
    )
