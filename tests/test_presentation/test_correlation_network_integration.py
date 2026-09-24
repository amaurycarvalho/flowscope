"""Testes de integração da sub-aba "Rede de Correlação" na Análise Geral."""

import os
import tkinter as tk
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from flowscope.presentation.gui.app_actions import ActionsMixin
from flowscope.presentation.gui.app_layout import LayoutMixin
from flowscope.presentation.gui.app_tab_actions import TabActionsMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.app_tabs import TAB_CONTENT
from flowscope.presentation.gui.charts.correlation_network_panel import (
    CorrelationNetworkPanel,
)

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)

BASE = date(2025, 1, 6)


def _dados(n: int, ticker: str = "PETR4") -> dict:
    return {
        ticker: {
            "daily_data": [
                {
                    "date": BASE + timedelta(days=i),
                    "last_price": Decimal(str(10 + i % 5)),
                }
                for i in range(n)
            ]
        }
    }


class _AppHost(
    tk.Tk, LayoutMixin, TabsLayoutMixin, TabActionsMixin, ActionsMixin
):
    """Host mínimo que constrói a área principal real com as abas."""

    def __init__(self) -> None:
        super().__init__()
        self._prefs = {"last_tab": "Análise Geral", "last_subtab": "VWAP"}
        self._current_data: dict = {}
        self._button_states: dict = {}
        self._ticker_selecionado = None
        self._build_main_area()

    def _copy_chart(self, figure: object) -> None:
        pass

    def _on_quadrant_summary(self, *args: object) -> None:
        pass

    def _on_flow_summary(self, *args: object) -> None:
        pass

    def _on_ticker_dir_changed(self, directory: object) -> None:
        pass

    def _build_about_tab(self) -> None:
        self._about_panel = None


class TestRegistroSubAba:
    @needs_display
    def test_subaba_aparece_apos_dominancia(self):
        host = _AppHost()
        try:
            textos = [
                host._general_notebook.tab(i, "text")
                for i in range(host._general_notebook.index("end"))
            ]
            assert "Rede de Correlação" in textos
            assert textos.index("Rede de Correlação") == textos.index(
                "Dominância do Pregão"
            ) + 1
            assert isinstance(
                host._correlation_network_panel, CorrelationNetworkPanel
            )
        finally:
            host.destroy()

    @needs_display
    def test_general_inclui_painel_da_rede(self):
        host = _AppHost()
        try:
            assert (
                host._GENERAL["Rede de Correlação"]
                is host._correlation_network_panel
            )
        finally:
            host.destroy()


class TestResolucaoEDespacho:
    @needs_display
    def test_resolve_chart_retorna_painel(self):
        host = _AppHost()
        try:
            assert ActionsMixin._resolve_chart(
                host, "Análise Geral", "Rede de Correlação"
            ) is host._correlation_network_panel
        finally:
            host.destroy()

    @needs_display
    def test_selecionar_subaba_atualiza_rede(self):
        host = _AppHost()
        try:
            host._current_data = _dados(45)
            host._ticker_list.get_tickers = MagicMock(return_value=["PETR4"])
            indice = next(
                i
                for i in range(host._general_notebook.index("end"))
                if host._general_notebook.tab(i, "text") == "Rede de Correlação"
            )
            host._general_notebook.select(indice)
            host._on_tab_changed()
            assert host._correlation_network_panel._resultado is not None
            assert host._correlation_network_panel._resultado.tickers == (
                "PETR4",
            )
        finally:
            host.destroy()

    def test_do_update_despacha_para_painel(self):
        import types

        host = MagicMock()
        host._correlation_network_panel = MagicMock()
        host._current_data = {"PETR4": {"daily_data": []}}
        host._ticker_list.get_tickers.return_value = ["PETR4"]
        host._ticker_charts = set()
        host._update_especial = types.MethodType(
            ActionsMixin._update_especial, host
        )

        ActionsMixin._do_update(host, host._correlation_network_panel)

        host._correlation_network_panel.update.assert_called_once_with(
            {"PETR4": {"daily_data": []}}, tickers=["PETR4"]
        )

    def test_mudanca_de_periodo_recalcula(self):
        host = MagicMock()
        host._period_var.get.return_value = "Últimos 30 dias"
        host._PERIOD_STATUS = {"Últimos 30 dias": "status"}
        host._current_data = {"PETR4": {}}

        ActionsMixin._on_period_combo_changed(host)

        host._controller.on_load_data.assert_called_once()

    def test_mudanca_de_amostragem_recalcula(self):
        host = MagicMock()
        host._sampling_var.get.return_value = "Todos os dias"
        host._SAMPLING_STATUS = {"Todos os dias": "status"}
        host._current_data = {"PETR4": {}}

        ActionsMixin._on_sampling_combo_changed(host)

        host._controller.on_load_data.assert_called_once()


class TestRestauracaoSubAba:
    @needs_display
    def test_restaura_ultima_subaba_rede(self):
        host = _AppHost()
        try:
            host._restore_tabs("Análise Geral", "Rede de Correlação")
            selecionada = host._general_notebook.tab(
                host._general_notebook.select(), "text"
            )
            assert selecionada == "Rede de Correlação"
        finally:
            host.destroy()

    @needs_display
    def test_on_tab_changed_guarda_last_subtab(self):
        host = _AppHost()
        try:
            host._prefs = {}
            indice = next(
                i
                for i in range(host._general_notebook.index("end"))
                if host._general_notebook.tab(i, "text") == "Rede de Correlação"
            )
            host._general_notebook.select(indice)
            host._on_tab_changed()
            assert host._prefs["last_subtab"] == "Rede de Correlação"
        finally:
            host.destroy()


class TestConteudoOrientacao:
    def test_entry_existe(self):
        assert ("Análise Geral", "Rede de Correlação") in TAB_CONTENT

    def test_secoes_obrigatorias(self):
        titulo, corpo = TAB_CONTENT[("Análise Geral", "Rede de Correlação")]
        assert "Rede de Correlação" in titulo
        texto = "".join(parte for parte, _ in corpo)
        for secao in (
            "Objetivo:",
            "Responde a pergunta:",
            "Indicadores envolvidos:",
            "Como interpretar:",
        ):
            assert secao in texto
        assert "correlação" in texto
        assert "cointegração" in texto
        assert "no mínimo 40" in texto
        assert "Todos os dias" in texto
