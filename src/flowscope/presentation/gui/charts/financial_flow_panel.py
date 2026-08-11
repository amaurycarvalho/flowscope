"""Painel de fluxo financeiro de um ativo no FlowScope."""

import tkinter as tk
import warnings
from collections.abc import Callable

from matplotlib.backend_bases import MouseEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.domain.strategies.classifiers import classify_money_flow
from flowscope.presentation.gui.charts.empty_state import (
    create_empty,
    hide_empty,
    show_empty,
)
from flowscope.presentation.gui.charts.financial_flow_helpers import (
    draw_bs_bar,
    draw_card,
    draw_clv_bar,
    extract_session_metrics,
    format_accumulated_mfv,
    generate_summary,
    tooltip_lines,
)
from flowscope.presentation.gui.charts.toolbar import ToolbarBR


class FinancialFlowPanel:
    """Exibe o fluxo financeiro, o CLV e as pressões de compra e venda."""

    def __init__(
        self: "FinancialFlowPanel",
        parent: tk.Widget,
        *,
        copy_chart_callback: Callable[[Figure], None] | None = None,
        summary_callback: Callable[[str], None] | None = None,
    ) -> None:
        """Cria o painel de fluxo financeiro com seus eixos e toolbar.

        Configura a figura com três subplots (cartão, CLV e pressões), o
        canvas Tkinter, a toolbar e a infraestrutura de hover do painel.
        """
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 4), dpi=100)
        self._gs = self._figure.add_gridspec(
            nrows=3, ncols=1, height_ratios=[3, 2, 3],
            hspace=0.3,
        )
        self._ax_card = self._figure.add_subplot(self._gs[0])
        self._ax_clv = self._figure.add_subplot(self._gs[1])
        self._ax_bs = self._figure.add_subplot(self._gs[2])

        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._toolbar = ToolbarBR(
            self._canvas, self.frame, copy_chart_callback=copy_chart_callback,
        )

        self._all_axes = [self._ax_card, self._ax_clv, self._ax_bs]
        self._empty_label = create_empty(self._figure, self._all_axes)

        self._summary_callback = summary_callback
        self._hover_data: list[dict] = []
        self._annot = self._ax_card.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "yellow", "ec": "gray", "alpha": 0.8},
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("motion_notify_event", self._on_motion)

    def update(self: "FinancialFlowPanel", data: dict,
               ticker: str | None = None) -> None:
        """Atualiza o painel com os dados de fluxo financeiro do ativo.

        Exibe o estado vazio quando não há dados ou ticker válido; caso
        contrário, renderiza o cartão, as barras de CLV e de pressões.
        """
        self._hover_data.clear()

        if not data or not ticker or ticker not in data:
            show_empty(self._figure, self._all_axes, self._empty_label)
            self._canvas.draw()
            return

        hide_empty(self._empty_label)
        for ax in [self._ax_card, self._ax_clv, self._ax_bs]:
            ax.clear()

        info = data[ticker]
        daily = info.get("daily_data", [])
        if not daily:
            show_empty(self._figure, self._all_axes, self._empty_label)
            self._canvas.draw()
            return

        all_inds = info.get("all_indicators", {})
        daily_sorted = sorted(daily, key=lambda x: x["date"])

        metrics = extract_session_metrics(daily_sorted, all_inds, info)
        score = metrics["clv"]

        classification = classify_money_flow(score)
        mfv_value, mfv_millions = format_accumulated_mfv(
            metrics["accumulated_mfv"]
        )

        draw_card(self._ax_card, metrics["dmf"], classification, mfv_value,
                  metrics["rp"], ticker, metrics["fin_vol_millions"],
                  mfv_millions)
        draw_clv_bar(self._ax_clv, metrics["clv"], metrics["dmf"])
        draw_bs_bar(self._ax_bs, metrics["bp"], metrics["sp"])

        self._hover_data.append({
            "date": metrics["last_date"],
            "dmf": metrics["dmf"],
            "clv": metrics["clv"],
            "score": score,
            "classification": classification.label,
            "fin_vol": metrics["fin_vol"],
            "mfv_acum": (
                float(metrics["accumulated_mfv"])
                if metrics["accumulated_mfv"] else None
            ),
            "range_pct": metrics["rp"],
        })

        if self._summary_callback:
            summary = generate_summary(metrics["dmf"], classification,
                                       metrics["clv"], metrics["bp"],
                                       metrics["sp"])
            self._summary_callback(summary)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self._figure.tight_layout()
        self._canvas.draw()

    def _on_motion(self: "FinancialFlowPanel", event: MouseEvent) -> None:
        """Exibe o tooltip do último pregão durante o movimento do mouse."""
        if event.inaxes != self._ax_card or not self._hover_data:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return

        self._show_tooltip(self._hover_data[0], event.xdata, event.ydata)

    def _show_tooltip(self: "FinancialFlowPanel", pt: dict,
                      x: float, y: float) -> None:
        """Posiciona a anotação com as informações do ponto sob o cursor."""
        self._annot.set_text("\n".join(tooltip_lines(pt)))
        self._annot.xy = (x, y)
        self._annot.set_visible(True)
        self._canvas.draw_idle()

    def reset(self: "FinancialFlowPanel") -> None:
        """Limpa o painel e exibe o estado vazio."""
        show_empty(self._figure, self._all_axes, self._empty_label)
        self._canvas.draw()

    def get_figure(self: "FinancialFlowPanel") -> Figure:
        """Retorna a figura matplotlib utilizada pelo painel."""
        return self._figure
