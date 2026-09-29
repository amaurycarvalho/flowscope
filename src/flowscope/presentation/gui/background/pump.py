"""Pump único de drenagem de eventos na thread do Tk.

Um único agendamento periódico drena as filas de todos os jobs ativos,
despacha os eventos aos callbacks e aplica o watchdog. O pump liga-se quando
há jobs ativos e desliga-se ao esvaziar, sem deixar agendamentos órfãos.
"""

from collections.abc import Callable


class Pump:
    """Agendador periódico único para a drenagem de todos os jobs."""

    def __init__(
        self: "Pump",
        agendar: Callable[[int, Callable[[], None]], object],
        drenar: Callable[[], None],
        tem_jobs: Callable[[], bool],
        *,
        intervalo_ms: int = 50,
    ) -> None:
        """Inicializa o pump com o agendador da thread do Tk."""
        self._agendar = agendar
        self._drenar = drenar
        self._tem_jobs = tem_jobs
        self._intervalo_ms = intervalo_ms
        self._agendado = False
        self._id: object | None = None

    @property
    def agendado(self: "Pump") -> bool:
        """Indica se há um próximo tick agendado."""
        return self._agendado

    def garantir_ativo(self: "Pump") -> None:
        """Garante que o pump esteja agendado, sem duplicar o laço."""
        if self._agendado:
            return
        self._agendado = True
        self._id = self._agendar(self._intervalo_ms, self._tick)

    def parar(self: "Pump") -> None:
        """Impede o próximo reagendamento do pump."""
        self._agendado = False

    def _tick(self: "Pump") -> None:
        """Drena uma vez e reagenda enquanto houver jobs ativos."""
        self._id = None
        self._drenar()
        if self._tem_jobs():
            self._id = self._agendar(self._intervalo_ms, self._tick)
        else:
            self._agendado = False
