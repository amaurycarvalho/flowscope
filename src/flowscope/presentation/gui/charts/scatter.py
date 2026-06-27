import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class ScatterChart:
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 5), dpi=100)
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._show_quiver = tk.BooleanVar(value=False)
        self._quiver_check = tk.Checkbutton(
            self.frame,
            text="Exibir setas temporais",
            variable=self._show_quiver,
            command=self._on_quiver_toggle,
        )
        self._quiver_check.pack(anchor=tk.W)

        self._current_data: dict = {}
        self._quiver_artists = []

    def update(self, data: dict) -> None:
        self._current_data = data
        self._axes.clear()
        if not data:
            self._axes.set_title("VWAP × CVD")
            self._canvas.draw()
            return

        tickers = []
        x_vals = []
        y_vals = []
        sizes = []
        colors = []

        for ticker, info in data.items():
            vwap_data = info.get("vwap")
            cvd_data = info.get("cvd")
            if not vwap_data or not cvd_data:
                continue
            x = float(vwap_data["period_vwap"])
            y = cvd_data["accumulated_cvd"]
            vol = float(vwap_data.get("total_fin_vol", 1))
            tickers.append(ticker)
            x_vals.append(x)
            y_vals.append(y)
            sizes.append(max(20, vol / 1e6))
            colors.append("blue" if y >= 0 else "red")

        if tickers:
            scatter = self._axes.scatter(x_vals, y_vals, s=sizes, c=colors, alpha=0.6)
            for i, ticker in enumerate(tickers):
                self._axes.annotate(
                    ticker,
                    (x_vals[i], y_vals[i]),
                    fontsize=8,
                    ha="center",
                    va="bottom",
                )
            self._axes.set_title("VWAP × CVD")
            self._axes.set_xlabel("VWAP (R$)")
            self._axes.set_ylabel("CVD (R$)")
            self._figure.tight_layout()
        else:
            self._axes.set_title("VWAP × CVD")

        self._quiver_artists.clear()
        if self._show_quiver.get():
            self._draw_quiver(data)
        self._canvas.draw()

    def _on_quiver_toggle(self):
        self.update(self._current_data)

    def _draw_quiver(self, data: dict) -> None:
        import matplotlib.patches as mpatches

        for ticker, info in data.items():
            vwap_data = info.get("vwap")
            cvd_data = info.get("cvd")
            if not vwap_data or not cvd_data:
                continue
            daily_vwap = vwap_data.get("daily_vwap", {})
            daily_cvd = cvd_data.get("daily_cvd", {})
            if len(daily_vwap) < 2:
                continue
            sorted_dates = sorted(daily_vwap.keys())
            d1_date = sorted_dates[-2]
            d0_date = sorted_dates[-1]
            x1 = float(daily_vwap[d1_date])
            y1 = daily_cvd.get(d1_date, 0)
            x2 = float(daily_vwap[d0_date])
            y2 = daily_cvd.get(d0_date, 0)
            arrow = mpatches.FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=15,
                color="gray",
                alpha=0.5,
                linestyle="--",
                linewidth=1,
            )
            self._axes.add_patch(arrow)
            self._quiver_artists.append(arrow)

    def get_figure(self):
        return self._figure
