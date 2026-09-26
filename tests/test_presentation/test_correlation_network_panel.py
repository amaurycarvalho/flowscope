"""Testes do painel de rede de correlação/cointegração."""

import os
import tkinter as tk
from datetime import date, timedelta
from decimal import Decimal
from tkinter import ttk

import numpy as np
import pytest

from flowscope.application.network.dados import AVISO_COINT_INDISPONIVEL
from flowscope.presentation.gui.charts.correlation_network_panel import (
    CorrelationNetworkPanel,
)

START = date(2025, 1, 6)

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


def _business_days(n: int) -> list[date]:
    dias: list[date] = []
    atual = START
    while len(dias) < n:
        if atual.weekday() < 5:
            dias.append(atual)
        atual += timedelta(days=1)
    return dias


def _dados(n: int) -> dict:
    """Monta dois tickers com preços positivos ao longo de ``n`` dias úteis."""
    dias = _business_days(n)
    rng = np.random.default_rng(7)
    base = 10.0 + np.cumsum(rng.normal(scale=0.2, size=n))
    return {
        "PETR4": {
            "daily_data": [
                {"date": d, "last_price": Decimal(f"{v:.2f}")}
                for d, v in zip(dias, base)
            ]
        },
        "VALE3": {
            "daily_data": [
                {"date": d, "last_price": Decimal(f"{v:.2f}")}
                for d, v in zip(dias, base + rng.normal(scale=0.05, size=n))
            ]
        },
    }


def _widgets(widget: tk.Widget) -> list[tk.Widget]:
    encontrados = [widget]
    for filho in widget.winfo_children():
        encontrados.extend(_widgets(filho))
    return encontrados


class TestCorrelationNetworkPanel:
    @needs_display
    def test_update_desenha_grafo(self):
        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            painel.update(_dados(45))
            assert painel._empty_label.get_visible() is False
            assert painel._resultado is not None
            assert painel._resultado.correlation_available is True
            assert painel._positions
        finally:
            root.destroy()

    @needs_display
    def test_estado_vazio_sem_dados(self):
        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            painel.update({})
            assert painel._empty_label.get_visible() is True
        finally:
            root.destroy()

    @needs_display
    def test_estado_vazio_sem_densidade(self):
        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            painel.update(_dados(10))
            assert painel._empty_label.get_visible() is True
        finally:
            root.destroy()

    @needs_display
    def test_mensagem_estado_vazio_quebra_em_multiplas_linhas(self):
        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            painel.update(_dados(10))
            assert painel._empty_label.get_visible() is True
            assert painel._empty_label.get_wrap() is True
        finally:
            root.destroy()

    @needs_display
    def test_mensagem_estado_vazio_cabe_na_figura(self):
        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            painel.update(_dados(10))
            renderer = painel.get_figure().canvas.get_renderer()
            largura = painel._empty_label.get_window_extent(renderer).width
            assert largura <= painel.get_figure().bbox.width
        finally:
            root.destroy()

    @needs_display
    def test_sem_seletor_de_janela_proprio(self):
        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            widgets = _widgets(painel.frame)
            assert not any(isinstance(w, ttk.Combobox) for w in widgets)
            assert not any(isinstance(w, tk.Scale) for w in widgets)
        finally:
            root.destroy()

    @needs_display
    def test_calculo_sobre_dados_carregados(self):
        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            painel.update(_dados(45))
            antes = painel._resultado.tickers
            painel.update({"PETR4": _dados(45)["PETR4"]})
            assert painel._resultado.tickers != antes
            assert painel._resultado.tickers == ("PETR4",)
        finally:
            root.destroy()

    @needs_display
    def test_layout_deterministico(self):
        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            dados = _dados(45)
            painel.update(dados)
            primeiro = {k: v.copy() for k, v in painel._positions.items()}
            painel.update(dados)
            segundo = painel._positions
            assert set(primeiro) == set(segundo)
            for node in primeiro:
                assert np.allclose(primeiro[node], segundo[node])
        finally:
            root.destroy()

    @needs_display
    def test_aviso_cointegracao_indisponivel(self):
        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            painel.update(_dados(35))
            assert painel._resultado.cointegration_available is False
            textos = [texto.get_text() for texto in painel._ax.texts]
            assert any(AVISO_COINT_INDISPONIVEL in t for t in textos)
        finally:
            root.destroy()

    @needs_display
    def test_reset_exibe_estado_vazio(self):
        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            painel.update(_dados(45))
            painel.reset()
            assert painel._empty_label.get_visible() is True
        finally:
            root.destroy()

    @needs_display
    def test_toolbar_copia_grafico(self):
        root = tk.Tk()
        try:
            copiados = []
            painel = CorrelationNetworkPanel(
                root, copy_chart_callback=copiados.append
            )
            painel._toolbar.copy_chart()
            assert copiados == [painel.get_figure()]
        finally:
            root.destroy()

    @needs_display
    def test_toolbar_paridade_com_vwap(self):
        from flowscope.presentation.gui.charts.toolbar import ToolbarBR
        from flowscope.presentation.gui.charts.vwap_hist import VWAPHistChart

        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            vwap = VWAPHistChart(root)
            assert isinstance(painel._toolbar, ToolbarBR)
            assert type(painel._toolbar).toolitems == type(vwap._toolbar).toolitems
            assert set(painel._toolbar._buttons) == set(vwap._toolbar._buttons)
            assert "Salvar" in painel._toolbar._buttons
        finally:
            root.destroy()

    @needs_display
    def test_toolbar_navegacao_disponivel(self):
        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            painel.update(_dados(45))
            painel._toolbar.home()
            painel._toolbar.pan()
            painel._toolbar.zoom()
            painel._toolbar.home()
            assert painel._resultado is not None
        finally:
            root.destroy()

    @needs_display
    def test_toolbar_visivel_em_janela_baixa(self):
        root = tk.Tk()
        try:
            root.geometry("600x400")
            painel = CorrelationNetworkPanel(root)
            painel.frame.pack(fill="both", expand=True)
            root.update()
            assert painel._toolbar.winfo_ismapped()
            assert painel._toolbar.winfo_height() > 1
        finally:
            root.destroy()

    @needs_display
    def test_colorbar_removida_no_estado_vazio(self):
        root = tk.Tk()
        try:
            painel = CorrelationNetworkPanel(root)
            painel.update(_dados(45))
            assert painel._colorbar is not None
            painel.update({})
            assert painel._colorbar is None
        finally:
            root.destroy()
