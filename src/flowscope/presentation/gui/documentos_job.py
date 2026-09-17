"""Execução em background da aquisição de documentos (design §4).

A thread de trabalho apenas executa a aquisição e publica o término em uma
fila; a thread do Tk consome a fila e remonta a árvore, respeitando a
thread-safety.
"""

import logging
import queue
import threading
from datetime import date

logger = logging.getLogger("flowscope")

#: Tipo da mensagem de progresso publicada na fila.
MENSAGEM_PROGRESSO = "progresso"


class DocumentosJob:
    """Executa a aquisição de documentos em thread e publica o término."""

    def __init__(
        self: "DocumentosJob",
        aquisicao: object,
        ticker: str,
        reference_date: date,
    ) -> None:
        """Inicializa o job com o orquestrador, o ticker e a data de referência."""
        self._aquisicao = aquisicao
        self._ticker = ticker
        self._reference_date = reference_date
        self.fila: queue.Queue = queue.Queue()
        self.thread: threading.Thread | None = None

    def iniciar(self: "DocumentosJob") -> threading.Thread:
        """Inicia a thread de trabalho e a retorna."""
        thread = threading.Thread(
            target=self._executar, name="flowscope-documentos", daemon=True
        )
        self.thread = thread
        thread.start()
        return thread

    def _executar(self: "DocumentosJob") -> None:
        """Executa a aquisição, publicando progresso e o término."""

        def _progresso(current: int, total: int, label: str) -> None:
            self.fila.put((MENSAGEM_PROGRESSO, current, total, label))

        try:
            self._aquisicao.adquirir(
                self._ticker, self._reference_date, progress=_progresso
            )
        except Exception:  # falha inesperada não deve travar a interface
            logger.warning(
                "Falha na aquisição de documentos de %s",
                self._ticker,
                exc_info=True,
            )
        finally:
            self.fila.put(True)
