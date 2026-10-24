"""Resolução das dependências injetadas no painel de documentos."""

from __future__ import annotations

from collections.abc import Callable

from flowscope.application.document_text_port import DocumentTextStore
from flowscope.application.documentos.catalogo import (
    CatalogoDocumentos,
    ConsultarCatalogoUseCase,
)
from flowscope.application.documentos.document_summary import DocumentSummaryService
from flowscope.application.documentos.document_summary_port import (
    DocumentSummaryStore,
)
from flowscope.domain.llm import LLMPort


def resolver_use_case(
    catalogo_use_case: ConsultarCatalogoUseCase | None,
    catalog: CatalogoDocumentos | None,
) -> ConsultarCatalogoUseCase:
    """Resolve o caso de uso do catálogo, construindo-o do repositório."""
    if catalogo_use_case is not None:
        return catalogo_use_case
    if catalog is None:
        raise ValueError(
            "DocumentTreePanel exige 'catalogo_use_case' ou 'catalog'."
        )
    return ConsultarCatalogoUseCase(catalog)


def resolver_summary(
    summary_service: DocumentSummaryService | None,
    summary_store: DocumentSummaryStore | None,
    catalog: CatalogoDocumentos | None,
    llm_factory: Callable[[], LLMPort] | None,
    llm_available: Callable[[], bool] | None,
) -> DocumentSummaryService:
    """Resolve o serviço de resumo, injetado ou montado do repositório."""
    if summary_service is not None:
        return summary_service
    store = summary_store
    base = None
    if catalog is not None:
        store = store or catalog.summary_store
        base = catalog.base_dir
    if store is None or base is None:
        raise ValueError(
            "DocumentTreePanel exige 'summary_service' ou "
            "'summary_store' com a raiz de cache."
        )
    return DocumentSummaryService(store, base, llm_factory, llm_available)


def resolver_text_store(
    text_store: DocumentTextStore | None,
    catalog: CatalogoDocumentos | None,
) -> DocumentTextStore:
    """Resolve o store de texto, injetado ou obtido do repositório."""
    if text_store is not None:
        return text_store
    if catalog is None:
        raise ValueError("DocumentTreePanel exige 'text_store' ou 'catalog'.")
    return catalog.text_store
