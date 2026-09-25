"""Execução em background da aquisição de notícias.

A thread de trabalho apenas executa a aquisição e publica progresso e término
em uma fila; a thread do Tk consome a fila e remonta a árvore, respeitando a
thread-safety.
"""

import logging
import queue
import threading
from datetime import date

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)

logger = logging.getLogger("flowscope")

#: Tipo da mensagem de progresso publicada na fila.
MENSAGEM_PROGRESSO = "progresso"


class NoticiasJob:
    """Executa a aquisição de notícias em thread e publica o término."""

    def __init__(
        self: "NoticiasJob",
        aquisicao: object,
        reference_date: date,
        cancel_token: CancellationToken | None = None,
    ) -> None:
        """Inicializa o job com o orquestrador e a data de referência."""
        self._aquisicao = aquisicao
        self._reference_date = reference_date
        self._cancel_token = cancel_token
        self.fila: queue.Queue = queue.Queue()
        self.thread: threading.Thread | None = None

    def iniciar(self: "NoticiasJob") -> threading.Thread:
        """Inicia a thread de trabalho e a retorna."""
        thread = threading.Thread(
            target=self._executar, name="flowscope-noticias", daemon=True
        )
        self.thread = thread
        thread.start()
        return thread

    def _executar(self: "NoticiasJob") -> None:
        """Executa a aquisição, publicando progresso e o término."""

        def _progresso(current: int, total: int, label: str) -> None:
            self.fila.put((MENSAGEM_PROGRESSO, current, total, label))

        try:
            self._aquisicao.adquirir(
                self._reference_date,
                progress=_progresso,
                cancel_token=self._cancel_token,
            )
        except OperacaoCancelada:
            logger.debug("Aquisição de notícias interrompida pelo usuário")
        except Exception:  # falha inesperada não deve travar a interface
            logger.warning("Falha na aquisição de notícias", exc_info=True)
        finally:
            self.fila.put(True)
