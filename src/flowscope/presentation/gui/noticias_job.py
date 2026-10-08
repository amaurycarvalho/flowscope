"""Trabalho em background da aquisição de notícias.

A função de trabalho executa a aquisição e, em seguida, o housekeeping de
deduplicação por conteúdo, publicando progresso e término; a thread do Tk
remonta a árvore pelo gerenciador, respeitando a thread-safety.
"""

import logging
from collections.abc import Callable
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
    deduplicar: Callable[[object], None] | None = None,
) -> int:
    """Executa a aquisição e o housekeeping, publicando progresso e término.

    Retorna a contagem de itens adquiridos (zero em cancelamento ou falha).
    """

    def _progresso(current: int, total: int, label: str) -> None:
        ctx.progress(detalhe=label, atual=current, total=total)

    adquiridos = 0
    try:
        adquiridos = aquisicao.adquirir(
            reference_date,
            progress=_progresso,
            cancel_token=ctx.token,
        ) or 0
    except OperacaoCancelada:
        logger.debug("Aquisição de notícias interrompida pelo usuário")
    except Exception:  # falha inesperada não deve travar a interface
        logger.warning("Falha na aquisição de notícias", exc_info=True)
    if deduplicar is None:
        return adquiridos
    try:
        deduplicar(ctx.token)
    except OperacaoCancelada:
        logger.debug("Housekeeping de notícias interrompido pelo usuário")
    except Exception:  # housekeeping não deve travar a interface
        logger.warning("Falha no housekeeping de notícias", exc_info=True)
    return adquiridos
