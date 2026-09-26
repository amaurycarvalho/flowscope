"""Testes headless do painel de VWAP.

Montam o painel sem Tk (figura matplotlib pura e canvas stub) para cobrir a
gestão do estado de hover e a atualização repetida, que não dependem de
interface gráfica.
"""

from datetime import date
from types import SimpleNamespace

from matplotlib.figure import Figure

from flowscope.presentation.gui.charts.empty_state import create_empty
from flowscope.presentation.gui.charts.vwap_hist import VWAPHistChart

D1 = date(2025, 1, 1)
D2 = date(2025, 1, 2)


def _dia(dt: date, avg: float, minimo: float, maximo: float,
         ultimo: float, qty: int) -> dict:
    return {
        "date": dt,
        "avg_price": avg,
        "min_price": minimo,
        "max_price": maximo,
        "last_price": ultimo,
        "fin_instr_qty": qty,
    }


def _data() -> dict:
    return {
        "PETR4": {
            "vwap": {"period_vwap": 100},
            "daily_data": [
                _dia(D1, 105.0, 100.0, 110.0, 108.0, 10),
                _dia(D2, 95.0, 90.0, 100.0, 92.0, 20),
            ],
        }
    }


def _headless_chart() -> VWAPHistChart:
    """Monta o painel sem Tk, com figura matplotlib pura e canvas stub."""
    chart = object.__new__(VWAPHistChart)
    figure = Figure()
    axes = figure.add_subplot(111)
    chart._axes = axes
    chart._figure = figure
    chart._all_axes = [axes]
    chart._empty_label = create_empty(figure, [axes])
    chart._canvas = SimpleNamespace(draw=lambda: None, draw_idle=lambda: None)
    chart._hover_tickers = []
    chart._hover_vwaps = []
    chart._hover_buckets = []
    chart._hover_last_pct = []
    chart._violin_polygons = []
    chart._annot = chart._create_annotation()
    return chart


class TestClearHoverState:
    def test_limpa_apos_store_com_tuplas(self):
        chart = _headless_chart()
        chart._store_hover_state(
            ("PETR4",), (100.0,), (((0.0,), (1.0,)),), (-5.0,)
        )
        chart._clear_hover_state()
        assert chart._hover_tickers == []
        assert chart._hover_vwaps == []
        assert chart._hover_buckets == []
        assert chart._hover_last_pct == []
        assert chart._violin_polygons == []

    def test_limpa_apos_store_com_listas(self):
        chart = _headless_chart()
        chart._store_hover_state(
            ["PETR4"], [100.0], [([0.0], [1.0])], [-5.0]
        )
        chart._clear_hover_state()
        assert chart._hover_tickers == []
        assert chart._hover_vwaps == []


class TestUpdateHeadless:
    def test_update_duas_vezes_nao_falha_e_mantem_estado(self):
        chart = _headless_chart()
        chart.update(_data())
        chart.update(_data())
        assert list(chart._hover_tickers) == ["PETR4"]
        assert list(chart._hover_last_pct) == [-8.0]
        assert chart._violin_polygons

    def test_update_vazio_exibe_estado_vazio(self):
        chart = _headless_chart()
        chart.update({})
        assert chart._empty_label.get_visible() is True
        assert chart._hover_tickers == []
