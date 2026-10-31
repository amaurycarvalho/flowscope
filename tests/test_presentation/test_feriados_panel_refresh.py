from unittest.mock import MagicMock

from flowscope.presentation.gui.charts.feriados_panel import FeriadosPanel


def _panel_sem_tk():
    panel = object.__new__(FeriadosPanel)
    panel._refreshing = False
    panel._refresh_button = MagicMock()
    panel._icon_refresh = "refresh"
    panel._icon_loading = "loading"
    panel._status = MagicMock()
    panel._render = MagicMock()
    return panel


def test_estado_do_botao_durante_atualizacao():
    panel = _panel_sem_tk()
    panel._set_refreshing(True)
    assert panel._refreshing is True
    panel._refresh_button.config.assert_any_call(state="disabled")
    panel._refresh_button.config.assert_any_call(image="loading")

    panel._set_refreshing(False)
    assert panel._refreshing is False
    panel._refresh_button.config.assert_any_call(state="normal")
    panel._refresh_button.config.assert_any_call(image="refresh")


def test_falha_preserva_conteudo_e_avisa():
    panel = _panel_sem_tk()
    panel._set_refreshing = MagicMock()
    panel._finish(None, RuntimeError("falha"))
    panel._render.assert_not_called()
    panel._status.assert_called_once()


def test_calendario_indisponivel_preserva_arvore():
    panel = _panel_sem_tk()
    panel._set_refreshing = MagicMock()
    panel._finish({2026: {"estado": "calendario_indisponivel", "feriados": []}}, None)
    panel._render.assert_not_called()
    panel._status.assert_called_once()


def test_sucesso_reconstroi_arvore():
    panel = _panel_sem_tk()
    panel._set_refreshing = MagicMock()
    panel._finish({
        2026: {
            "estado": "ok",
            "feriados": [
                {"data": "2026-01-01", "nome": "Confraternizacao", "origem": "ANBIMA"}
            ],
        }
    }, None)
    panel._render.assert_called_once()
    assert panel._status.call_args.args[1] == "✓"


def test_defasado_reconstroi_e_avisa():
    panel = _panel_sem_tk()
    panel._set_refreshing = MagicMock()
    panel._finish({
        2026: {
            "estado": "defasado",
            "feriados": [
                {"data": "2026-01-01", "nome": "Confraternizacao", "origem": "ANBIMA"}
            ],
        }
    }, None)
    panel._render.assert_called_once()
    assert panel._status.call_args.args[1] == "⚠"
