"""Gráfico de evolução da dominância de um ativo ao longo do tempo.

A classe DominanceTimelineChart apresenta o histórico de CLV de um
ativo selecionado, com barras diárias e hastes proporcionais ao fluxo
monetário de cada pregão.
"""

import tkinter as tk
from collections.abc import Callable

from matplotlib.backend_bases import MouseEvent, PickEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.domain.strategies.classifiers import (
    classify_conviction,
    classify_dominance,
)
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
from flowscope.presentation.gui.charts.timeline_data import (
    build_rows,
    direction_balance,
)
from flowscope.presentation.gui.charts.toolbar import ToolbarBR


class DominanceTimelineChart:
    """Exibe a linha do tempo da dominância de um ativo ao longo dos pregões."""

    def __init__(
        self: "DominanceTimelineChart",
        parent: tk.Widget,
        *,
        copy_chart_callback: Callable[[Figure], None] | None = None,
    ) -> None:
        """Cria o gráfico de evolução da dominância com sua toolbar.

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
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "yellow", "ec": "gray", "alpha": 0.8},
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("pick_event", self._on_pick)
        self._canvas.mpl_connect("motion_notify_event", self._on_motion)

    def update(self: "DominanceTimelineChart", data: dict,
               ticker: str | None = None) -> None:
        """Atualiza a linha do tempo de dominância do ativo selecionado."""
        self._hover_data.clear()
        self._bars = None

        if not data or not ticker or ticker not in data:
            self._show_empty()
            return

        hide_empty(self._empty_label)
        self._axes.clear()

        rows = build_rows(data[ticker])
        if not rows:
            self._show_empty()
            return

        self._plot_rows(rows, ticker)
        self._figure.tight_layout()
        self._attach_annot()
        self._canvas.draw()

    def _show_empty(self: "DominanceTimelineChart") -> None:
        """Limpa os eixos e exibe o rótulo de estado vazio."""
        show_empty(self._figure, self._all_axes, self._empty_label)
        self._canvas.draw()

    def _plot_rows(self: "DominanceTimelineChart",
                   rows: list[dict], ticker: str) -> None:
        """Desenha as barras, hastes e rótulos da linha do tempo."""
        y_pos = list(range(len(rows)))
        clvs = [r["clv"] for r in rows]
        dmfs = [r["daily_mfv"] for r in rows]
        labels = [str(r["date"]) for r in rows]

        self._axes.axvline(x=0, color="gray", linestyle="-", linewidth=0.8, zorder=1)

        self._bars = self._axes.barh(
            y_pos, clvs, height=0.6, color=bar_colors(clvs),
            zorder=3, picker=True,
        )

        max_dmf = max(abs(d) for d in dmfs) if dmfs else 1.0
        draw_stems(self._axes, dmfs, clvs, y_pos, max_dmf, scale=0.15)

        self._hover_data = rows

        self._axes.set_yticks(y_pos)
        self._axes.set_yticklabels(labels, fontsize=7)
        self._axes.set_xlabel("CLV", fontsize=9)
        self._axes.set_title(f"Evolução da Dominância — {ticker}", fontsize=10)
        self._axes.set_xlim(-1.2, 1.2)
        self._axes.set_ylim(-0.5, len(rows) - 0.5)

        self._annotate_balance(rows)

    def _annotate_balance(self: "DominanceTimelineChart",
                          rows: list[dict]) -> None:
        """Exibe o percentual de dias compradores e vendedores."""
        buyer_days, seller_days = direction_balance(rows)
        total_dir = buyer_days + seller_days
        buyer_pct = (buyer_days / total_dir * 100) if total_dir else 0
        seller_pct = (seller_days / total_dir * 100) if total_dir else 0

        self._axes.text(0.95, -0.10, f"Compradores {buyer_pct:.0f}% →",
                        transform=self._axes.transAxes, ha="right", va="top",
                        fontsize=8, color="green", fontweight="bold")
        self._axes.text(0.05, -0.10, f"← Vendedores {seller_pct:.0f}%",
                        transform=self._axes.transAxes, ha="left", va="top",
                        fontsize=8, color="red", fontweight="bold")

    def _attach_annot(self: "DominanceTimelineChart") -> None:
        """Recria a anotação de hover após a limpeza dos eixos."""
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "yellow", "ec": "gray", "alpha": 0.8},
            fontsize=9, visible=False, zorder=10,
        )

    def _on_pick(self: "DominanceTimelineChart", event: PickEvent) -> None:
        """Exibe a tooltip do pregão selecionado com o cursor."""
        if not hasattr(event, "ind") or not event.ind:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return
        idx = event.ind[0]
        if idx >= len(self._hover_data):
            return
        pt = self._hover_data[idx]
        self._show_tooltip(pt, event.mouseevent.xdata, event.mouseevent.ydata)

    def _on_motion(self: "DominanceTimelineChart", event: MouseEvent) -> None:
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

    def _show_tooltip(self: "DominanceTimelineChart", pt: dict, x: float,
                      y: float) -> None:
        """Preenche a anotação com os dados do pregão sob o cursor."""
        dom_cls = classify_dominance(pt["clv"])
        conv_cls = classify_conviction(pt["efficiency"])
        dmf_str = f"R$ {pt['daily_mfv']:,.0f}" if pt["daily_mfv"] != 0 else "N/A"
        self._annot.set_text(
            f"Data: {pt['date']}\n"
            f"Dominância: {dom_cls.label} (CLV: {pt['clv']:+.2f})\n"
            f"Convicção: {conv_cls.label} (Efic: {pt['efficiency']*100:.1f}%)\n"
            f"MFV do pregão: {dmf_str}"
        )
        self._annot.xy = (x, y)
        self._annot.set_visible(True)
        self._canvas.draw_idle()

    def reset(self: "DominanceTimelineChart") -> None:
        """Limpa o gráfico e exibe o estado vazio."""
        self._show_empty()

    def get_figure(self: "DominanceTimelineChart") -> Figure:
        """Retorna a figura matplotlib utilizada pelo gráfico."""
        return self._figure
