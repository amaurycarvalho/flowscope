"""Teste de integração do fluxo de interrupção de processamento."""

import threading

from flowscope.application.cancellation import OperacaoCancelada
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
    view.presenter = presenter
    token = presenter.cancel_token

    presenter.on_operation_started()
    presenter.job_cancelavel_iniciado()
    view.set_progress(0, 10, "Processando")
    assert view.cancellable is True
    assert view.progress_visible is True

    iteracoes: list[int] = []

    def worker() -> None:
        try:
            for i in range(10):
                token.raise_if_cancelled()
                iteracoes.append(i)
                if i == 2:
                    view._on_stop_clicked()
        except OperacaoCancelada:
            return

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=2)

    assert iteracoes == [0, 1, 2]

    presenter.job_cancelavel_finalizado()
    presenter.on_operation_finished()

    assert view.cancellable is False
    assert view.progress_visible is False
    assert view.cursor_busy is False
    assert view.buttons_disabled is False
    assert view.status == ("Processamento interrompido.", "⚠")
    assert presenter._operacoes_ativas == 0
