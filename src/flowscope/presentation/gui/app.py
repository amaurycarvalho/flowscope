import platform
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

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        w = int(screen_w * 0.8)
        h = int(screen_h * 0.8)
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(w, h)
        self.resizable(True, True)
        if platform.system() == "Linux":
            self.wm_attributes("-type", "normal")

        self._repo = B3DataRepository(B3Client())
        self._use_case = AnalyzeTickersUseCase(self._repo)
        self._current_data: dict = {}
        self._tickers: list[str] = []

        self._build_top_bar()
        self._build_main_area()
        self._build_statusbar()
        self._build_action_buttons()

        self._set_status("Pronto. Selecione uma data e clique em Carregar.")

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
        tk.Button(top, text="Carregar", command=self._on_load_data).pack(side=tk.LEFT, padx=5)

    def _build_main_area(self):
        main = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=6)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        left_pw = tk.PanedWindow(main, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=6)
        main.add(left_pw, stretch="always")

        selector_frame = tk.Frame(left_pw)
        left_pw.add(selector_frame, stretch="never")
        self._chart_var = tk.StringVar(value="vwap")
        for text, value in [("VWAP", "vwap"), ("CVD", "cvd"), ("Dispersão", "scatter")]:
            rb = tk.Radiobutton(selector_frame, text=text, variable=self._chart_var,
                                value=value, command=self._on_chart_select)
            rb.pack(side=tk.LEFT, padx=4)

        self._chart_container = tk.Frame(left_pw)
        left_pw.add(self._chart_container, stretch="always")

        self._vwap_chart = VWAPHistChart(self._chart_container)
        self._cvd_chart = CVDHistChart(self._chart_container)
        self._scatter_chart = ScatterChart(self._chart_container)
        self._show_current_chart()

        right_pw = tk.PanedWindow(main, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=6)
        main.add(right_pw, stretch="never")

        ticker_frame = tk.Frame(right_pw)
        right_pw.add(ticker_frame, stretch="always")
        self._ticker_list = TickerList(ticker_frame, on_change=self._on_ticker_edit)
        self._ticker_list.frame.pack(fill=tk.BOTH, expand=True)

        analysis_frame = tk.Frame(right_pw)
        right_pw.add(analysis_frame, stretch="never")
        self._analysis_text = AnalysisText(analysis_frame)
        self._analysis_text.frame.pack(fill=tk.X)

    def _build_action_buttons(self):
        bottom = tk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        tk.Button(bottom, text="Copiar Dados", command=self._copy_data).pack(side=tk.LEFT, padx=2)
        tk.Button(bottom, text="Copiar Gráfico", command=self._copy_chart).pack(side=tk.LEFT, padx=2)

    def _build_statusbar(self):
        self._status_var = tk.StringVar()
        bar = tk.Label(self, textvariable=self._status_var, relief=tk.SUNKEN,
                       anchor=tk.W, padx=5, pady=2)
        bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _set_status(self, msg: str) -> None:
        self._status_var.set(msg)

    def _on_load_data(self):
        self._set_status("Carregando dados...")
        self.update_idletasks()
        ref_date = self._date_entry.get_date()
        try:
            self._current_data = self._use_case.execute(ref_date, self._tickers or None)
            self._tickers = list(self._current_data.keys())
            self._ticker_list.set_tickers(self._tickers)
            self._update_charts()
            n = len(self._tickers)
            self._set_status(f"{n} ticker{'s' if n != 1 else ''} carregado{'s' if n != 1 else ''} para {ref_date}.")
        except Exception as e:
            self._set_status(f"Erro ao carregar dados: {e}")

    def _on_chart_select(self):
        self._show_current_chart()

    def _show_current_chart(self):
        for c in (self._vwap_chart, self._cvd_chart, self._scatter_chart):
            c.frame.pack_forget()
        selected = self._chart_var.get()
        {
            "vwap": self._vwap_chart,
            "cvd": self._cvd_chart,
            "scatter": self._scatter_chart,
        }[selected].frame.pack(fill=tk.BOTH, expand=True)

    def _on_ticker_edit(self):
        self._update_charts()
        self._set_status("Filtro aplicado!")

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
        self._show_current_chart()

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
            self._set_status("Dados CSV copiados para a área de transferência.")
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
        self._set_status("Dados CSV copiados para a área de transferência (fallback).")

    def _copy_chart(self):
        from flowscope.infrastructure.clipboard_image import (
            ClipboardError,
            copy_image_to_clipboard,
        )
        chart = {
            "vwap": self._vwap_chart,
            "cvd": self._cvd_chart,
            "scatter": self._scatter_chart,
        }[self._chart_var.get()]
        figure = chart.get_figure()
        if figure is not None:
            try:
                copy_image_to_clipboard(figure)
                self._set_status("Gráfico copiado para a área de transferência.")
            except ClipboardError as e:
                self._set_status(f"Erro: {e}")
