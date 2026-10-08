"""Teste de integração do fluxo de interrupção de processamento."""

import threading

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.presentation.gui.background.events import Outcome
from flowscope.presentation.gui.background.manager import BackgroundManager
from flowscope.presentation.gui.presenter import FlowScopePresenter


class _ViewFake:
    """View mínima que registra o estado observável da barra de status."""

    def __init__(self) -> None:
        self.presenter: FlowScopePresenter | None = None
        self.cancellable = False
        self.progress_visible = False
        self.status: tuple[str, str] | None = None
        self.cursor_busy = False
        self.buttons_disabled = False

    def _on_stop_clicked(self) -> None:
        self.presenter.request_cancel()

    def set_cancellable(self, value: bool) -> None:
        self.cancellable = value

    def set_progress(self, current: int, total: int, label: str) -> None:
        self.progress_visible = True

    def clear_progress(self) -> None:
        self.progress_visible = False

    def disable_all_buttons(self) -> None:
        self.buttons_disabled = True

    def restore_all_buttons(self) -> None:
        self.buttons_disabled = False

    def enter_busy(self) -> None:
        self.cursor_busy = True

    def exit_busy(self) -> None:
        self.cursor_busy = False

    def set_status(self, msg: str, icon: str = "") -> None:
        self.status = (msg, icon)

    def config_copy_button_state(self, state: str) -> None:
        pass


def test_clique_interrompe_worker_e_finaliza_interface():
    view = _ViewFake()
    presenter = FlowScopePresenter(view)
    background = BackgroundManager()
    presenter.attach_background(background)
    background.ao_iniciar(lambda handle: presenter.on_operation_started())
    background.ao_terminar(
        lambda handle: presenter.exit(handle.outcome, handle.falha_reportada)
    )
    view.presenter = presenter

    iniciado = threading.Event()
    iteracoes: list[int] = []

    def trabalho(ctx):
        iniciado.set()
        try:
            for i in range(10):
                ctx.raise_if_cancelled()
                iteracoes.append(i)
        except OperacaoCancelada:
            return

    handle = background.submit(trabalho, grupo="g", cancelavel=True)
    assert iniciado.wait(2)

    presenter.job_cancelavel_iniciado()
    view.set_progress(0, 10, "Processando")
    assert view.cancellable is True
    assert view.progress_visible is True

    view._on_stop_clicked()

    handle.thread.join(timeout=2)
    assert handle.outcome is Outcome.CANCELADO

    presenter.job_cancelavel_finalizado()

    assert view.cancellable is False
    assert view.progress_visible is False
    assert view.cursor_busy is False
    assert view.buttons_disabled is False
    assert view.status == ("Processamento interrompido.", "⚠")
    assert presenter._operacoes_ativas == 0
