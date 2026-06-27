import tkinter as tk
from datetime import date
from tkcalendar import DateEntry

from flowscope.application.use_cases import AnalyzeTickersUseCase
from flowscope.infrastructure.b3.client import B3Client
from flowscope.infrastructure.b3.repository import B3DataRepository
from flowscope.presentation.gui.charts.cvd_hist import CVDHistChart
from flowscope.presentation.gui.charts.scatter import ScatterChart
from flowscope.presentation.gui.charts.vwap_hist import VWAPHistChart
from flowscope.presentation.gui.widgets.analysis_text import AnalysisText
from flowscope.presentation.gui.widgets.ticker_list import TickerList


class FlowScopeGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FlowScope")
        self.minsize(1024, 768)

        self._repo = B3DataRepository(B3Client())
        self._use_case = AnalyzeTickersUseCase(self._repo)
        self._current_data: dict = {}
        self._tickers: list[str] = []

        self._build_top_bar()
        self._build_main_area()
        self._build_action_buttons()

        self._on_date_change()

    def _build_top_bar(self):
        top = tk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        tk.Label(top, text="Data de referência:").pack(side=tk.LEFT)
        self._date_entry = DateEntry(
            top,
            date_pattern="yyyy-MM-dd",
            maxdate=date.today(),
        )
        self._date_entry.pack(side=tk.LEFT, padx=5)
        self._date_entry.bind("<<DateEntrySelected>>", lambda e: self._on_date_change())

    def _build_main_area(self):
        main = tk.Frame(self)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        charts_frame = tk.Frame(main)
        charts_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        top_charts = tk.Frame(charts_frame)
        top_charts.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        left_charts = tk.Frame(top_charts)
        left_charts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._vwap_chart = VWAPHistChart(left_charts)
        self._vwap_chart.frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._cvd_chart = CVDHistChart(left_charts)
        self._cvd_chart.frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self._scatter_chart = ScatterChart(top_charts)
        self._scatter_chart.frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(main)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        self._ticker_list = TickerList(sidebar, on_change=self._on_ticker_edit)
        self._ticker_list.frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._analysis_text = AnalysisText(sidebar)
        self._analysis_text.frame.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_action_buttons(self):
        bottom = tk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        tk.Button(bottom, text="Copiar Dados", command=self._copy_data).pack(side=tk.LEFT, padx=2)
        tk.Button(bottom, text="Copiar Gráfico", command=self._copy_chart).pack(side=tk.LEFT, padx=2)

    def _on_ticker_edit(self):
        self._update_charts()

    def _on_date_change(self):
        ref_date = self._date_entry.get_date()
        self._current_data = self._use_case.execute(ref_date, self._tickers or None)
        self._tickers = list(self._current_data.keys())
        self._ticker_list.set_tickers(self._tickers)
        self._update_charts()

    def _update_charts(self):
        import matplotlib
        matplotlib.use("TkAgg")

        tickers = self._ticker_list.get_tickers()
        filtered = {t: self._current_data.get(t) for t in tickers if t in self._current_data}
        self._vwap_chart.update(filtered)
        self._cvd_chart.update(filtered)
        self._scatter_chart.update(filtered)

    def _copy_data(self):
        try:
            import pyxclip
            import pyxclip.main as pyxclip_main
            lines = ["Ticker;VWAP;CVD"]
            for ticker, data in self._current_data.items():
                vwap = data.get("vwap", {}).get("period_vwap", "")
                cvd = data.get("cvd", {}).get("accumulated_cvd", "")
                lines.append(f"{ticker};{vwap};{cvd}")
            text = "\n".join(lines)
            pyxclip_main.copy(text)
        except Exception:
            self._fallback_clipboard_text()

    def _fallback_clipboard_text(self):
        self.clipboard_clear()
        lines = ["Ticker;VWAP;CVD"]
        for ticker, data in self._current_data.items():
            vwap = data.get("vwap", {}).get("period_vwap", "")
            cvd = data.get("cvd", {}).get("accumulated_cvd", "")
            lines.append(f"{ticker};{vwap};{cvd}")
        self.clipboard_append("\n".join(lines))

    def _copy_chart(self):
        from flowscope.infrastructure.clipboard_image import copy_image_to_clipboard
        figure = self._scatter_chart.get_figure()
        if figure is not None:
            copy_image_to_clipboard(figure)
