"""Gerenciador único de processamentos assíncronos da interface.

Concentra submissão, políticas de agendamento, token de cancelamento por job e
a drenagem única de eventos na thread do Tk, eliminando a coreografia
duplicada de thread/fila/watchdog dos jobs da camada de apresentação.
"""

from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import (
    Erro,
    Evento,
    Progresso,
    Resultado,
    Termino,
)
from flowscope.presentation.gui.background.job import (
    EstadoJob,
    JobCallbacks,
    JobHandle,
    Politica,
)
from flowscope.presentation.gui.background.manager import BackgroundManager

__all__ = [
    "BackgroundManager",
    "Erro",
    "EstadoJob",
    "Evento",
    "JobCallbacks",
    "JobContext",
    "JobHandle",
    "Politica",
    "Progresso",
    "Resultado",
    "Termino",
]
