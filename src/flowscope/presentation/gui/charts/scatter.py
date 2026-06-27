import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.presentation.gui.charts.toolbar import ToolbarBR


class ScatterChart:
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 5), dpi=100)
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._toolbar = ToolbarBR(self._canvas, self.frame)

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
        self._hover_tickers: list[str] = []
        self._hover_x: list[float] = []
        self._hover_y: list[float] = []
        self._hover_sizes: list[float] = []
        self._scatter = None
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("motion_notify_event", self._on_hover)

    def update(self, data: dict) -> None:
        self._current_data = data
        self._axes.clear()
        self._scatter = None
        self._hover_tickers.clear()
        self._hover_x.clear()
        self._hover_y.clear()
        self._hover_sizes.clear()
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
            vol = float(vwap_data.get("total_fin_instr_qty", 1))
            tickers.append(ticker)
            x_vals.append(x)
            y_vals.append(y)
            sizes.append(max(20, vol / 1e6))
            colors.append("blue" if y >= 0 else "red")

        self._hover_tickers = tickers
        self._hover_x = x_vals
        self._hover_y = y_vals
        self._hover_sizes = sizes

        if tickers:
            self._scatter = self._axes.scatter(x_vals, y_vals, s=sizes, c=colors, alpha=0.6)
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
            self._scatter = None
            self._axes.set_title("VWAP × CVD")

        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )

        self._quiver_artists.clear()
        if self._show_quiver.get():
            self._draw_quiver(data)
        self._canvas.draw()

    def _on_hover(self, event):
        if event.inaxes != self._axes:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return
        if not self._scatter or not self._hover_tickers:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return

        contains, info = self._scatter.contains(event)
        if contains:
            ind = info["ind"][0]
            self._annot.xy = (self._hover_x[ind], self._hover_y[ind])
            vol_str = f"{self._hover_sizes[ind]:.1f}" if self._hover_sizes[ind] < 1000 else f"{self._hover_sizes[ind] / 1000:.1f}M"
            self._annot.set_text(
                f"{self._hover_tickers[ind]}\n"
                f"VWAP: R$ {self._hover_x[ind]:.2f}\n"
                f"CVD: R$ {self._hover_y[ind]:+.2f}\n"
                f"Vol: {vol_str}"
            )
            self._annot.set_visible(True)
            self._canvas.draw_idle()
        else:
            self._annot.set_visible(False)
            self._canvas.draw_idle()

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
