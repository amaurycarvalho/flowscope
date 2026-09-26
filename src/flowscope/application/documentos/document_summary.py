"""Disponibilidade, geração e persistência de resumos de documentos.

Concentra a decisão de "LLM disponível", a chamada ao serviço de resumo e a
gravação no store. As estratégias de LLM são injetadas pelo ponto de composição:
a aplicação não conhece a configuração nem a fábrica de provedores.
"""

import logging
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from flowscope.application.documentos.catalogo import chave_documento
from flowscope.application.documentos.document_summary_port import (
    DocumentSummaryStore,
)
from flowscope.application.documentos.mensagens import mensagem_indisponivel
from flowscope.application.resumo_documento import (
    ResumirDocumentoUseCase,
    ResumoDocumento,
)
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.documents.texto import tem_texto
from flowscope.domain.llm import LLMError, LLMPort

logger = logging.getLogger("flowscope")


class DocumentSummaryService:
    """Resolve disponibilidade, geração e persistência de resumos."""

    def __init__(
        self: "DocumentSummaryService",
        summary_store: DocumentSummaryStore,
        base_dir: Path,
        llm_factory: Callable[[], LLMPort] | None = None,
        llm_available: Callable[[], bool] | None = None,
    ) -> None:
        """Guarda o store, a raiz de cache e as estratégias de LLM."""
        self._store = summary_store
        self._base_dir = base_dir
        self._llm_factory = llm_factory
        self._llm_available = llm_available

    def disponivel(self: "DocumentSummaryService") -> bool:
        """Indica se a geração de resumos está habilitada."""
        if self._llm_available is not None:
            return self._llm_available()
        return self._llm_factory is not None

    def mensagem_indisponivel(self: "DocumentSummaryService") -> str:
        """Retorna a mensagem de indisponibilidade conforme a LLM configurada."""
        return mensagem_indisponivel(self.disponivel())

    def precisa_resumo(
        self: "DocumentSummaryService",
        arquivo: DocumentoArquivo,
        texto: str | None,
    ) -> bool:
        """Indica se o documento ainda precisa de geração de resumo."""
        return (
            arquivo.long_summary is None
            and self.disponivel()
            and tem_texto(texto)
        )

    def resumo_para_exibir(
        self: "DocumentSummaryService",
        arquivo: DocumentoArquivo,
        texto: str,
    ) -> str | None:
        """Resolve o resumo a exibir quando não há geração pendente."""
        if arquivo.long_summary is not None:
            return arquivo.long_summary
        if tem_texto(texto):
            return self.mensagem_indisponivel()
        return None

    def gerar(
        self: "DocumentSummaryService",
        arquivo: DocumentoArquivo,
        texto: str,
    ) -> ResumoDocumento | None:
        """Gera o resumo do documento, tolerando falhas da LLM."""
        if not self.precisa_resumo(arquivo, texto):
            return None
        try:
            return ResumirDocumentoUseCase(self._criar_llm()).resumir(texto)
        except LLMError as exc:
            logger.warning(
                "Falha ao resumir documento %s: %s", arquivo.caminho, exc
            )
            return None
        except Exception as exc:  # falha inesperada não deve derrubar a thread
            logger.warning(
                "Erro inesperado ao resumir %s: %s", arquivo.caminho, exc
            )
            return None

    def gerar_estrito(
        self: "DocumentSummaryService",
        arquivo: DocumentoArquivo,
        texto: str,
    ) -> ResumoDocumento | None:
        """Gera o resumo propagando falhas da LLM (contrato do lote).

        Diferente de :meth:`gerar`, não suprime erros: o chamador precisa ser
        notificado para interromper o processamento em lote.
        """
        if not self.precisa_resumo(arquivo, texto):
            return None
        return ResumirDocumentoUseCase(self._criar_llm()).resumir(texto)

    def atualizar(
        self: "DocumentSummaryService",
        arquivo: DocumentoArquivo,
        resumo: ResumoDocumento,
    ) -> DocumentoArquivo:
        """Devolve a entrada atualizada com o resumo, sem gravar no store."""
        return replace(
            arquivo,
            short_summary=resumo.short_summary,
            long_summary=resumo.long_summary,
        )

    def persistir(
        self: "DocumentSummaryService",
        arquivo: DocumentoArquivo,
        resumo: ResumoDocumento,
    ) -> DocumentoArquivo:
        """Grava o resumo no store e devolve a entrada atualizada."""
        self._store.salvar(
            arquivo.ticker,
            self.chave(arquivo),
            resumo.short_summary,
            resumo.long_summary,
        )
        return self.atualizar(arquivo, resumo)

    def gerar_e_persistir(
        self: "DocumentSummaryService",
        arquivo: DocumentoArquivo,
        texto: str,
    ) -> ResumoDocumento | None:
        """Gera o resumo e o grava no store, sem tocar em widgets.

        É seguro chamar da thread de trabalho do lote: apenas o store é
        acessado, preservando a gravação imediata após cada item.
        """
        resumo = self.gerar_estrito(arquivo, texto)
        if resumo is not None:
            self.persistir(arquivo, resumo)
        return resumo

    def chave(self: "DocumentSummaryService", arquivo: DocumentoArquivo) -> str:
        """Deriva a chave do documento relativa à raiz de cache."""
        try:
            return chave_documento(arquivo.caminho, self._base_dir)
        except (TypeError, ValueError):
            return arquivo.nome

    def _criar_llm(self: "DocumentSummaryService") -> LLMPort:
        """Cria a porta de completion a partir da fábrica injetada."""
        if self._llm_factory is None:
            raise LLMError("Fábrica de LLM não configurada.")
        return self._llm_factory()
