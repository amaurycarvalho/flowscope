from unittest.mock import MagicMock, call
from datetime import date

from flowscope.application.load_portfolio_use_case import (
    PortfolioNotFoundError,
)
from flowscope.presentation.gui.controller import FlowScopeController
from flowscope.presentation.gui.presenter import FlowScopePresenter


def _make_controller(**overrides):
    defaults = dict(
        guard=MagicMock(),
        load_portfolio=MagicMock(),
        analyze=MagicMock(),
        presenter=MagicMock(),
        logger=MagicMock(),
    )
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


class TestOnIndexClicked:
    def test_successo_chama_presenter_na_ordem(self):
        guard = MagicMock()
        guard.acquire.return_value = _mock_context(True)
        load_portfolio = MagicMock()
        load_portfolio.execute.return_value = ["PETR4", "VALE3"]
        analyze = MagicMock()
        analyze.execute.return_value = {"vwap": {}}
        presenter = MagicMock()
        presenter.get_reference_date.return_value = date(2024, 1, 15)

        controller = _make_controller(
            guard=guard, load_portfolio=load_portfolio,
            analyze=analyze, presenter=presenter,
        )
        controller.on_index_clicked("IBOV")

        args, kwargs = load_portfolio.execute.call_args
        assert args[0] == "IBOV"
        assert callable(kwargs["progress_callback"])
        mc = presenter.mock_calls
        idx_started = mc.index(call.on_operation_started())
        idx_loaded = mc.index(call.on_portfolio_loaded(["PETR4", "VALE3"]))
        idx_refdate = mc.index(call.get_reference_date())
        idx_result = mc.index(
            call.on_result({"vwap": {}}, ["PETR4", "VALE3"], date(2024, 1, 15))
        )
        idx_finished = mc.index(call.on_operation_finished())
        assert idx_started < idx_loaded < idx_refdate < idx_result < idx_finished

    def test_guard_bloqueia_segundo_clique(self):
        guard = MagicMock()
        guard.acquire.return_value = _mock_context(False)
        presenter = MagicMock()

        controller = _make_controller(guard=guard, presenter=presenter)
        controller.on_index_clicked("IBOV")

        presenter.assert_not_called()

    def test_portfolio_not_found_chama_operation_finished_sem_result(self):
        guard = MagicMock()
        guard.acquire.return_value = _mock_context(True)
        load_portfolio = MagicMock()
        load_portfolio.execute.side_effect = PortfolioNotFoundError()
        presenter = MagicMock()

        controller = _make_controller(
            guard=guard, load_portfolio=load_portfolio, presenter=presenter,
        )
        controller.on_index_clicked("IBOV")

        mc = presenter.mock_calls
        idx_started = mc.index(call.on_operation_started())
        idx_finished = mc.index(call.on_operation_finished())
        assert idx_started < idx_finished
        assert call.on_result not in mc

    def test_excecao_generica_chama_on_technical_error(self):
        guard = MagicMock()
        guard.acquire.return_value = _mock_context(True)
        load_portfolio = MagicMock()
        load_portfolio.execute.side_effect = RuntimeError("bug")
        presenter = MagicMock()

        controller = _make_controller(
            guard=guard, load_portfolio=load_portfolio, presenter=presenter,
        )
        controller.on_index_clicked("IBOV")

        mc = presenter.mock_calls
        idx_started = mc.index(call.on_operation_started())
        presenter.on_technical_error.assert_called_once()
        args = presenter.on_technical_error.call_args[0]
        assert isinstance(args[0], RuntimeError)
        assert str(args[0]) == "bug"
        idx_finished = mc.index(call.on_operation_finished())
        assert idx_started < mc.index(call.on_technical_error(args[0], args[1])) < idx_finished


