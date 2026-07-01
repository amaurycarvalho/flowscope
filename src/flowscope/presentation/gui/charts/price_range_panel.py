import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.presentation.gui.charts.toolbar import ToolbarBR


class PriceRangePanel:
    def __init__(self, parent, *, copy_chart_callback=None):
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 4), dpi=100)
        self._gs = self._figure.add_gridspec(
            nrows=4, ncols=1, height_ratios=[3, 1, 0.5, 0.5],
            hspace=0.15,
        )
        self._ax_timeline = self._figure.add_subplot(self._gs[0])
        self._ax_range_history = self._figure.add_subplot(self._gs[1])
        self._ax_efficiency = self._figure.add_subplot(self._gs[2])
        self._ax_clv = self._figure.add_subplot(self._gs[3])

        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._toolbar = ToolbarBR(
            self._canvas, self.frame, copy_chart_callback=copy_chart_callback,
        )

        self._hover_data: list[dict] = []
        self._annot = self._ax_timeline.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("motion_notify_event", self._on_motion)

    def update(self, data: dict, ticker: str | None = None) -> None:
        for ax in [self._ax_timeline, self._ax_range_history,
                   self._ax_efficiency, self._ax_clv]:
            ax.clear()
        self._hover_data.clear()

        if not data or not ticker or ticker not in data:
            self._ax_timeline.set_title("Amplitude de Preço")
            self._ax_timeline.set_xlim(-0.05, 1.05)
            self._canvas.draw()
            return

        info = data[ticker]
        daily = info.get("daily_data", [])
        if not daily:
            self._ax_timeline.set_title(f"Amplitude de Preço — {ticker}")
            self._ax_timeline.set_xlim(-0.05, 1.05)
            self._canvas.draw()
            return

        all_inds = info.get("all_indicators", {})

        daily_sorted = sorted(daily, key=lambda x: x["date"])

        typical_dict = all_inds.get("typical_price") or {}
        median_dict = all_inds.get("median_price") or {}
        weighted_dict = all_inds.get("weighted_close") or {}
        range_pct_dict = all_inds.get("range_percentual") or {}
        clv_dict = all_inds.get("clv") or {}
        eff_dict = all_inds.get("daily_efficiency") or {}

        self._build_timeline(daily_sorted, typical_dict, median_dict,
                             weighted_dict, range_pct_dict, eff_dict)
        self._build_range_history(daily_sorted, range_pct_dict)
        self._build_efficiency_gauge(daily_sorted, eff_dict)
        self._build_clv_gauge(daily_sorted, clv_dict)

        self._attach_annot()
        self._figure.tight_layout()
        self._canvas.draw()

    def _attach_annot(self):
        self._annot = self._ax_timeline.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False, zorder=10,
        )

    @staticmethod
    def _normalize(price, min_p, max_p):
        rng = max_p - min_p
        if rng == 0:
            return 0.5
        return (price - min_p) / rng

    def _build_timeline(self, daily, typical_dict, median_dict,
                        weighted_dict, range_pct_dict, eff_dict):
        ax = self._ax_timeline
        n = len(daily)
        rev_daily = list(reversed(daily))
        today_range_text = None

        for i, d in enumerate(rev_daily):
            dt = d["date"]
            min_p = float(d["min_price"])
            max_p = float(d["max_price"])
            close = float(d["last_price"])
            avg_p = float(d["avg_price"])

            norm_close = self._normalize(close, min_p, max_p)
            norm_avg = self._normalize(avg_p, min_p, max_p)

            ax.plot([0, 1], [i, i], color="#CCCCCC", linewidth=3, zorder=1)

            is_last = (i == 0)

            if is_last:
                today_range_text = f"Min: {min_p:.2f}  Max: {max_p:.2f}"

                ax.scatter(norm_close, i, marker="o", color="blue", s=60,
                           zorder=5, label="Close")

                typical = typical_dict.get(dt)
                median = median_dict.get(dt)
                weighted = weighted_dict.get(dt)

                if median is not None:
                    norm_m = self._normalize(float(median), min_p, max_p)
                    ax.scatter(norm_m, i, marker="s", color="orange", s=50,
                               zorder=5)
                    ax.annotate("M", (norm_m, i),
                                xytext=(4, 4), textcoords="offset points",
                                fontsize=8, color="orange", fontweight="bold")

                if typical is not None:
                    norm_t = self._normalize(float(typical), min_p, max_p)
                    ax.scatter(norm_t, i, marker="^", color="green", s=50,
                               zorder=5)
                    ax.annotate("T", (norm_t, i),
                                xytext=(4, 4), textcoords="offset points",
                                fontsize=8, color="green", fontweight="bold")

                ax.scatter(norm_avg, i, marker="D", color="purple", s=50,
                           zorder=5)
                ax.annotate("V", (norm_avg, i),
                            xytext=(4, 4), textcoords="offset points",
                            fontsize=8, color="purple", fontweight="bold")

                if weighted is not None:
                    norm_w = self._normalize(float(weighted), min_p, max_p)
                    ax.scatter(norm_w, i, marker="v", color="brown", s=50,
                               zorder=5)
                    ax.annotate("W", (norm_w, i),
                                xytext=(4, 4), textcoords="offset points",
                                fontsize=8, color="brown", fontweight="bold")

                self._hover_data.append({
                    "date": dt,
                    "close": close,
                    "typical": typical,
                    "median": median,
                    "vwap": avg_p,
                    "weighted": weighted,
                    "min_p": min_p,
                    "max_p": max_p,
                })
            else:
                ax.scatter(norm_close, i, marker="o", color="blue", s=30,
                           alpha=0.35, zorder=3)
                self._hover_data.append({
                    "date": dt,
                    "close": close,
                    "min_p": min_p,
                    "max_p": max_p,
                })

        if n >= 2:
            for i in range(n - 1):
                curr = rev_daily[i]
                next_d = rev_daily[i + 1]

                curr_close = float(curr["last_price"])
                next_close = float(next_d["last_price"])
                curr_min = float(curr["min_price"])
                curr_max = float(curr["max_price"])
                next_min = float(next_d["min_price"])
                next_max = float(next_d["max_price"])

                x0 = self._normalize(curr_close, curr_min, curr_max)
                x1 = self._normalize(next_close, next_min, next_max)
                y0 = i
                y1 = i + 1

                ax.arrow(x0, y0, x1 - x0, y1 - y0,
                         head_width=0.25, head_length=0.02,
                         fc="gray", ec="gray", alpha=0.3,
                         length_includes_head=True, zorder=2)

        classification = self._get_classification(
            daily, range_pct_dict, eff_dict
        )
        if classification:
            ax.text(0.98, 0.98, classification,
                    transform=ax.transAxes, ha="right", va="top",
                    fontsize=10, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow",
                              ec="gray", alpha=0.9),
                    zorder=10)

        ax.set_yticks(range(n))
        ax.set_yticklabels([str(d["date"]) for d in rev_daily], fontsize=8)
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(-0.5, n - 0.5)
        ax.set_xlabel("Faixa de Preço Normalizada (%)", fontsize=8)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=7)
        ax.set_title("Price Range Timeline", fontsize=10)

        if today_range_text:
            ax.text(0.5, -0.05, today_range_text, transform=ax.transAxes,
                    ha="center", va="top", fontsize=7, color="gray")

    def _get_classification(self, daily, range_pct_dict, eff_dict):
        if not daily or not range_pct_dict or not eff_dict:
            return None

        range_pct_values = [
            float(v) for v in range_pct_dict.values() if v is not None
        ]
        if not range_pct_values:
            return None

        sorted_vals = sorted(range_pct_values)
        n_vals = len(sorted_vals)
        if n_vals % 2 == 0:
            median_rp = (sorted_vals[n_vals // 2 - 1]
                         + sorted_vals[n_vals // 2]) / 2
        else:
            median_rp = sorted_vals[n_vals // 2]

        last_date = daily[-1]["date"]
        current_rp = range_pct_dict.get(last_date)
        current_eff = eff_dict.get(last_date)

        if current_rp is None or current_eff is None:
            return None

        current_rp = float(current_rp)
        current_eff = float(current_eff)

        if current_rp <= median_rp and current_eff <= 0.30:
            return "Pregão Lateral"
        elif current_rp > median_rp and current_eff <= 0.30:
            return "Volatilidade sem Direção"
        elif current_rp <= median_rp and current_eff > 0.30:
            return "Movimento Consistente"
        else:
            return "Movimento Direcional Forte"

    def _build_range_history(self, daily, range_pct_dict):
        ax = self._ax_range_history

        dates = [d["date"] for d in daily]
        values = [
            float(range_pct_dict.get(d["date"], 0) or 0)
            for d in daily
        ]

        if not values or all(v == 0 for v in values):
            ax.set_title("Range % Histórico", fontsize=9)
            return

        ax.plot(dates, values, marker="o", color="steelblue",
                linewidth=1.5, markersize=4, zorder=3)

        if len(values) > 0:
            ax.scatter(dates[-1], values[-1], color="red", s=50,
                       zorder=5, marker="o", edgecolors="darkred",
                       linewidth=1)

        ax.set_title("Range % Histórico", fontsize=9)
        ax.set_ylabel("Range %", fontsize=8)
        ax.tick_params(axis="x", labelsize=7)
        ax.tick_params(axis="y", labelsize=7)
        ax.grid(True, alpha=0.3)

    def _build_efficiency_gauge(self, daily, eff_dict):
        ax = self._ax_efficiency

        last_date = daily[-1]["date"] if daily else None
        eff = float(eff_dict.get(last_date, 0) or 0) if last_date else 0

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        ax.barh(0.5, 1, height=0.35, color="#EEEEEE", zorder=1)

        if eff <= 0.30:
            color = "#CC6666"
        elif eff <= 0.60:
            color = "#CCAA44"
        else:
            color = "#44AA66"

        ax.barh(0.5, eff, height=0.35, color=color, zorder=2)

        ax.text(eff / 2, 0.5, f"{eff*100:.0f}%",
                ha="center", va="center", fontsize=9, fontweight="bold",
                color="white" if eff > 0.3 else "black")

        ax.set_title("Eficiência Diária", fontsize=9, loc="left")
        ax.set_yticks([])
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=7)

    def _build_clv_gauge(self, daily, clv_dict):
        ax = self._ax_clv

        last_date = daily[-1]["date"] if daily else None
        clv = float(clv_dict.get(last_date, 0) or 0) if last_date else 0

        ax.set_xlim(-1, 1)
        ax.set_ylim(0, 1)

        ax.barh(0.5, 2, height=0.35, color="#EEEEEE", zorder=1, left=-1)

        if clv > 0:
            ax.barh(0.5, clv, height=0.35, color="#44AA66", zorder=2, left=0)
        elif clv < 0:
            ax.barh(0.5, abs(clv), height=0.35, color="#CC4444",
                    zorder=2, left=clv)

        ax.axvline(x=0, color="gray", linewidth=0.8, linestyle="-", zorder=3)

        clv_pct = clv * 100
        if clv != 0:
            clv_text = f"{clv:+.2f} ({clv_pct:+.0f}%)"
        else:
            clv_text = "0.00"
        ax.text(clv / 2 if clv != 0 else 0, 0.5, clv_text,
                ha="center", va="center", fontsize=9, fontweight="bold",
                color="white" if abs(clv) > 0.15 else "black")

        ax.set_title("CLV", fontsize=9, loc="left")
        ax.set_yticks([])
        ax.set_xticks([-1, -0.5, 0, 0.5, 1])
        ax.set_xticklabels(["-100%", "-50%", "0%", "50%", "100%"], fontsize=7)

    def _on_motion(self, event):
        if event.inaxes != self._ax_timeline or not self._hover_data:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return

        closest = None
        min_dist = 0.3
        for i, pt in enumerate(self._hover_data):
            dy = abs(event.ydata - i)
            if dy < min_dist:
                min_dist = dy
                closest = pt

        if closest:
            self._show_tooltip(closest, event.xdata, event.ydata)
        else:
            self._annot.set_visible(False)
            self._canvas.draw_idle()

    def _show_tooltip(self, pt, x, y):
        lines = [f"Data: {pt['date']}"]
        lines.append(f"Close: {pt['close']:.2f}")
        lines.append(f"Min: {pt['min_p']:.2f}  Max: {pt['max_p']:.2f}")
        if "typical" in pt and pt["typical"] is not None:
            lines.append(f"Typical: {float(pt['typical']):.2f}")
        if "median" in pt and pt["median"] is not None:
            lines.append(f"Median: {float(pt['median']):.2f}")
        if "vwap" in pt:
            lines.append(f"VWAP: {float(pt['vwap']):.2f}")
        if "weighted" in pt and pt["weighted"] is not None:
            lines.append(f"W. Close: {float(pt['weighted']):.2f}")

        self._annot.set_text("\n".join(lines))
        self._annot.xy = (x, y)
        self._annot.set_visible(True)
        self._canvas.draw_idle()

    def get_figure(self):
        return self._figure
