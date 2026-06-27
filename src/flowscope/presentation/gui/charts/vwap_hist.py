import tkinter as tk
from collections import defaultdict

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.presentation.gui.charts.toolbar import ToolbarBR


class VWAPHistChart:
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 3), dpi=100)
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        self._toolbar = ToolbarBR(self._canvas, self.frame)

        self._hover_tickers: list[str] = []
        self._hover_vwaps: list[float] = []
        self._hover_buckets: list[list[tuple[float, float]]] = []
        self._violin_polygons: list[tuple[int, object]] = []
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("motion_notify_event", self._on_hover)

    def update(self, data: dict) -> None:
        self._axes.clear()
        self._hover_tickers.clear()
        self._hover_vwaps.clear()
        self._hover_buckets.clear()
        self._violin_polygons.clear()
        if not data:
            self._axes.set_title("VWAP — Distribuição de Preços")
            self._canvas.draw()
            return

        tickers = []
        violin_data = []
        vwap_values = []
        min_prices = []
        max_prices = []
        last_prices = []

        for ticker, info in data.items():
            daily = info.get("daily_data", [])
            if not daily:
                continue
            tickers.append(ticker)

            prices = [float(d["avg_price"]) for d in daily]
            qtys = [d["fin_instr_qty"] for d in daily]
            violin_data.append((prices, qtys))

            vwap_info = info.get("vwap", {})
            vwap_values.append(float(vwap_info.get("period_vwap", 0)))

            min_prices.append(float(min(d["min_price"] for d in daily)))
            max_prices.append(float(max(d["max_price"] for d in daily)))

            last_day = max(daily, key=lambda d: d["date"])
            last_prices.append(float(last_day["last_price"]))

        if not tickers:
            self._axes.set_title("VWAP — Distribuição de Preços")
            self._canvas.draw()
            return

        x_positions = list(range(len(tickers)))
        bucket_size = self._estimate_bucket_size(violin_data)
        max_vol = 1
        violin_shapes = []

        for prices, qtys in violin_data:
            buckets = defaultdict(float)
            for p, q in zip(prices, qtys):
                bucket = round(p / bucket_size) * bucket_size
                buckets[bucket] += q
            sorted_buckets = sorted(buckets.items())
            y_vals = [b[0] for b in sorted_buckets]
            vol_vals = [b[1] for b in sorted_buckets]
            if vol_vals:
                max_vol = max(max_vol, max(vol_vals))
            violin_shapes.append((y_vals, vol_vals))

        violin_width = 0.35
        for idx, (y_vals, vol_vals) in enumerate(violin_shapes):
            if not vol_vals:
                continue
            norm_vol = [v / max_vol * violin_width for v in vol_vals]
            norm_vol = [max(w, 0.02) for w in norm_vol]
            x_pos = x_positions[idx]
            x_left = [x_pos - w for w in norm_vol]
            x_right = [x_pos + w for w in reversed(norm_vol)]
            y_v = list(y_vals) + list(reversed(y_vals))
            x_v = x_left + x_right
            fills = self._axes.fill(
                x_v, y_v, alpha=0.3, color="steelblue",
                edgecolor="steelblue", linewidth=0.5,
            )
            if fills:
                self._violin_polygons.append((idx, fills[0]))

        self._hover_tickers = tickers
        self._hover_vwaps = vwap_values
        self._hover_buckets = [[(y, v) for y, v in zip(ys, vs)] for ys, vs in violin_shapes]

        yerr_lower = [v - mp for v, mp in zip(vwap_values, min_prices)]
        yerr_upper = [mx - v for v, mx in zip(vwap_values, max_prices)]
        self._axes.errorbar(
            x_positions, vwap_values,
            yerr=[yerr_lower, yerr_upper],
            fmt="o", color="black", capsize=4, capthick=1.5, markersize=6,
            zorder=5,
        )

        self._axes.scatter(
            x_positions, last_prices,
            color="red", marker="D", s=40, zorder=6, label="Último preço",
        )

        self._axes.set_xticks(x_positions)
        self._axes.set_xticklabels(tickers, rotation=45)
        self._axes.set_title("VWAP — Distribuição de Preços")
        self._axes.set_ylabel("Preço (R$)")
        self._axes.legend(loc="best")
        self._figure.tight_layout()

        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )
        self._canvas.draw()

    def _on_hover(self, event):
        if event.inaxes != self._axes or not self._violin_polygons:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return

        for idx, poly in self._violin_polygons:
            if poly.contains(event)[0]:
                ticker = self._hover_tickers[idx]
                vwap = self._hover_vwaps[idx]
                buckets = self._hover_buckets[idx]
                if buckets:
                    prices = [b[0] for b in buckets]
                    vols = [b[1] for b in buckets]
                    price_range = f"R$ {min(prices):.2f} — R$ {max(prices):.2f}"
                    total_vol = sum(vols)
                    vol_str = f"{total_vol:.0f}" if total_vol < 1e6 else f"{total_vol / 1e6:.1f}M"
                    self._annot.set_text(
                        f"{ticker}\n"
                        f"VWAP: R$ {vwap:.2f}\n"
                        f"Faixa: {price_range}\n"
                        f"Volume: {vol_str}"
                    )
                else:
                    self._annot.set_text(f"{ticker}\nVWAP: R$ {vwap:.2f}")
                self._annot.xy = (event.xdata, event.ydata)
                self._annot.set_visible(True)
                self._canvas.draw_idle()
                return

        self._annot.set_visible(False)
        self._canvas.draw_idle()

    def _estimate_bucket_size(self, violin_data):
        all_prices = []
        for prices, _ in violin_data:
            all_prices.extend(prices)
        if not all_prices:
            return 0.10
        price_range = max(all_prices) - min(all_prices)
        if price_range <= 1:
            return 0.01
        elif price_range <= 10:
            return 0.10
        elif price_range <= 100:
            return 1.0
        else:
            return 10.0

    def get_figure(self):
        return self._figure
