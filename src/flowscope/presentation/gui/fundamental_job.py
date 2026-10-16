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
        from flowscope.presentation.composicao import bloqueio_de_escrita

        with bloqueio_de_escrita():
            resultados = caso.execute(
                tickers,
                reference_date,
                progress_callback=_progresso,
                force_refresh=force_refresh,
                cancel_token=ctx.token,
                on_item=lambda ticker: ctx.descrever(f"Fundamentos: {ticker}"),
            )
    except OperacaoCancelada:
        logger.debug("Análise fundamentalista interrompida pelo usuário")
        return
    except Exception as exc:  # falha inesperada do job
        logger.warning("Falha na análise fundamentalista", exc_info=True)
        ctx.falhar(exc)
        return

    dados = {resultado.ticker: resultado for resultado in resultados}
    houve_falha = bool(getattr(caso, "houve_falha_recuperavel", False))
    _registrar_marcador(reference_date)
    ctx.resultado(valor=dados, falhou=houve_falha)


def _registrar_marcador(reference_date: date) -> None:
    """Registra o marcador da última carga de fundamentos, tolerando falhas."""
    try:
        from flowscope.presentation.composicao import registrar_carga_fundamentos

        registrar_carga_fundamentos(reference_date)
    except Exception:  # gravação do marcador não deve derrubar o job
        logger.warning(
            "Falha ao registrar o marcador da última carga de fundamentos",
            exc_info=True,
        )
