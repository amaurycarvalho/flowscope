import threading
from datetime import date
from unittest.mock import MagicMock, patch

from flowscope.presentation.gui import controller_fundamental
from flowscope.presentation.gui.background.manager import BackgroundManager
from flowscope.presentation.gui.controller import FlowScopeController
from flowscope.presentation.gui.presenter import FlowScopePresenter


def _make_controller(**overrides):
    defaults = {
        "guard": MagicMock(),
        "load_portfolio": MagicMock(),
        "analyze": MagicMock(),
        "presenter": MagicMock(),
        "logger": MagicMock(),
    }
    defaults.update(overrides)
    return FlowScopeController(**defaults)


def _mock_context(return_value: bool = True) -> MagicMock:
    ctx = MagicMock()
    ctx.__enter__.return_value = return_value
    return ctx


class TestMakeProgressCb:
    def test_chama_advance_quando_failed_false(self):
        controller = _make_controller()
        reporter = MagicMock()
        cb = controller._make_progress_cb(reporter)
        cb("detalhe", False)
        reporter.advance.assert_called_once_with(1, "detalhe")

    def test_chama_fail_quando_failed_true(self):
        controller = _make_controller()
        reporter = MagicMock()
        cb = controller._make_progress_cb(reporter)
        cb("detalhe", True)
        reporter.fail.assert_called_once_with(1, "detalhe")


