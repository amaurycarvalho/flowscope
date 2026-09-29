"""Trabalho em background da aquisição de notícias.

A função de trabalho apenas executa a aquisição e publica progresso e término;
a thread do Tk remonta a árvore pelo gerenciador, respeitando a thread-safety.
"""

import logging
from datetime import date

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.job import Politica

logger = logging.getLogger("flowscope")

#: Grupo de exclusão e política da aquisição de notícias.
GRUPO = "noticias"
POLITICA = Politica.LATEST_WINS


def executar_noticias(
    ctx: JobContext,
    aquisicao: object,
    reference_date: date,
) -> None:
    """Executa a aquisição, publicando progresso e o término."""

    def _progresso(current: int, total: int, label: str) -> None:
        ctx.progress(detalhe=label, atual=current, total=total)

    try:
        aquisicao.adquirir(
            reference_date,
            progress=_progresso,
            cancel_token=ctx.token,
        )
    except OperacaoCancelada:
        logger.debug("Aquisição de notícias interrompida pelo usuário")
    except Exception:  # falha inesperada não deve travar a interface
        logger.warning("Falha na aquisição de notícias", exc_info=True)
