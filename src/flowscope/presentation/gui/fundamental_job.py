"""Execução em background da análise fundamentalista (design §2).

A thread de trabalho apenas calcula e publica mensagens em uma fila; a thread
do Tk consome a fila e atualiza a interface, respeitando a thread-safety.
"""

import logging
import queue
import threading
from datetime import date

logger = logging.getLogger("flowscope")

MENSAGEM_PROGRESSO = "progresso"
MENSAGEM_RESULTADO = "resultado"
MENSAGEM_ERRO = "erro"


class FundamentalJob:
    """Executa o caso de uso fundamentalista em thread e publica na fila."""

    def __init__(
        self: "FundamentalJob",
        caso: object,
        tickers: list[str],
        reference_date: date,
        generation: int,
        force_refresh: bool = False,
    ) -> None:
        """Inicializa o job com o caso de uso, os tickers e a geração."""
        self._caso = caso
        self._tickers = list(tickers)
        self._reference_date = reference_date
        self.generation = generation
        self._force_refresh = force_refresh
        self.fila: queue.Queue = queue.Queue()
        self.thread: threading.Thread | None = None

    def iniciar(self: "FundamentalJob") -> threading.Thread:
        """Inicia a thread de trabalho e a retorna."""
        thread = threading.Thread(
            target=self._executar, name="flowscope-fundamental", daemon=True
        )
        self.thread = thread
        thread.start()
        return thread

    def _executar(self: "FundamentalJob") -> None:
        """Executa a análise e publica progresso, resultado ou erro."""
        try:
            total = len(self._tickers)
            atual = 0

            def _progresso(detalhe: str, falhou: bool) -> None:
                nonlocal atual
                atual += 1
                self.fila.put(
                    (MENSAGEM_PROGRESSO, detalhe, falhou, atual, total)
                )

            resultados = self._caso.execute(
                self._tickers,
                self._reference_date,
                progress_callback=_progresso,
                force_refresh=self._force_refresh,
            )
            dados = {resultado.ticker: resultado for resultado in resultados}
            houve_falha = bool(
                getattr(self._caso, "houve_falha_recuperavel", False)
            )
            self.fila.put((MENSAGEM_RESULTADO, dados, houve_falha))
        except Exception as exc:  # falha inesperada do job
            logger.warning("Falha na análise fundamentalista", exc_info=True)
            self.fila.put((MENSAGEM_ERRO, str(exc)))
