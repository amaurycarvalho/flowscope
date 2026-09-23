"""Testes do tratamento da aba "Sobre" na navegação."""

import os
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock

import pytest

from flowscope.presentation.gui.app_actions import ActionsMixin
from flowscope.presentation.gui.app_tab_actions import TabActionsMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.app_tabs import ABOUT_TAB
from flowscope.presentation.gui.widgets.about_panel import AboutPanel

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


class TestCurrentTabs:
    def test_reconhece_sobre_sem_ler_subnotebooks(self):
        host = MagicMock()
        host._main_notebook.tab.return_value = ABOUT_TAB
        assert TabActionsMixin._current_tabs(host) == (ABOUT_TAB, ABOUT_TAB)
        host._ticker_notebook.tab.assert_not_called()
        host._general_notebook.tab.assert_not_called()

    def test_analise_geral_le_subaba_geral(self):
        host = MagicMock()
        host._main_notebook.tab.return_value = "Análise Geral"
        host._general_notebook.tab.return_value = "Fundamentos"
        assert TabActionsMixin._current_tabs(host) == (
            "Análise Geral",
            "Fundamentos",
        )


class TestResolucaoDeGrafico:
    def test_resolve_chart_sobre_e_none(self):
        host = MagicMock()
        assert ActionsMixin._resolve_chart(host, ABOUT_TAB, ABOUT_TAB) is None

    def test_resolve_current_chart_sobre_nao_le_ticker(self):
        host = MagicMock()
        host._main_notebook.tab.return_value = ABOUT_TAB
        assert ActionsMixin._resolve_current_chart(host) is None
        host._ticker_notebook.tab.assert_not_called()


class TestOnTabChanged:
    def test_sobre_nao_resolve_grafico_nem_painel(self):
        host = MagicMock()
        host._prefs = {}
        host._current_tabs = MagicMock(return_value=(ABOUT_TAB, ABOUT_TAB))

        TabActionsMixin._on_tab_changed(host)

        host._resolve_chart.assert_not_called()
        host._orientation_panel.set_content.assert_not_called()
        host._verificar_nova_versao.assert_called_once()
        assert host._prefs["last_tab"] == ABOUT_TAB


class _FakeNotebook:
    def __init__(self, textos):
        self._textos = list(textos)
        self.selecionado = None

    def index(self, _arg=None):
        return len(self._textos)

    def tab(self, indice, _opcao):
        return self._textos[indice]

    def select(self, indice):
        self.selecionado = indice


class _HostRestore(TabsLayoutMixin):
    def __init__(self, main, general, ticker):
        self._main_notebook = main
        self._general_notebook = general
        self._ticker_notebook = ticker
        self.chamadas = 0

    def _on_tab_changed(self):
        self.chamadas += 1


class TestRestoreTabs:
    def test_sobre_seleciona_sem_mexer_subnotebooks(self):
        main = _FakeNotebook(["Análise Geral", "Análise do Ticker", ABOUT_TAB])
        general = _FakeNotebook(["Fundamentos"])
        ticker = _FakeNotebook(["Documentos"])
        host = _HostRestore(main, general, ticker)

        host._restore_tabs(ABOUT_TAB, "Documentos")

        assert main.selecionado == 2
        assert general.selecionado is None
        assert ticker.selecionado is None
        assert host.chamadas == 1

    def test_analise_geral_seleciona_subaba(self):
        main = _FakeNotebook(["Análise Geral", "Análise do Ticker", ABOUT_TAB])
        general = _FakeNotebook(["Fundamentos", "VWAP"])
        ticker = _FakeNotebook(["Documentos"])
        host = _HostRestore(main, general, ticker)

        host._restore_tabs("Análise Geral", "VWAP")

        assert main.selecionado == 0
        assert general.selecionado == 1
        assert ticker.selecionado is None


@needs_display
class TestBuildAboutTab:
    def test_posiciona_apos_analise_do_ticker(self):
        root = tk.Tk()
        try:
            host = MagicMock()
            host._main_notebook = ttk.Notebook(root)
            host._main_notebook.add(
                ttk.Frame(host._main_notebook), text="Análise Geral"
            )
            host._main_notebook.add(
                ttk.Frame(host._main_notebook), text="Análise do Ticker"
            )
            host._load_icon = MagicMock(
                return_value=tk.PhotoImage(width=2, height=2)
            )
            host._abrir_repositorio = MagicMock()
            host._abrir_log_flowscope = MagicMock()

            TabsLayoutMixin._build_about_tab(host)

            textos = [
                host._main_notebook.tab(i, "text")
                for i in range(host._main_notebook.index("end"))
            ]
            assert textos == ["Análise Geral", "Análise do Ticker", ABOUT_TAB]
            assert isinstance(host._about_panel, AboutPanel)
        finally:
            root.destroy()
