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

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)
from flowscope.application.documentos.lote import (
    PainelLote,
    gerar_resumo_do_lote,
)
from flowscope.domain.documents import DocumentoArquivo
from flowscope.presentation.gui.charts.document_preview import tem_texto

logger = logging.getLogger("flowscope")

#: Tipos das mensagens publicadas na fila.
MENSAGEM_PROGRESSO = "progresso"
MENSAGEM_RESULTADO = "resultado"
MENSAGEM_ERRO = "erro"

#: Rótulos das duas fases do lote.
FASE_PREPARAR = "• Preparando textos"
FASE_RESUMIR = "• Resumindo documentos"


class _PainelDocumentos(PainelLote, Protocol):
    """Fachada do painel de documentos usada pelo job de lote.

    Além do seam de persistência (``persistir_no_lote``/``gerar_e_persistir``/
    ``gerar_resumo_estrito``), expõe a preparação de texto e a avaliação de
    guidance.
    """

    def preparar_texto(
        self: "_PainelDocumentos", arquivo: DocumentoArquivo
    ) -> str:
        """Retorna o texto do documento, convertendo apenas em *miss*."""
        ...

    def avaliar_guidance(
        self: "_PainelDocumentos", arquivo: DocumentoArquivo, texto: str
    ) -> None:
        """Avalia o guidance do documento, tolerando falhas."""
        ...


class ResumosPendentesJob:
    """Prepara textos e gera resumos em lote, publicando o andamento."""

    def __init__(
        self: "ResumosPendentesJob",
        painel: _PainelDocumentos,
        arquivos: list[DocumentoArquivo],
        cancel_token: CancellationToken | None = None,
        continuar_em_erro: bool = False,
    ) -> None:
        """Inicializa o job com a fachada do painel e o snapshot de arquivos.

        Quando ``continuar_em_erro`` é verdadeiro, uma falha por item é
        publicada e o lote prossegue com os demais; caso contrário, o lote é
        interrompido no primeiro erro.
        """
        self._painel = painel
        self._arquivos = list(arquivos)
        self._cancel_token = cancel_token
        self._continuar_em_erro = continuar_em_erro
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
        except OperacaoCancelada:
            logger.debug("Resumo em lote interrompido pelo usuário")
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
            if self._cancel_token is not None:
                self._cancel_token.raise_if_cancelled()
            try:
                texto = self._painel.preparar_texto(arquivo)
            except Exception as exc:
                self.fila.put((MENSAGEM_ERRO, arquivo, exc))
                if not self._continuar_em_erro:
                    return None
                continue
            if self._texto_utilizavel(arquivo, texto):
                self._avaliar_guidance(arquivo, texto)
            preparados.append((arquivo, texto))
            self._progresso(1, indice, total, FASE_PREPARAR)
        com_texto = [
            (a, t) for a, t in preparados if self._texto_utilizavel(a, t)
        ]
        self.sem_texto = total - len(com_texto)
        return com_texto

    def _texto_utilizavel(
        self: "ResumosPendentesJob", arquivo: DocumentoArquivo, texto: str
    ) -> bool:
        """Indica se o texto preparado serve para resumir.

        Painéis que distinguem texto resolvido de conteúdo sem valor (por
        exemplo, notícias "Geral" cujo documento vinculado não foi baixado)
        expõem ``texto_utilizavel``; na ausência do método, vale o texto
        extraível genérico.
        """
        metodo = getattr(self._painel, "texto_utilizavel", None)
        if metodo is not None:
            return bool(metodo(arquivo, texto))
        return tem_texto(texto)

    def _avaliar_guidance(
        self: "ResumosPendentesJob", arquivo: DocumentoArquivo, texto: str
    ) -> None:
        """Avalia o guidance sem interromper o lote em caso de falha."""
        try:
            self._painel.avaliar_guidance(arquivo, texto)
        except Exception:  # falha isolada não deve abortar o lote
            logger.warning(
                "Falha ao avaliar guidance de %s", arquivo.caminho, exc_info=True
            )

    def _resumir(
        self: "ResumosPendentesJob",
        com_texto: list[tuple[DocumentoArquivo, str]],
    ) -> None:
        """Gera e publica o resumo de cada documento com texto extraível."""
        total = len(com_texto)
        self._progresso(2, 0, total, FASE_RESUMIR)
        for indice, (arquivo, texto) in enumerate(com_texto, start=1):
            if self._cancel_token is not None:
                self._cancel_token.raise_if_cancelled()
            try:
                resumo = gerar_resumo_do_lote(self._painel, arquivo, texto)
            except Exception as exc:
                self.fila.put((MENSAGEM_ERRO, arquivo, exc))
                if not self._continuar_em_erro:
                    return
                continue
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
