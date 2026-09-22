from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest
import tkinter as tk

from flowscope.application.logging_port import LogReference
from flowscope.presentation.gui.presenter import FlowScopePresenter


class TestFlowScopePresenter:
    def test_on_operation_started_disabilita_botoes_e_muda_cursor(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        view.disable_all_buttons.assert_called_once()
        view.enter_busy.assert_called_once()

    def test_on_operation_finished_restaura_botoes_cursor_e_progresso(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        presenter.on_operation_finished()
        view.restore_all_buttons.assert_called_once()
        view.exit_busy.assert_called_once()
        view.clear_progress.assert_called_once()

    def test_transicao_0_1_1_0_dispara_efeitos_uma_unica_vez(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        presenter.on_operation_started()
        view.disable_all_buttons.assert_called_once()
        view.enter_busy.assert_called_once()

        presenter.on_operation_finished()
        view.restore_all_buttons.assert_not_called()
        view.exit_busy.assert_not_called()

        presenter.on_operation_finished()
        view.restore_all_buttons.assert_called_once()
        view.exit_busy.assert_called_once()
        view.clear_progress.assert_called_once()

    def test_busy_restaura_estado_mesmo_com_excecao(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        with pytest.raises(RuntimeError):
            with presenter.busy():
                raise RuntimeError("boom")

        assert presenter._operacoes_ativas == 0
        view.enter_busy.assert_called_once()
        view.exit_busy.assert_called_once()

    def test_exit_sem_operacao_ativa_e_idempotente(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_finished()
        assert presenter._operacoes_ativas == 0
        view.exit_busy.assert_not_called()
        view.restore_all_buttons.assert_not_called()

    def test_on_progress_delega_para_view(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_progress(3, 10, "Baixando...")
        view.set_progress.assert_called_once_with(3, 10, "Baixando...")

    def test_on_fundamental_progress_atualiza_barra_com_marcador(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_fundamental_progress("Fundamentos: HGBS11 (1/5)", 1, 5)
        view.set_progress.assert_called_once_with(
            1, 5, "• Fundamentos: HGBS11 (1/5)"
        )
        view.set_status.assert_not_called()

    def test_on_fundamental_progress_formato_antigo_usa_status(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_fundamental_progress("Fundamentos: HGBS11")
        view.set_status.assert_called_once_with("Fundamentos: HGBS11", "•")
        view.set_progress.assert_not_called()

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

    def test_copy_button_permanece_desabilitado_durante_operacao(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        presenter.on_result({"vwap": {}}, ["PETR4"], date(2024, 1, 15))

        assert view.config_copy_button_state.call_args[0][0] == tk.DISABLED

    def test_copy_button_habilita_ao_final_da_operacao(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        presenter.on_result({"vwap": {}}, ["PETR4"], date(2024, 1, 15))
        presenter.on_operation_finished()

        assert view.config_copy_button_state.call_args[0][0] == tk.NORMAL

    def test_copy_button_so_habilita_apos_fundamental(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        presenter.on_result({"vwap": {}}, ["PETR4"], date(2024, 1, 15))
        presenter.on_fundamental_started()
        presenter.on_operation_finished()

        assert view.config_copy_button_state.call_args[0][0] == tk.DISABLED

        presenter.on_fundamental_finished()
        assert view.config_copy_button_state.call_args[0][0] == tk.NORMAL

    def test_on_error_chama_set_status_com_mensagem(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        error = ValueError("dados inválidos")
        presenter.on_error(error)
        view.set_status.assert_called_once()
        args = view.set_status.call_args[0]
        assert "dados inválidos" in args[0]
        assert args[1] == "⚠"

    def test_on_fundamental_result_sem_falha_exibe_sucesso(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_fundamental_result({"X": 1})
        view.set_fundamental_data.assert_called_once_with({"X": 1})
        view.set_status.assert_called_once()
        args = view.set_status.call_args[0]
        assert args[0] == "Dados atualizados com sucesso."
        assert args[1] == "✓"

    def test_on_fundamental_result_com_falha_exibe_mitigacao(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_fundamental_result({"X": 1}, houve_falha=True)
        args = view.set_status.call_args[0]
        assert args[0] == "Dados atualizados com mitigação de falhas."
        assert args[1] == "⚠"

    def test_on_fundamental_error_exibe_falha(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_fundamental_error()
        args = view.set_status.call_args[0]
        assert args[0] == "Falha ao atualizar dados"
        assert args[1] == "⚠"

    def test_cursor_permanece_ate_analise_fundamental_terminar(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        presenter.on_fundamental_started()
        view.enter_busy.assert_called()
        presenter.on_operation_finished()
        view.exit_busy.assert_not_called()
        presenter.on_fundamental_finished()
        view.exit_busy.assert_called_once()

    def test_on_fundamental_started_desabilita_controles(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_fundamental_started()
        view.disable_all_buttons.assert_called_once()
        view.enter_busy.assert_called_once()

    def test_substituicao_de_job_mantem_contador_consistente(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        presenter.on_fundamental_started()
        presenter.on_operation_finished()
        presenter.on_fundamental_started()
        presenter.on_fundamental_finished()
        view.exit_busy.assert_not_called()
        assert presenter._operacoes_ativas == 1
        presenter.on_fundamental_finished()
        view.exit_busy.assert_called_once()
        view.restore_all_buttons.assert_called_once()
        assert presenter._operacoes_ativas == 0

    def test_nao_limpa_progresso_com_operacao_fundamental_ativa(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        presenter.on_fundamental_started()
        presenter.on_operation_finished()
        view.clear_progress.assert_not_called()

    def test_limpa_progresso_quando_todas_operacoes_terminam(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        presenter.on_fundamental_started()
        presenter.on_operation_finished()
        presenter.on_fundamental_finished()
        view.clear_progress.assert_called_once()

    def test_nao_restaura_controles_com_operacao_fundamental_ativa(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        presenter.on_fundamental_started()
        presenter.on_operation_finished()
        view.restore_all_buttons.assert_not_called()

    def test_restaura_controles_ao_final_da_fundamental(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        presenter.on_operation_started()
        presenter.on_fundamental_started()
        presenter.on_operation_finished()
        presenter.on_fundamental_finished()
        view.restore_all_buttons.assert_called_once()

    def test_on_technical_error_mostra_mensagem_do_log(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        error = RuntimeError("timeout")
        ref = LogReference(
            source="flowscope.log",
            identifier=datetime.now(timezone.utc).isoformat(),
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