class TestOnToday:
    def test_on_today_nao_leva_attribute_error(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        guard = MagicMock()
        guard.acquire.return_value = _mock_context(False)

        controller = _make_controller(presenter=presenter, guard=guard)
        controller.on_today()

        view._date_entry.set_date.assert_called_once()


class _RepoVazio:
    def obter_nome(self, ticker):
        return None

    def obter_proventos(self, ticker, reference_date):
        return []

    def obter_patrimonio(self, ticker, reference_date):
        return None


class TestFundamentalProgress:
    def test_inicia_barra_em_zero(self):
        presenter = MagicMock()
        controller = _make_controller(
            presenter=presenter, fundamental_repo=_RepoVazio(),
        )

        controller._iniciar_analise_fundamental(
            ["PETR4", "VALE3"], date(2024, 1, 15), {},
        )

        presenter.on_progress.assert_any_call(0, 2, "• Fundamentos...")


class TestOnTickerEdit:
    def test_on_ticker_edit_com_tickers_aplica_filtro(self):
        view = MagicMock()
        view._resolve_current_chart.return_value = None
        presenter = FlowScopePresenter(view)
        presenter.get_current_tickers = MagicMock(return_value=["PETR4"])

        controller = _make_controller(presenter=presenter)
        controller.on_ticker_edit()

        view.enter_busy.assert_called_once()
        view.exit_busy.assert_called_once()
        view.disable_all_buttons.assert_called_once()
        view.restore_all_buttons.assert_called_once()
        view._flash_status.assert_called_once()


class TestAtualizarFundamentos:
    def test_forca_recomputacao(self):
        presenter = MagicMock()
        presenter.get_current_tickers.return_value = ["HGBS11"]
        presenter.get_reference_date.return_value = date(2026, 9, 4)
        presenter._gui._current_data = {"HGBS11": {"daily_data": []}}
        controller = _make_controller(
            presenter=presenter, fundamental_repo=object()
        )

        with patch.object(controller, "_iniciar_analise_fundamental") as iniciar:
            controller.on_atualizar_fundamentos()

        iniciar.assert_called_once()
        assert iniciar.call_args.kwargs["force"] is True

    def test_sem_tickers_nao_dispara(self):
        presenter = MagicMock()
        presenter.get_current_tickers.return_value = []
        controller = _make_controller(
            presenter=presenter, fundamental_repo=object()
        )

        with patch.object(controller, "_iniciar_analise_fundamental") as iniciar:
            controller.on_atualizar_fundamentos()

        iniciar.assert_not_called()

    def test_sem_repo_nao_dispara(self):
        presenter = MagicMock()
        controller = _make_controller(presenter=presenter, fundamental_repo=None)

        with patch.object(controller, "_iniciar_analise_fundamental") as iniciar:
            controller.on_atualizar_fundamentos()

        iniciar.assert_not_called()

    def test_nao_dispara_com_job_ativo(self):
        presenter = MagicMock()
        presenter.get_current_tickers.return_value = ["HGBS11"]
        presenter.get_reference_date.return_value = date(2026, 9, 4)
        background = MagicMock()
        background.tem_ativo.return_value = True
        controller = _make_controller(
            presenter=presenter,
            fundamental_repo=object(),
            background=background,
        )

        with patch.object(controller, "_iniciar_analise_fundamental") as iniciar:
            controller.on_atualizar_fundamentos()

        iniciar.assert_not_called()


class TestSubstituicaoJobFundamental:
    def _controller(self):
        view = MagicMock()
        view.get_current_tickers.return_value = ["PETR4"]
        view.get_reference_date.return_value = date(2026, 9, 4)
        view.get_sampling_config.return_value = MagicMock()
        presenter = FlowScopePresenter(view)
        guard = MagicMock()
        guard.acquire.return_value = _mock_context(True)
        analyze = MagicMock()
        analyze.execute.return_value = {"PETR4": {"daily_data": []}}
        background = BackgroundManager()
        background.ao_iniciar(lambda handle: presenter.enter())
        background.ao_terminar(lambda handle: presenter.exit())
        controller = _make_controller(
            guard=guard,
            load_portfolio=MagicMock(),
            analyze=analyze,
            presenter=presenter,
            fundamental_repo=object(),
            background=background,
        )
        return controller, presenter, view, background

    def test_job_substituido_balanceia_contador_e_libera_cursor(self):
        controller, presenter, view, background = self._controller()
        bloqueio = threading.Event()
        with patch.object(
            controller_fundamental,
            "executar_fundamental",
            lambda *args, **kwargs: bloqueio.wait(2),
        ), patch.object(
            controller_fundamental, "FundamentalAnalysisUseCase"
        ):
            controller._iniciar_analise_fundamental(
                ["PETR4"], date(2026, 9, 4), {}
            )
            handle1 = background.jobs_ativos[0]
            controller._iniciar_analise_fundamental(
                ["PETR4"], date(2026, 9, 4), {}
            )
            assert presenter._operacoes_ativas == 1
            assert len(background.jobs_ativos) == 1

            bloqueio.set()
            handle1.thread.join(2)
            handle2 = background.jobs_ativos[0]
            handle2.thread.join(2)
            background.drenar()

        assert presenter._operacoes_ativas == 0
        view.exit_busy.assert_called()

    def test_falha_balanceia_contador_e_libera_cursor(self):
        controller, presenter, view, background = self._controller()

        def _falha(ctx, *args, **kwargs):
            ctx.erro(RuntimeError("boom"))

        with patch.object(
            controller_fundamental, "executar_fundamental", _falha
        ), patch.object(controller_fundamental, "FundamentalAnalysisUseCase"):
            controller._iniciar_analise_fundamental(
                ["PETR4"], date(2026, 9, 4), {}
            )
            handle = background.jobs_ativos[0]
            handle.thread.join(2)
            background.drenar()

        assert presenter._operacoes_ativas == 0
        view.exit_busy.assert_called()

    def test_carga_sobreposta_ao_fundamental_balanceia(self):
        controller, presenter, view, background = self._controller()
        bloqueio = threading.Event()
        with patch.object(
            controller_fundamental,
            "executar_fundamental",
            lambda *args, **kwargs: bloqueio.wait(2),
        ), patch.object(
            controller_fundamental, "FundamentalAnalysisUseCase"
        ):
            controller._iniciar_analise_fundamental(
                ["PETR4"], date(2026, 9, 4), {}
            )
            controller.on_load_data()
            assert presenter._operacoes_ativas == 2

            for handle in background.jobs_ativos:
                handle.token.request()
            bloqueio.set()
            for _ in range(5):
                handles = list(background.jobs_ativos)
                if not handles:
                    break
                for handle in handles:
                    if handle.thread is not None:
                        handle.thread.join(2)
                background.drenar()

        assert presenter._operacoes_ativas == 0
        view.exit_busy.assert_called()


class TestWiringHistorico:
    def test_store_injetado_no_caso_de_uso(self):
        presenter = MagicMock()
        controller = _make_controller(
            presenter=presenter,
            fundamental_repo=object(),
            fundamental_history_store="STORE",
        )

        with patch(
            "flowscope.presentation.gui.controller_fundamental"
            ".FundamentalAnalysisUseCase"
        ) as caso:
            controller._iniciar_analise_fundamental(
                ["HGBS11"], date(2026, 9, 4), {}
            )

        assert caso.call_args.kwargs["historico_store"] == "STORE"


class TestWiringGuidance:
    def test_store_de_guidance_injetado_no_caso_de_uso(self):
        presenter = MagicMock()
        controller = _make_controller(
            presenter=presenter,
            fundamental_repo=object(),
            fundamental_guidance_store="GUIDANCE_STORE",
        )

        with patch(
            "flowscope.presentation.gui.controller_fundamental"
            ".FundamentalAnalysisUseCase"
        ) as caso:
            controller._iniciar_analise_fundamental(
                ["HGBS11"], date(2026, 9, 4), {}
            )

        assert caso.call_args.kwargs["guidance_store"] == "GUIDANCE_STORE"