class TestOnLoadData:
    def test_sucesso_com_tickers_existentes(self):
        guard = MagicMock()
        guard.acquire.return_value = _mock_context(True)
        load_portfolio = MagicMock()
        analyze = MagicMock()
        analyze.execute.return_value = {"vwap": {}}
        presenter = MagicMock()
        presenter.get_current_tickers.return_value = ["PETR4", "VALE3"]
        presenter.get_reference_date.return_value = date(2024, 1, 15)

        controller = _make_controller(
            guard=guard, load_portfolio=load_portfolio,
            analyze=analyze, presenter=presenter,
        )
        controller.on_load_data()

        load_portfolio.execute.assert_not_called()
        mc = presenter.mock_calls
        idx_started = mc.index(call.on_operation_started())
        idx_tickers = mc.index(call.get_current_tickers())
        idx_refdate = mc.index(call.get_reference_date())
        idx_result = mc.index(
            call.on_result({"vwap": {}}, ["PETR4", "VALE3"], date(2024, 1, 15))
        )
        idx_finished = mc.index(call.on_operation_finished())
        assert idx_started < idx_tickers < idx_refdate < idx_result < idx_finished

    def test_sucesso_com_tickers_vazios_fallback_idiv(self):
        guard = MagicMock()
        guard.acquire.return_value = _mock_context(True)
        load_portfolio = MagicMock()
        load_portfolio.execute.return_value = ["PETR4", "VALE3"]
        analyze = MagicMock()
        analyze.execute.return_value = {"vwap": {}}
        presenter = MagicMock()
        presenter.get_current_tickers.return_value = []
        presenter.get_reference_date.return_value = date(2024, 1, 15)

        controller = _make_controller(
            guard=guard, load_portfolio=load_portfolio,
            analyze=analyze, presenter=presenter,
        )
        controller.on_load_data()

        args, kwargs = load_portfolio.execute.call_args
        assert args[0] == "IDIV"
        assert callable(kwargs["progress_callback"])
        mc = presenter.mock_calls
        idx_started = mc.index(call.on_operation_started())
        idx_tickers = mc.index(call.get_current_tickers())
        idx_loaded = mc.index(call.on_portfolio_loaded(["PETR4", "VALE3"]))
        idx_result = mc.index(
            call.on_result({"vwap": {}}, ["PETR4", "VALE3"], date(2024, 1, 15))
        )
        idx_finished = mc.index(call.on_operation_finished())
        assert idx_started < idx_tickers < idx_loaded < idx_result < idx_finished

    def test_fallback_idiv_levanta_portfolio_not_found(self):
        guard = MagicMock()
        guard.acquire.return_value = _mock_context(True)
        load_portfolio = MagicMock()
        load_portfolio.execute.side_effect = PortfolioNotFoundError()
        presenter = MagicMock()
        presenter.get_current_tickers.return_value = []

        controller = _make_controller(
            guard=guard, load_portfolio=load_portfolio, presenter=presenter,
        )
        controller.on_load_data()

        presenter.set_status.assert_called_once()
        args = presenter.set_status.call_args[0]
        assert "não foi possível" in args[0].lower()
        presenter.on_operation_finished.assert_called_once()

    def test_guard_bloqueia_chamadas_concorrentes(self):
        guard = MagicMock()
        guard.acquire.return_value = _mock_context(False)
        presenter = MagicMock()

        controller = _make_controller(guard=guard, presenter=presenter)
        controller.on_load_data()

        presenter.assert_not_called()


class TestOnToday:
    def test_on_today_nao_leva_attribute_error(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        guard = MagicMock()
        guard.acquire.return_value = _mock_context(False)

        controller = _make_controller(presenter=presenter, guard=guard)
        controller.on_today()

        view._date_entry.set_date.assert_called_once()


class TestOnTickerEdit:
    def test_on_ticker_edit_sem_tickers_carrega_idiv(self):
        view = MagicMock()
        view._resolve_current_chart.return_value = None
        view.get_current_tickers.return_value = []
        presenter = FlowScopePresenter(view)
        load_portfolio = MagicMock()
        load_portfolio.execute.return_value = ["PETR4"]

        controller = _make_controller(
            presenter=presenter, load_portfolio=load_portfolio,
        )
        controller.on_ticker_edit()

        load_portfolio.execute.assert_called_once_with("IDIV")
        view.set_tickers.assert_called_once_with(["PETR4"])

    def test_on_ticker_edit_sem_tickers_idiv_nao_encontrado(self):
        view = MagicMock()
        view.get_current_tickers.return_value = []
        presenter = FlowScopePresenter(view)
        load_portfolio = MagicMock()
        load_portfolio.execute.side_effect = PortfolioNotFoundError()

        controller = _make_controller(
            presenter=presenter, load_portfolio=load_portfolio,
        )
        controller.on_ticker_edit()

        load_portfolio.execute.assert_called_once_with("IDIV")
        view._flash_status.assert_called_once()

    def test_on_ticker_edit_com_tickers_aplica_filtro(self):
        view = MagicMock()
        view._resolve_current_chart.return_value = None
        presenter = FlowScopePresenter(view)
        presenter.get_current_tickers = MagicMock(return_value=["PETR4"])

        controller = _make_controller(presenter=presenter)
        controller.on_ticker_edit()

        view._set_wait_cursor.assert_called_once()
        view._clear_wait_cursor.assert_called_once()
        view._flash_status.assert_called_once()
