"""Execução em background do resumo em lote dos documentos pendentes.

A thread de trabalho prepara o texto (reutilizando o cache) e gera os resumos,
publicando progresso, resultado por documento, erro e término em uma fila; a
thread do Tk consome a fila e aplica os resultados, respeitando a
thread-safety. Qualquer erro por documento interrompe o lote.
"""

import logging
import queue
import threading
from typing import Protocol

from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.infrastructure.document_catalog import DocumentoArquivo
from flowscope.presentation.gui.charts.document_preview import tem_texto

logger = logging.getLogger("flowscope")

#: Tipos das mensagens publicadas na fila.
MENSAGEM_PROGRESSO = "progresso"
MENSAGEM_RESULTADO = "resultado"
MENSAGEM_ERRO = "erro"

#: Rótulos das duas fases do lote.
FASE_PREPARAR = "• Preparando textos"
FASE_RESUMIR = "• Resumindo documentos"


class _PainelDocumentos(Protocol):
    """Fachada do painel de documentos usada pelo job de lote."""

    def preparar_texto(
        self: "_PainelDocumentos", arquivo: DocumentoArquivo
    ) -> str:
        """Retorna o texto do documento, convertendo apenas em *miss*."""
        ...

    def gerar_resumo_estrito(
        self: "_PainelDocumentos", arquivo: DocumentoArquivo, texto: str
    ) -> ResumoDocumento | None:
        """Gera o resumo propagando falhas."""
        ...


class ResumosPendentesJob:
    """Prepara textos e gera resumos em lote, publicando o andamento."""

    def __init__(
        self: "ResumosPendentesJob",
        painel: _PainelDocumentos,
        arquivos: list[DocumentoArquivo],
    ) -> None:
        """Inicializa o job com a fachada do painel e o snapshot de arquivos."""
        self._painel = painel
        self._arquivos = list(arquivos)
        self.fila: queue.Queue = queue.Queue()
        self.thread: threading.Thread | None = None
        self.total = len(self._arquivos)
        self.sem_texto = 0

    def iniciar(self: "ResumosPendentesJob") -> threading.Thread:
        """Inicia a thread de trabalho e a retorna."""
        thread = threading.Thread(
            target=self._executar, name="flowscope-resumos", daemon=True
        )
        self.thread = thread
        thread.start()
        return thread

    def _executar(self: "ResumosPendentesJob") -> None:
        """Executa as duas fases, publicando o término ao final."""
        try:
            preparados = self._preparar_textos()
            if preparados is not None:
                self._resumir(preparados)
        finally:
            self.fila.put(True)

    def _preparar_textos(
        self: "ResumosPendentesJob",
    ) -> list[tuple[DocumentoArquivo, str]] | None:
        """Prepara os textos que faltam e retorna os que têm texto.

        Retorna ``None`` quando um erro interrompe a fase.
        """
        total = len(self._arquivos)
        self._progresso(1, 0, total, FASE_PREPARAR)
        preparados: list[tuple[DocumentoArquivo, str]] = []
        for indice, arquivo in enumerate(self._arquivos, start=1):
            try:
                texto = self._painel.preparar_texto(arquivo)
            except Exception as exc:
                self.fila.put((MENSAGEM_ERRO, arquivo, exc))
                return None
            preparados.append((arquivo, texto))
            self._progresso(1, indice, total, FASE_PREPARAR)
        com_texto = [(a, t) for a, t in preparados if tem_texto(t)]
        self.sem_texto = total - len(com_texto)
        return com_texto

    def _resumir(
        self: "ResumosPendentesJob",
        com_texto: list[tuple[DocumentoArquivo, str]],
    ) -> None:
        """Gera e publica o resumo de cada documento com texto extraível."""
        total = len(com_texto)
        self._progresso(2, 0, total, FASE_RESUMIR)
        for indice, (arquivo, texto) in enumerate(com_texto, start=1):
            try:
                resumo = self._painel.gerar_resumo_estrito(arquivo, texto)
            except Exception as exc:
                self.fila.put((MENSAGEM_ERRO, arquivo, exc))
                return
            self.fila.put((MENSAGEM_RESULTADO, arquivo, resumo))
            self._progresso(2, indice, total, FASE_RESUMIR)

    def _progresso(
        self: "ResumosPendentesJob",
        fase: int,
        current: int,
        total: int,
        label: str,
    ) -> None:
        """Publica uma mensagem de progresso da fase corrente."""
        self.fila.put((MENSAGEM_PROGRESSO, fase, current, total, label))
