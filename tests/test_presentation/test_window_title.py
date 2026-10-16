"""Testes do título dinâmico da janela principal com o nome do watchlist."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from flowscope.presentation.gui.app_constants import TITLE_PREFIX

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


def _construir(monkeypatch, tmp_path, prefs):
    """Constrói a janela principal isolando config e preferências."""
    from flowscope.presentation.gui import app as app_mod

    monkeypatch.setattr(app_mod, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(app_mod, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(app_mod, "load_preferences", lambda: prefs)
    janela = app_mod.FlowScopeGUI()
    janela.update()
    return janela


@pytest.fixture
def gui(monkeypatch, tmp_path):
    """Constrói a janela principal com preferências padrão e a encerra ao final."""
    from flowscope.presentation.gui import app as app_mod

    janela = _construir(monkeypatch, tmp_path, dict(app_mod.DEFAULT_CONFIG))
    yield janela
    janela.destroy()


class TestTituloComposicao:
    @needs_display
    def test_sem_arquivo_exibe_nova_lista(self, gui):
        gui._watchlist_file = None
        gui._index_name = None
        gui._watchlist_dirty = False

        gui._update_window_title()
        gui.update()

        assert gui.title() == f"{TITLE_PREFIX} — Nova lista.txt"

    @needs_display
    def test_arquivo_carregado_exibe_basename_sem_asterisco(self, gui):
        gui._on_watchlist_file_changed(Path("/home/user/dados/petr4.txt"))
        gui.update()

        assert gui.title() == f"{TITLE_PREFIX} — petr4.txt"

    @needs_display
    def test_editar_conteudo_exibe_asterisco(self, gui):
        gui._on_watchlist_file_changed(Path("/home/user/dados/petr4.txt"))

        gui._on_watchlist_content_changed()
        gui.update()

        assert gui.title() == f"{TITLE_PREFIX} — petr4.txt*"

    @needs_display
    def test_selecao_nao_exibe_asterisco(self, gui, monkeypatch):
        monkeypatch.setattr(gui, "_controller", MagicMock())
        gui._on_watchlist_file_changed(Path("/home/user/dados/petr4.txt"))

        gui._ticker_list.set_tickers(["PETR4", "VALE3"])
        gui._ticker_list._on_listbox_select()
        gui.update()

        assert gui._watchlist_dirty is False
        assert gui.title() == f"{TITLE_PREFIX} — petr4.txt"

    @needs_display
    def test_indice_exibe_nome_do_indice(self, gui, monkeypatch):
        monkeypatch.setattr(gui, "_controller", MagicMock())

        gui._on_index_click("IBOV")
        gui.update()

        assert gui.title() == f"{TITLE_PREFIX} — IBOV.txt"


class TestPersistenciaArquivo:
    @needs_display
    def test_carregar_grava_caminho_no_config(self, gui, tmp_path):
        gui._on_watchlist_file_changed(Path("/home/user/dados/petr4.txt"))

        dados = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
        assert dados["last_ticker_file"] == "/home/user/dados/petr4.txt"

    @needs_display
    def test_indice_nao_sobrescreve_caminho(self, gui, monkeypatch, tmp_path):
        monkeypatch.setattr(gui, "_controller", MagicMock())
        gui._on_watchlist_file_changed(Path("/home/user/dados/petr4.txt"))

        gui._on_index_click("IBOV")

        dados = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
        assert dados["last_ticker_file"] == "/home/user/dados/petr4.txt"

    @needs_display
    def test_fechamento_grava_caminho(self, monkeypatch, tmp_path):
        from flowscope.presentation.gui import app as app_mod

        janela = _construir(monkeypatch, tmp_path, dict(app_mod.DEFAULT_CONFIG))
        janela._on_watchlist_file_changed(Path("/home/user/dados/petr4.txt"))

        janela._on_close()

        dados = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
        assert dados["last_ticker_file"] == "/home/user/dados/petr4.txt"


class TestRestauracaoNoStartup:
    @needs_display
    def test_restaura_basename_no_titulo(self, monkeypatch, tmp_path):
        from flowscope.presentation.gui import app as app_mod

        prefs = dict(app_mod.DEFAULT_CONFIG)
        prefs["last_ticker_file"] = "/home/user/dados/petr4.txt"

        janela = _construir(monkeypatch, tmp_path, prefs)
        try:
            janela.update()
            assert janela.title() == f"{TITLE_PREFIX} — petr4.txt"
        finally:
            janela.destroy()
