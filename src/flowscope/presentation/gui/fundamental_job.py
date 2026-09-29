"""Trabalho em background da análise fundamentalista.

A função de trabalho apenas calcula e publica progresso, resultado ou erro no
:class:`JobContext`; a thread do Tk consome os eventos pelo gerenciador,
respeitando a thread-safety.
"""

import logging
from datetime import date

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.job import Politica

logger = logging.getLogger("flowscope")

#: Grupo de exclusão e política do trabalho fundamentalista.
GRUPO = "fundamental"
POLITICA = Politica.LATEST_WINS


def executar_fundamental(
    ctx: JobContext,
    caso: object,
    tickers: list[str],
    reference_date: date,
    force_refresh: bool = False,
) -> None:
    """Executa a análise e publica progresso, resultado ou erro."""
    total = len(tickers)
    atual = 0

    def _progresso(detalhe: str, falhou: bool) -> None:
        nonlocal atual
        atual += 1
        ctx.progress(detalhe=detalhe, atual=atual, total=total)

    try:
        resultados = caso.execute(
            tickers,
            reference_date,
            progress_callback=_progresso,
            force_refresh=force_refresh,
            cancel_token=ctx.token,
        )
    except OperacaoCancelada:
        logger.debug("Análise fundamentalista interrompida pelo usuário")
        return
    except Exception as exc:  # falha inesperada do job
        logger.warning("Falha na análise fundamentalista", exc_info=True)
        ctx.erro(exc)
        return

    dados = {resultado.ticker: resultado for resultado in resultados}
    houve_falha = bool(getattr(caso, "houve_falha_recuperavel", False))
    ctx.resultado(valor=dados, falhou=houve_falha)
