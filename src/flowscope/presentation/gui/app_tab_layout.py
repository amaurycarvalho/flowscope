"""Construção das abas e restauração do estado do layout da interface."""

import tkinter as tk
from tkinter import ttk

from flowscope.presentation.gui.app_tabs import ENABLED_TABS, TAB_CONFIGS
from flowscope.presentation.gui.charts.dominance_ranking import DominanceRankingChart
from flowscope.presentation.gui.charts.dominance_timeline import DominanceTimelineChart
from flowscope.presentation.gui.charts.financial_flow_panel import FinancialFlowPanel
from flowscope.presentation.gui.charts.price_range_panel import PriceRangePanel
from flowscope.presentation.gui.charts.quadrant_chart import QuadrantChart
from flowscope.presentation.gui.charts.vwap_hist import VWAPHistChart


class TabsLayoutMixin:
    """Constrói as abas de análise e restaura o estado dos separadores."""

    def _build_general_tabs(self: "TabsLayoutMixin") -> None:
        general_vwap_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_vwap_frame, text="VWAP")
        self._vwap_chart = VWAPHistChart(general_vwap_frame, copy_chart_callback=self._copy_chart)
        self._vwap_chart.frame.pack(fill=tk.BOTH, expand=True)

        general_quadrantes_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_quadrantes_frame, text="Quadrantes")
        self._quadrant_chart = QuadrantChart(
            general_quadrantes_frame,
            copy_chart_callback=self._copy_chart,
            summary_callback=self._on_quadrant_summary,
        )
        self._quadrant_chart.frame.pack(fill=tk.BOTH, expand=True)

        general_dominance_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_dominance_frame, text="Dominância do Pregão")
        self._dominance_ranking = DominanceRankingChart(
            general_dominance_frame, copy_chart_callback=self._copy_chart,
        )
        self._dominance_ranking.frame.pack(fill=tk.BOTH, expand=True)

    def _build_ticker_tabs(self: "TabsLayoutMixin") -> None:
        ticker_main_frame = ttk.Frame(self._main_notebook)
        self._main_notebook.add(ticker_main_frame, text="Análise do Ticker")

        self._ticker_notebook = ttk.Notebook(ticker_main_frame)
        self._ticker_notebook.pack(fill=tk.BOTH, expand=True)

        self._ticker_indicator_frames = {}
        for name, *keys in TAB_CONFIGS:
            frame = ttk.Frame(self._ticker_notebook)
            kwargs = {"text": name}
            if name not in ENABLED_TABS:
                kwargs["state"] = "disabled"
            self._ticker_notebook.add(frame, **kwargs)
            if name == "Evolução da Dominância":
                self._dominance_timeline = DominanceTimelineChart(
                    frame, copy_chart_callback=self._copy_chart,
                )
                self._dominance_timeline.frame.pack(fill=tk.BOTH, expand=True)
                self._ticker_indicator_frames[name] = {"frame": frame, "text": None, "keys": keys}
            elif name == "Amplitude de Preço":
                self._price_range_panel = PriceRangePanel(
                    frame, copy_chart_callback=self._copy_chart,
                )
                self._price_range_panel.frame.pack(fill=tk.BOTH, expand=True)
                self._ticker_indicator_frames[name] = {"frame": frame, "text": None, "keys": keys}
            elif name == "Fluxo Financeiro":
                self._financial_flow_panel = FinancialFlowPanel(
                    frame, copy_chart_callback=self._copy_chart,
                    summary_callback=self._on_flow_summary,
                )
                self._financial_flow_panel.frame.pack(fill=tk.BOTH, expand=True)
                self._ticker_indicator_frames[name] = {"frame": frame, "text": None, "keys": keys}
            else:
                text_widget = tk.Text(frame, wrap=tk.WORD, font=("TkDefaultFont", 11),
                                      padx=8, pady=8, relief=tk.FLAT, state=tk.DISABLED)
                text_widget.pack(fill=tk.BOTH, expand=True)
                self._ticker_indicator_frames[name] = {"frame": frame, "text": text_widget, "keys": keys}

    def _restore_tabs(self: "TabsLayoutMixin", last_tab: str, last_subtab: str) -> None:
        try:
            for i in range(self._main_notebook.index("end")):
                if self._main_notebook.tab(i, "text") == last_tab:
                    self._main_notebook.select(i)
                    break
            notebook = self._general_notebook if last_tab == "Análise Geral" else self._ticker_notebook
            for i in range(notebook.index("end")):
                if notebook.tab(i, "text") == last_subtab:
                    notebook.select(i)
                    break
        except tk.TclError:
            pass
        self._on_tab_changed()

    def _restore_sashes(self: "TabsLayoutMixin", positions: list[int]) -> None:
        try:
            if len(positions) >= 2:
                self._main_pw.sash_place(0, positions[0], 0)
            if len(positions) >= 4 and hasattr(self, "_left_pw"):
                self._left_pw.sash_place(0, 0, positions[1])
        except tk.TclError:
            pass
