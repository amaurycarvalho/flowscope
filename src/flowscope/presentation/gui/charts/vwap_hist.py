from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class VWAPHistChart:
    def __init__(self, parent):
        self.frame = parent
        self._figure = Figure(figsize=(5, 3), dpi=100)
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=parent)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    def update(self, data: dict) -> None:
        self._axes.clear()
        if not data:
            self._axes.set_title("VWAP por Ticker")
            self._canvas.draw()
            return

        tickers = []
        vwaps = []
        for ticker, info in data.items():
            vwap_data = info.get("vwap")
            if vwap_data:
                tickers.append(ticker)
                vwaps.append(float(vwap_data["period_vwap"]))

        if tickers:
            self._axes.bar(tickers, vwaps, color="steelblue")
            self._axes.set_title("VWAP por Ticker")
            self._axes.set_ylabel("Preço (R$)")
            self._axes.tick_params(axis="x", rotation=45)
            self._figure.tight_layout()
        else:
            self._axes.set_title("VWAP por Ticker")
        self._canvas.draw()

    def get_figure(self):
        return self._figure
