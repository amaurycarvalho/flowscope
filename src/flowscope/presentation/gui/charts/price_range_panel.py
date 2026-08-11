"""Painel de gráfico de amplitude de preços de um ativo no FlowScope."""

import tkinter as tk
import warnings
from collections.abc import Callable

from matplotlib.backend_bases import MouseEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.presentation.gui.charts.empty_state import (
    create_empty,
    hide_empty,
    show_empty,
)
from flowscope.presentation.gui.charts.price_range_helpers import (
    as_dict,
    draw_clv_gauge,
    draw_main_chart,
    tooltip_lines,
)
from flowscope.presentation.gui.charts.toolbar import ToolbarBR


class PriceRangePanel:
    """Exibe a amplitude de preços diária e o medidor de CLV de um ativo."""

    def __init__(
        self: "PriceRangePanel",
        parent: tk.Widget,
        *,
        copy_chart_callback: Callable[[Figure], None] | None = None,
    ) -> None:
        """Cria o painel de amplitude de preços com seus eixos e toolbar.

        Configura a figura, a grade de subplots, o canvas Tkinter, a toolbar
        e a anotação de hover usada para inspecionar os pregos do gráfico.
        """
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 4), dpi=100)
        self._gs = self._figure.add_gridspec(
            nrows=2, ncols=1, height_ratios=[3, 0.6],
            hspace=0.3,
        )
        self._ax_main = self._figure.add_subplot(self._gs[0])
        self._ax_clv = self._figure.add_subplot(self._gs[1])

        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._toolbar = ToolbarBR(
            self._canvas, self.frame, copy_chart_callback=copy_chart_callback,
        )

        self._all_axes = [self._ax_main, self._ax_clv]
        self._empty_label = create_empty(self._figure, self._all_axes)

        self._hover_data: list[dict] = []
        self._annot = self._ax_main.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "yellow", "ec": "gray", "alpha": 0.8},
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("motion_notify_event", self._on_motion)

    def update(self: "PriceRangePanel", data: dict,
               ticker: str | None = None) -> None:
        """Atualiza o gráfico com os dados de amplitude de preços do ativo.

        Quando os dados ou o ticker são inválidos, exibe o estado vazio;
        caso contrário, redesenha o gráfico principal e o medidor de CLV.
        """
        self._hover_data.clear()

        if not data or not ticker or ticker not in data:
            show_empty(self._figure, self._all_axes, self._empty_label)
            self._canvas.draw()
            return

        hide_empty(self._empty_label)
        for ax in [self._ax_main, self._ax_clv]:
            ax.clear()

        info = data[ticker]
        daily = info.get("daily_data", [])
        if not daily:
            show_empty(self._figure, self._all_axes, self._empty_label)
            self._canvas.draw()
            return

        all_inds = info.get("all_indicators", {})
        daily_sorted = sorted(daily, key=lambda x: x["date"])

        typical_dict = as_dict(all_inds.get("typical_price"))
        median_dict = as_dict(all_inds.get("median_price"))
        weighted_dict = as_dict(all_inds.get("weighted_close"))
        range_pct_dict = as_dict(all_inds.get("range_percentual"))
        clv_dict = as_dict(all_inds.get("clv"))
        eff_dict = as_dict(all_inds.get("daily_efficiency"))

        draw_main_chart(self._ax_main, daily_sorted, typical_dict,
                        median_dict, weighted_dict, range_pct_dict,
                        eff_dict, ticker, self._hover_data)
        draw_clv_gauge(self._ax_clv, daily_sorted, clv_dict)

        self._attach_annot()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self._figure.tight_layout()
        self._canvas.draw()

    def _attach_annot(self: "PriceRangePanel") -> None:
        """Reanexa a anotação de hover após limpar o eixo principal."""
        self._annot = self._ax_main.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "yellow", "ec": "gray", "alpha": 0.8},
            fontsize=9, visible=False, zorder=10,
        )

    def _on_motion(self: "PriceRangePanel", event: MouseEvent) -> None:
        """Exibe o tooltip do ponto mais próximo durante o movimento do mouse."""
        if event.inaxes != self._ax_main or not self._hover_data:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return

        closest = None
        min_dist = 0.3
        for i, pt in enumerate(self._hover_data):
            dy = abs(event.ydata - i)
            if dy < min_dist:
                min_dist = dy
                closest = pt

        if closest:
            self._show_tooltip(closest, event.xdata, event.ydata)
        else:
            self._annot.set_visible(False)
            self._canvas.draw_idle()

    def _show_tooltip(self: "PriceRangePanel", pt: dict,
                      x: float, y: float) -> None:
        """Posiciona a anotação com as informações do ponto sob o cursor."""
        self._annot.set_text("\n".join(tooltip_lines(pt)))
        self._annot.xy = (x, y)
        self._annot.set_visible(True)
        self._canvas.draw_idle()

    def reset(self: "PriceRangePanel") -> None:
        """Limpa o gráfico e exibe o estado vazio."""
        show_empty(self._figure, self._all_axes, self._empty_label)
        self._canvas.draw()

    def get_figure(self: "PriceRangePanel") -> Figure:
        """Retorna a figura matplotlib utilizada pelo painel."""
        return self._figure
