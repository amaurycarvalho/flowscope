"""Contrato de um job gerenciado: identificador, política e callbacks.

O :class:`JobHandle` é o registro interno do gerenciador para um trabalho
submetido. Ele carrega o token de cancelamento próprio, a fila de eventos e a
configuração de política, sem conhecer widgets nem a thread do Tk.
"""

import queue
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from flowscope.application.cancellation import CancellationToken
from flowscope.presentation.gui.background.events import (
    Erro,
    Evento,
    Progresso,
    Resultado,
)

if TYPE_CHECKING:
    from flowscope.presentation.gui.background.context import JobContext


class Politica(Enum):
    """Política de agendamento entre jobs do mesmo grupo."""

    PARALLEL = "parallel"
    LATEST_WINS = "latest_wins"
    SERIALIZE = "serialize"


class EstadoJob(Enum):
    """Estado de ciclo de vida de um job submetido."""

    PENDENTE = "pendente"
    EXECUTANDO = "executando"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"
    DESCARTADO = "descartado"


#: Assinatura do trabalho executado fora da thread do Tk.
Trabalho = Callable[["JobContext"], None]

#: Assinatura de um callback registrado para um evento do job.
Callback = Callable[[Evento], None]


@dataclass
class JobCallbacks:
    """Callbacks por tipo de evento, executados na thread do Tk."""

    progresso: Callback | None = None
    resultado: Callback | None = None
    erro: Callback | None = None
    termino: Callback | None = None

    def para(self: "JobCallbacks", evento: Evento) -> Callback | None:
        """Retorna o callback correspondente ao evento, se houver."""
        if isinstance(evento, Progresso):
            return self.progresso
        if isinstance(evento, Resultado):
            return self.resultado
        if isinstance(evento, Erro):
            return self.erro
        return None


@dataclass
class JobHandle:
    """Registro de um job ativo no gerenciador."""

    id: int
    grupo: str
    politica: Politica
    chave: object = None
    cancelavel: bool = False
    estado: EstadoJob = EstadoJob.PENDENTE
    token: CancellationToken = field(default_factory=CancellationToken)
    callbacks: JobCallbacks = field(default_factory=JobCallbacks)
    trabalho: Trabalho | None = None
    thread: threading.Thread | None = None
    fila: "queue.Queue[Evento]" = field(default_factory=queue.Queue)
    ultima_atividade: float = 0.0
