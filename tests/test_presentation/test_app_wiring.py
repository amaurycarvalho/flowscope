"""Testes da ligação do término de jobs ao apresentador."""

from unittest.mock import MagicMock

from flowscope.presentation.gui.app_wiring import WiringMixin
from flowscope.presentation.gui.background.events import Outcome
from flowscope.presentation.gui.background.job import JobHandle, Politica


class _WireHost(WiringMixin):
    def __init__(self, presenter) -> None:
        self._presenter = presenter


def _handle(*, cancelavel: bool, outcome: Outcome, reportada: bool) -> JobHandle:
    handle = JobHandle(
        id=1, grupo="g", politica=Politica.PARALLEL, cancelavel=cancelavel
    )
    handle.outcome = outcome
    handle.falha_reportada = reportada
    return handle


class TestTerminoBackground:
    def test_entrega_desfecho_e_falha_reportada(self):
        presenter = MagicMock()
        host = _WireHost(presenter)
        handle = _handle(
            cancelavel=True, outcome=Outcome.FALHA, reportada=True
        )

        host._on_background_terminado(handle)

        presenter.job_cancelavel_finalizado.assert_called_once()
        presenter.exit.assert_called_once_with(Outcome.FALHA, True)

    def test_job_nao_cancelavel_nao_mexe_no_botao(self):
        presenter = MagicMock()
        host = _WireHost(presenter)
        handle = _handle(
            cancelavel=False, outcome=Outcome.SUCESSO, reportada=False
        )

        host._on_background_terminado(handle)

        presenter.job_cancelavel_finalizado.assert_not_called()
        presenter.exit.assert_called_once_with(Outcome.SUCESSO, False)
