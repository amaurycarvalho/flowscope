"""Gráfico de quadrantes comparando CLV e desvio do VWAP entre ativos.

A classe QuadrantChart desenha os pontos finais dos ativos sobre os
quatro quadrantes formados pelos eixos do CLV e do desvio do VWAP.
"""

import math
import tkinter as tk
from collections.abc import Callable

import matplotlib
from matplotlib.backend_bases import MouseEvent, PickEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.presentation.gui.charts.empty_state import (
    create_empty,
    hide_empty,
    show_empty,
)
from flowscope.presentation.gui.charts.quadrant_data import (
    build_trajectories,
    compute_scatter_data,
    generate_summary,
)
from flowscope.presentation.gui.charts.toolbar import ToolbarBR


class QuadrantChart:
    """Dispõe os ativos em quadrantes conforme CLV e desvio percentual do VWAP."""

    def __init__(
        self: "QuadrantChart",
        parent: tk.Widget,
        *,
        copy_chart_callback: Callable[[Figure], None] | None = None,
        summary_callback: Callable[[str], None] | None = None,
    ) -> None:
        """Cria o gráfico de quadrantes com sua toolbar.

        Configura a figura, os eixos e o rótulo de estado vazio, além
        de conectar os eventos de seleção e movimento do mouse.
        """
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 3), dpi=100)
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._toolbar = ToolbarBR(
            self._canvas, self.frame, copy_chart_callback=copy_chart_callback
        )

        self._all_axes = [self._axes]
        self._empty_label = create_empty(self._figure, self._all_axes)

        self._summary_callback = summary_callback
        self._hover_data: list[dict] = []
        self._scatter = None
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "yellow", "ec": "gray", "alpha": 0.8},
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("pick_event", self._on_pick)
        self._canvas.mpl_connect("motion_notify_event", self._on_motion)

    def update(self: "QuadrantChart", data: dict,
               *, show_arrows: bool = False) -> None:
        """Atualiza o gráfico com as trajetórias dos ativos nos quadrantes."""
        self._hover_data.clear()
        self._scatter = None

        if not data:
            self._show_empty()
            return

        hide_empty(self._empty_label)
        self._axes.clear()

        trajectories = build_trajectories(data)
        if not trajectories:
            self._show_empty()
            return

        self._plot_trajectories(trajectories, show_arrows)
        self._figure.tight_layout()
        self._attach_annot()
        self._canvas.draw()

        if self._summary_callback:
            self._summary_callback(self._generate_summary(trajectories))

    def _show_empty(self: "QuadrantChart") -> None:
        """Limpa os eixos e exibe o rótulo de estado vazio."""
        show_empty(self._figure, self._all_axes, self._empty_label)
        self._canvas.draw()

    def _plot_trajectories(self: "QuadrantChart",
                           trajectories: list[list[dict]],
                           show_arrows: bool) -> None:
        """Desenha as trajetórias e o marcador final de cada ativo."""
        if show_arrows:
            self._draw_arrows(trajectories)

        (last_x, last_y, last_sizes, last_colors,
         all_y, last_points) = compute_scatter_data(trajectories)
        self._hover_data = last_points

        cmap = matplotlib.colormaps["RdYlGn"]
        self._scatter = self._axes.scatter(
            last_x, last_y, s=last_sizes, c=last_colors, cmap=cmap,
            vmin=-1, vmax=1, edgecolors="black", linewidth=0.5,
            alpha=0.8, zorder=5, picker=True, pickradius=5,
        )

        self._annotate_tickers()
        self._style_axes(all_y)

    def _draw_arrows(self: "QuadrantChart",
                     trajectories: list[list[dict]]) -> None:
        """Desenha as setas que ligam os pontos consecutivos da trajetória."""
        for points in trajectories:
            for i in range(len(points) - 1):
                p0, p1 = points[i], points[i + 1]
                self._axes.arrow(
                    p0["clv"], p0["vwap_dist"],
                    p1["clv"] - p0["clv"], p1["vwap_dist"] - p0["vwap_dist"],
                    head_width=0.02, head_length=0.02,
                    fc="gray", ec="gray", alpha=0.3,
                    length_includes_head=True, zorder=2,
                )

    def _annotate_tickers(self: "QuadrantChart") -> None:
        """Rotula cada ponto final com o ticker do ativo correspondente."""
        for pt in self._hover_data:
            self._axes.annotate(
                pt["ticker"],
                xy=(pt["clv"], pt["vwap_dist"]),
                xytext=(5, 5), textcoords="offset points",
                fontsize=7, alpha=0.8,
                bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.5},
            )

    def _style_axes(self: "QuadrantChart", all_y: list[float]) -> None:
        """Aplica rótulos, limites e textos auxiliares nos eixos."""
        self._axes.axhline(y=0, color="gray", linestyle="--", linewidth=0.8, zorder=1)
        self._axes.axvline(x=0, color="gray", linestyle="--", linewidth=0.8, zorder=1)

        self._axes.set_xlabel("CLV")
        self._axes.set_ylabel("Desvio do VWAP (%)")
        self._axes.set_title("Quadrantes — CLV vs VWAP Distance")

        x_margin = 0.1
        self._axes.set_xlim(-1 - x_margin, 1 + x_margin)

        y_max_abs = max(abs(min(all_y)), abs(max(all_y)), 0.5)
        self._axes.set_ylim(-y_max_abs * 1.1, y_max_abs * 1.1)

        self._axes.text(0.95, 0.95, "Q1", transform=self._axes.transAxes,
                        ha="right", va="top", fontsize=10, alpha=0.4)
        self._axes.text(0.05, 0.95, "Q2", transform=self._axes.transAxes,
                        ha="left", va="top", fontsize=10, alpha=0.4)
        self._axes.text(0.05, 0.05, "Q3", transform=self._axes.transAxes,
                        ha="left", va="bottom", fontsize=10, alpha=0.4)
        self._axes.text(0.95, 0.05, "Q4", transform=self._axes.transAxes,
                        ha="right", va="bottom", fontsize=10, alpha=0.4)

        self._axes.text(0.95, -0.08, "Compradores →",
                        transform=self._axes.transAxes, ha="right", va="top",
                        fontsize=9, color="green", fontweight="bold")
        self._axes.text(0.05, -0.08, "← Vendedores",
                        transform=self._axes.transAxes, ha="left", va="top",
                        fontsize=9, color="red", fontweight="bold")

    def _attach_annot(self: "QuadrantChart") -> None:
        """Recria a anotação de hover após a limpeza dos eixos."""
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "yellow", "ec": "gray", "alpha": 0.8},
            fontsize=9, visible=False,
        )

    def _generate_summary(self: "QuadrantChart",
                          trajectories: list[list[dict]]) -> str:
        """Gera o resumo textual da distribuição entre os quadrantes."""
        return generate_summary(trajectories)

    def _on_pick(self: "QuadrantChart", event: PickEvent) -> None:
        """Exibe a tooltip do ativo selecionado com o cursor."""
        if not hasattr(event, "ind") or not event.ind:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return
        idx = event.ind[0]
        if idx >= len(self._hover_data):
            return
        pt = self._hover_data[idx]
        self._show_tooltip(pt, event.mouseevent.xdata, event.mouseevent.ydata)

    def _on_motion(self: "QuadrantChart", event: MouseEvent) -> None:
        """Atualiza a tooltip conforme o ativo mais próximo do cursor."""
        if event.inaxes != self._axes or not self._scatter:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return
        contains, _info = self._scatter.contains(event)
        if contains:
            return
        closest = None
        min_dist = 0.08
        for pt in self._hover_data:
            dx = event.xdata - pt["clv"]
            dy = event.ydata - pt["vwap_dist"]
            dist = math.sqrt(dx**2 + dy**2)
            if dist < min_dist:
                min_dist = dist
                closest = pt
        if closest:
            self._show_tooltip(closest, event.xdata, event.ydata)
        else:
            self._annot.set_visible(False)
            self._canvas.draw_idle()

    def _show_tooltip(self: "QuadrantChart", pt: dict, x: float, y: float) -> None:
        """Preenche a anotação com os dados do ponto sob o cursor."""
        vol_str = (
            str(pt["fin_instr_qty"])
            if pt["fin_instr_qty"] < 1e6
            else f"{pt['fin_instr_qty'] / 1e6:.1f}M"
        )
        self._annot.set_text(
            f"{pt['ticker']}\n"
            f"Data: {pt['date']}\n"
            f"CLV: {pt['clv']:+.2f}\n"
            f"VWAP: {pt['vwap_dist']:+.2f}%\n"
            f"Qtd: {vol_str}"
        )
        self._annot.xy = (x, y)
        self._annot.set_visible(True)
        self._canvas.draw_idle()

    def reset(self: "QuadrantChart") -> None:
        """Limpa o gráfico e exibe o estado vazio."""
        self._show_empty()

    def get_figure(self: "QuadrantChart") -> Figure:
        """Retorna a figura matplotlib utilizada pelo gráfico."""
        return self._figure
