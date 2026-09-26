"""Testes de integração da aba de chat com a janela principal."""

import os

import pytest

from flowscope.presentation.gui import app_tab_actions as app_tab_actions_mod

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


@pytest.fixture
def gui(monkeypatch):
    """Constroi a janela principal com preferências padrão e a encerra ao final."""
    from flowscope.presentation.gui import app as app_mod

    monkeypatch.setattr(
        app_mod, "load_preferences", lambda: dict(app_mod.DEFAULT_CONFIG)
    )
    janela = app_mod.FlowScopeGUI()
    janela.update()
    yield janela
    janela.destroy()


def _abas(notebook) -> list[str]:
    """Lista os textos das abas de um notebook."""
    return [notebook.tab(i, "text") for i in range(notebook.index("end"))]


class TestAbaChatAI:
    @needs_display
    def test_aba_unica_entre_ticker_e_sobre(self, gui):
        abas = _abas(gui._main_notebook)
        assert "Chat AI" in abas
        assert (
            abas.index("Análise do Ticker")
            < abas.index("Chat AI")
            < abas.index("Sobre")
        )

    @needs_display
    def test_sem_subabas_de_chat(self, gui):
        assert "Chat Geral" not in _abas(gui._general_notebook)
        assert "Chat Ticker" not in _abas(gui._ticker_notebook)

    @needs_display
    def test_orientacao_da_aba_chat(self, gui):
        gui._select_tab(gui._main_notebook, "Chat AI")
        gui.update()
        titulo = gui._orientation_panel._title_label.cget("text")
        assert "Chat AI" in titulo


class TestContextoNoticias:
    @needs_display
    def test_chat_registra_fonte_de_noticias(self, gui):
        from flowscope.application.chat.noticias import FonteNoticias

        fontes = gui._chat_panel._fontes_adicionais
        assert any(isinstance(fonte, FonteNoticias) for fonte in fontes)


class TestCopiaComChatAtivo:
    @needs_display
    def test_texto_copia_chat(self, gui):
        gui._select_tab(gui._main_notebook, "Chat AI")
        gui.update()
        gui._chat_panel._registrar("user", "pergunta do chat")
        assert "pergunta do chat" in gui._texto_para_copiar()

    @needs_display
    def test_outra_subaba_nao_usa_chat(self, gui):
        gui._select_tab(gui._main_notebook, "Análise Geral")
        gui._select_tab(gui._general_notebook, "VWAP")
        gui.update()
        assert gui._chat_panel_para_tabs(gui._current_tabs()) is None

    @needs_display
    def test_botao_copiar_habilitado_no_chat(self, gui):
        gui._select_tab(gui._main_notebook, "Chat AI")
        gui.update()
        assert str(gui._copy_data_btn.cget("state")) == "normal"


class TestDialogoConfiguracao:
    @needs_display
    def test_salvar_reavalia_estado_do_chat(self, gui, monkeypatch):
        capturado: dict = {}

        class _Dialogo:
            def __init__(self, parent, config_port=None, on_saved=None):
                capturado["on_saved"] = on_saved

        monkeypatch.setattr(app_tab_actions_mod, "LLMConfigDialog", _Dialogo)
        reavaliados: list = []
        monkeypatch.setattr(
            gui, "_reavaliar_chat_llm", lambda: reavaliados.append(True)
        )
        gui._abrir_config_llm()
        capturado["on_saved"]()
        assert reavaliados == [True]

    @needs_display
    def test_reavaliar_chama_o_painel_unico(self, gui, monkeypatch):
        chamadas: list = []
        monkeypatch.setattr(
            gui._chat_panel, "avaliar_estado", lambda: chamadas.append("chat")
        )
        gui._reavaliar_chat_llm()
        assert chamadas == ["chat"]
