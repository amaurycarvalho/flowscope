from unittest.mock import MagicMock, call
from datetime import date, datetime

from flowscope.application.logging_port import LogReference
from flowscope.presentation.gui.presenter import FlowScopePresenter


class TestFlowScopePresenter:
    def test_on_operation_started_disabilita_botoes_e_muda_cursor(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        view.disable_all_buttons.assert_called_once()
        view.set_wait_cursor.assert_called_once()

    def test_on_operation_finished_restaura_botoes_cursor_e_progresso(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_finished()
        view.restore_all_buttons.assert_called_once()
        view.clear_wait_cursor.assert_called_once()
        view.clear_progress.assert_called_once()

    def test_on_progress_delega_para_view(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_progress(3, 10, "Baixando...")
        view.set_progress.assert_called_once_with(3, 10, "Baixando...")

    def test_on_result_formata_dados_corretamente(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        result = {"vwap": {}}
        tickers = ["PETR4", "VALE3"]
        ref_date = date(2024, 1, 15)

        presenter.on_result(result, tickers, ref_date)

        view.set_current_data.assert_called_once_with(result)
        view.set_tickers_list.assert_called_once_with(tickers)
        view.config_copy_button_state.assert_called_once_with("normal")
        view.set_counter.assert_called_once()
        assert "Tickers (2)" in view.set_counter.call_args[0][0]
        view.set_date_label.assert_called_once_with("Dados: 2024-01-15")
        view.on_tab_changed.assert_called_once()
        view.set_status.assert_called_once()
        args = view.set_status.call_args[0]
        assert "carregado" in args[0]
        assert args[1] == "✓"

    def test_on_error_chama_set_status_com_mensagem(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        error = ValueError("dados inválidos")
        presenter.on_error(error)
        view.set_status.assert_called_once()
        args = view.set_status.call_args[0]
        assert "dados inválidos" in args[0]
        assert args[1] == "⚠"

    def test_on_technical_error_mostra_mensagem_do_log(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        error = RuntimeError("timeout")
        ref = LogReference(
            source="flowscope.log",
            identifier=datetime.now().isoformat(),
            hint="Consulte o arquivo de log em ~/.flowscope/logs/flowscope.log",
        )
        presenter.on_technical_error(error, ref)
        view.set_status.assert_called_once()
        args = view.set_status.call_args[0]
        assert "Erro técnico" in args[0]
        assert "flowscope.log" in args[0]

    def test_get_reference_date_le_da_view(self):
        view = MagicMock()
        view.get_reference_date.return_value = date(2024, 6, 1)
        presenter = FlowScopePresenter(view)
        result = presenter.get_reference_date()
        assert result == date(2024, 6, 1)
        view.get_reference_date.assert_called_once()

    def test_get_current_tickers_le_da_view(self):
        view = MagicMock()
        view.get_current_tickers.return_value = ["PETR4", "VALE3"]
        presenter = FlowScopePresenter(view)
        result = presenter.get_current_tickers()
        assert result == ["PETR4", "VALE3"]
        view.get_current_tickers.assert_called_once()
