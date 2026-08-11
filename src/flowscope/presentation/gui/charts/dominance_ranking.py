"""Gráfico de dominância do pregão ordenado por ativo.

A classe DominanceRankingChart apresenta o ranking dos ativos segundo
o último CLV, com barras coloridas e hastes proporcionais ao fluxo
monetário de cada um.
"""

import tkinter as tk
from collections.abc import Callable

from matplotlib.backend_bases import MouseEvent, PickEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.domain.strategies.classifiers import classify_dominance
from flowscope.presentation.gui.charts.dominance_data import (
    bar_colors,
    draw_stems,
    find_closest_row,
)
from flowscope.presentation.gui.charts.empty_state import (
    create_empty,
    hide_empty,
    show_empty,
)
from flowscope.presentation.gui.charts.ranking_data import (
    build_rows,
    draw_ticker_labels,
    stem_lengths,
)
from flowscope.presentation.gui.charts.toolbar import ToolbarBR


class DominanceRankingChart:
    """Exibe o ranking de dominância do pregão para todos os ativos."""

    def __init__(
        self: "DominanceRankingChart",
        parent: tk.Widget,
        *,
        copy_chart_callback: Callable[[Figure], None] | None = None,
    ) -> None:
        """Cria o gráfico de ranking de dominância com sua toolbar.

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

        self._hover_data: list[dict] = []
        self._bars = None
        self._circles = None
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "yellow", "ec": "gray", "alpha": 0.8},
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("pick_event", self._on_pick)
        self._canvas.mpl_connect("motion_notify_event", self._on_motion)

    def update(self: "DominanceRankingChart", data: dict) -> None:
        """Atualiza o ranking de dominância com os dados do pregão."""
        self._hover_data.clear()
        self._bars = None
        self._circles = None

        if not data:
            self._show_empty()
            return

        hide_empty(self._empty_label)
        self._axes.clear()

        rows = build_rows(data)
        if not rows:
            self._show_empty()
            return

        self._plot_rows(rows)
        self._figure.tight_layout()
        self._attach_annot()
        self._canvas.draw()

    def _show_empty(self: "DominanceRankingChart") -> None:
        """Limpa os eixos e exibe o rótulo de estado vazio."""
        show_empty(self._figure, self._all_axes, self._empty_label)
        self._canvas.draw()

    def _plot_rows(self: "DominanceRankingChart", rows: list[dict]) -> None:
        """Desenha as barras, hastes e rótulos do ranking de dominância."""
        rows.sort(key=lambda r: r["clv"])
        tickers = [r["ticker"] for r in rows]
        clvs = [r["clv"] for r in rows]
        mfvs = [r["mfv"] for r in rows]
        y_pos = list(range(len(rows)))

        self._axes.axvline(x=0, color="gray", linestyle="-", linewidth=0.8, zorder=1)

        self._bars = self._axes.barh(
            y_pos, clvs, height=0.6, color=bar_colors(clvs), zorder=3, picker=True,
        )

        max_mfv = max(abs(v) for v in mfvs) if mfvs else 0.0
        stem_lens = stem_lengths(mfvs, max_mfv)
        draw_ticker_labels(self._axes, tickers, clvs, stem_lens, y_pos)
        draw_stems(self._axes, mfvs, clvs, y_pos, max_mfv)

        self._hover_data = rows

        self._axes.set_yticks(y_pos)
        self._axes.set_yticklabels([])
        self._axes.set_xlabel("CLV")
        self._axes.set_title("Dominância do Pregão")
        self._axes.set_xlim(-1.2, 1.2)
        self._axes.set_ylim(-0.5, len(rows) - 0.5)

        self._axes.text(0.95, -0.08, "Compradores →",
                        transform=self._axes.transAxes, ha="right", va="top",
                        fontsize=9, color="green", fontweight="bold")
        self._axes.text(0.05, -0.08, "← Vendedores",
                        transform=self._axes.transAxes, ha="left", va="top",
                        fontsize=9, color="red", fontweight="bold")

    def _attach_annot(self: "DominanceRankingChart") -> None:
        """Recria a anotação de hover após a limpeza dos eixos."""
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "yellow", "ec": "gray", "alpha": 0.8},
            fontsize=9, visible=False, zorder=10,
        )

    def _on_pick(self: "DominanceRankingChart", event: PickEvent) -> None:
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

    def _on_motion(self: "DominanceRankingChart", event: MouseEvent) -> None:
        """Atualiza a tooltip conforme a barra mais próxima do cursor."""
        if event.inaxes != self._axes:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return
        if self._bars is None:
            return
        closest = find_closest_row(self._hover_data, event.xdata, event.ydata)
        if closest:
            self._show_tooltip(closest, event.xdata, event.ydata)
        else:
            self._annot.set_visible(False)
            self._canvas.draw_idle()

    def _show_tooltip(self: "DominanceRankingChart", pt: dict, x: float,
                      y: float) -> None:
        """Preenche a anotação com os dados do ativo sob o cursor."""
        cls = classify_dominance(pt["clv"])
        mfv_str = f"R$ {pt['mfv']:,.0f}" if pt["mfv"] != 0 else "N/A"
        self._annot.set_text(
            f"{pt['ticker']}\n"
            f"CLV: {pt['clv']:+.2f}\n"
            f"Dominância: {cls.label}\n"
            f"MFV: {mfv_str}\n"
            f"Data: {pt['date']}"
        )
        self._annot.xy = (x, y)
        self._annot.set_visible(True)
        self._canvas.draw_idle()

    def reset(self: "DominanceRankingChart") -> None:
        """Limpa o gráfico e exibe o estado vazio."""
        self._show_empty()

    def get_figure(self: "DominanceRankingChart") -> Figure:
        """Retorna a figura matplotlib utilizada pelo gráfico."""
        return self._figure
