import tkinter as tk
from collections import defaultdict

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.presentation.gui.charts.toolbar import ToolbarBR
from flowscope.presentation.gui.charts.empty_state import create_empty, show_empty, hide_empty


class VWAPHistChart:
    def __init__(self, parent, *, copy_chart_callback=None):
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 3), dpi=100)
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        self._toolbar = ToolbarBR(self._canvas, self.frame, copy_chart_callback=copy_chart_callback)

        self._all_axes = [self._axes]
        self._empty_label = create_empty(self._figure, self._all_axes)

        self._hover_tickers: list[str] = []
        self._hover_vwaps: list[float] = []
        self._hover_buckets: list[list[tuple[float, float]]] = []
        self._hover_last_pct: list[float] = []
        self._violin_polygons: list[tuple[int, object]] = []
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("motion_notify_event", self._on_hover)

    @staticmethod
    def _to_pct(price: float, vwap: float) -> float:
        return (price - vwap) / vwap * 100

    def _collect_ticker_data(self, data):
        tickers = []
        violin_data = []
        vwap_values_abs = []
        min_prices_pct = []
        max_prices_pct = []
        last_prices_pct = []

        for ticker, info in data.items():
            daily = info.get("daily_data", [])
            if not daily:
                continue

            vwap_info = info.get("vwap", {})
            vwap_abs = float(vwap_info.get("period_vwap", 0))
            if vwap_abs == 0:
                continue

            tickers.append(ticker)
            vwap_values_abs.append(vwap_abs)

            prices_pct = [self._to_pct(float(d["avg_price"]), vwap_abs) for d in daily]
            qtys = [d["fin_instr_qty"] for d in daily]
            violin_data.append((prices_pct, qtys))

            min_prices_pct.append(
                self._to_pct(float(min(d["min_price"] for d in daily)), vwap_abs)
            )
            max_prices_pct.append(
                self._to_pct(float(max(d["max_price"] for d in daily)), vwap_abs)
            )

            last_day = max(daily, key=lambda d: d["date"])
            last_prices_pct.append(self._to_pct(float(last_day["last_price"]), vwap_abs))

        return tickers, violin_data, vwap_values_abs, min_prices_pct, max_prices_pct, last_prices_pct

    def _compute_violin_shapes(self, violin_data):
        bucket_size = self._estimate_bucket_size(violin_data)
        max_vol = 1
        violin_shapes = []

        for prices_pct, qtys in violin_data:
            buckets = defaultdict(float)
            for p, q in zip(prices_pct, qtys):
                bucket = round(p / bucket_size) * bucket_size
                buckets[bucket] += q
            sorted_buckets = sorted(buckets.items())
            y_vals = [b[0] for b in sorted_buckets]
            vol_vals = [b[1] for b in sorted_buckets]
            if vol_vals:
                max_vol = max(max_vol, max(vol_vals))
            violin_shapes.append((y_vals, vol_vals))

        return violin_shapes, max_vol, bucket_size

    def update(self, data: dict) -> None:
        self._hover_tickers.clear()
        self._hover_vwaps.clear()
        self._hover_buckets.clear()
        self._hover_last_pct.clear()
        self._violin_polygons.clear()
        if not data:
            show_empty(self._figure, self._all_axes, self._empty_label)
            self._canvas.draw()
            return

        hide_empty(self._empty_label)
        self._axes.clear()

        (tickers, violin_data, vwap_values_abs, min_prices_pct,
         max_prices_pct, last_prices_pct) = self._collect_ticker_data(data)

        if not tickers:
            show_empty(self._figure, self._all_axes, self._empty_label)
            self._canvas.draw()
            return

        x_positions = list(range(len(tickers)))
        violin_shapes, max_vol, bucket_size = self._compute_violin_shapes(violin_data)

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
        self._hover_vwaps = vwap_values_abs
        self._hover_buckets = [[(y, v) for y, v in zip(ys, vs)] for ys, vs in violin_shapes]
        self._hover_last_pct = last_prices_pct

        self._axes.axhline(y=0, color="gray", linestyle="--", linewidth=0.8, zorder=1)

        self._axes.vlines(
            x_positions, min_prices_pct, max_prices_pct,
            colors="black", linewidth=1.5, zorder=4,
        )

        self._axes.scatter(
            x_positions, [0] * len(tickers),
            color="black", marker="o", s=40, zorder=5,
        )

        self._axes.scatter(
            x_positions, last_prices_pct,
            color="red", marker="D", s=40, zorder=6, label="Último preço",
        )

        self._axes.set_xticks(x_positions)
        self._axes.set_xticklabels(tickers, rotation=45)
        self._axes.set_title("VWAP — Distribuição de Preços")
        self._axes.set_ylabel("Diferença do VWAP (%)")
        self._axes.legend(loc="best")

        all_y = []
        for y_vals, _ in violin_shapes:
            all_y.extend(y_vals)
        all_y.extend(min_prices_pct)
        all_y.extend(max_prices_pct)
        all_y.extend(last_prices_pct)
        if all_y:
            max_abs = max(abs(min(all_y)), abs(max(all_y)))
            self._axes.set_ylim(-max_abs * 1.1, max_abs * 1.1)

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
                vwap_abs = self._hover_vwaps[idx]
                buckets = self._hover_buckets[idx]
                if buckets:
                    prices_pct = [b[0] for b in buckets]
                    vols = [b[1] for b in buckets]
                    min_pct = min(prices_pct)
                    max_pct = max(prices_pct)
                    total_vol = sum(vols)
                    vol_str = f"{total_vol:.0f}" if total_vol < 1e6 else f"{total_vol / 1e6:.1f}M"
                    last_pct = self._hover_last_pct[idx]
                    self._annot.set_text(
                        f"{ticker}\n"
                        f"VWAP: R$ {vwap_abs:.2f}\n"
                        f"Δ Máx: {max_pct:+.2f}% / Δ Mín: {min_pct:+.2f}%\n"
                        f"LastPric: {last_pct:+.2f}%\n"
                        f"Volume: {vol_str}"
                    )
                else:
                    self._annot.set_text(f"{ticker}\nVWAP: R$ {vwap_abs:.2f}")
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
            return 0.01
        price_range = max(all_prices) - min(all_prices)
        if price_range <= 0.5:
            return 0.01
        elif price_range <= 2:
            return 0.05
        elif price_range <= 10:
            return 0.25
        else:
            return 0.50

    def reset(self):
        show_empty(self._figure, self._all_axes, self._empty_label)
        self._canvas.draw()

    def get_figure(self):
        return self._figure
