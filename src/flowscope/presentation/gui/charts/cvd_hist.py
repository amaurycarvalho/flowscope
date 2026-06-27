import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class CVDHistChart:
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 3), dpi=100)
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    def update(self, data: dict) -> None:
        self._axes.clear()
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
        else:
            self._axes.set_title("CVD por Ticker")
        self._canvas.draw()

    def get_figure(self):
        return self._figure
