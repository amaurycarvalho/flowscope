import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.presentation.gui.charts.toolbar import ToolbarBR


class CVDHistChart:
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 3), dpi=100)
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        self._toolbar = ToolbarBR(self._canvas, self.frame)

        self._hover_tickers: list[str] = []
        self._hover_cvds: list[float] = []
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("motion_notify_event", self._on_hover)

    def update(self, data: dict) -> None:
        self._axes.clear()
        self._hover_tickers.clear()
        self._hover_cvds.clear()
        if not data:
            self._axes.set_title("CVD por Ticker")
            self._canvas.draw()
            return

        tickers = []
        cvds = []
        for ticker, info in data.items():
            cvd_data = info.get("cvd")
            if cvd_data:
                tickers.append(ticker)
                cvds.append(cvd_data["accumulated_cvd"])

        if tickers:
            colors = ["green" if v >= 0 else "red" for v in cvds]
            self._axes.bar(tickers, cvds, color=colors)
            self._axes.set_title("CVD por Ticker")
            self._axes.set_ylabel("Delta de Volume (R$)")
            self._axes.tick_params(axis="x", rotation=45)
            self._figure.tight_layout()
            self._hover_tickers = tickers
            self._hover_cvds = cvds
        else:
            self._axes.set_title("CVD por Ticker")

        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )
        self._canvas.draw()

    def _on_hover(self, event):
        if event.inaxes != self._axes or not self._hover_tickers:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return

        for i, patch in enumerate(self._axes.patches):
            if patch.contains(event)[0]:
                self._annot.xy = (patch.get_x() + patch.get_width() / 2, patch.get_y() + patch.get_height())
                self._annot.set_text(
                    f"{self._hover_tickers[i]}\nCVD: R$ {self._hover_cvds[i]:+.2f}"
                )
                self._annot.set_visible(True)
                self._canvas.draw_idle()
                return

        self._annot.set_visible(False)
        self._canvas.draw_idle()

    def get_figure(self):
        return self._figure
