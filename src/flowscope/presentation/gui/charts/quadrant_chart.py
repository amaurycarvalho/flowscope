import math
import tkinter as tk

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.presentation.gui.charts.toolbar import ToolbarBR


class QuadrantChart:
    def __init__(self, parent, *, copy_chart_callback=None, summary_callback=None):
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 3), dpi=100)
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._toolbar = ToolbarBR(
            self._canvas, self.frame, copy_chart_callback=copy_chart_callback
        )

        self._summary_callback = summary_callback
        self._hover_data: list[dict] = []
        self._scatter = None
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("pick_event", self._on_pick)
        self._canvas.mpl_connect("motion_notify_event", self._on_motion)

    def update(self, data: dict) -> None:
        self._axes.clear()
        self._hover_data.clear()
        self._scatter = None

        if not data:
            self._axes.set_title("Quadrantes — CLV vs VWAP Distance")
            self._canvas.draw()
            return

        ticker_trajectories: list[list[dict]] = []

        for ticker, info in data.items():
            daily = info.get("daily_data", [])
            if not daily:
                continue
            clv_by_date = info.get("all_indicators", {}).get("clv") or {}
            vwap_dist_by_date = info.get("all_indicators", {}).get("vwap_distance") or {}

            points = []
            for d in sorted(daily, key=lambda x: x["date"]):
                dt = d["date"]
                clv = clv_by_date.get(dt)
                vd = vwap_dist_by_date.get(dt)
                if clv is None or vd is None:
                    continue
                points.append({
                    "ticker": ticker,
                    "date": dt,
                    "clv": float(clv),
                    "vwap_dist": float(vd) * 100,
                    "fin_instr_qty": d["fin_instr_qty"],
                })

            if points:
                ticker_trajectories.append(points)

        if not ticker_trajectories:
            self._axes.set_title("Quadrantes — CLV vs VWAP Distance")
            self._canvas.draw()
            return

        all_x: list[float] = []
        all_y: list[float] = []

        for points in ticker_trajectories:
            for i in range(len(points) - 1):
                p0, p1 = points[i], points[i + 1]
                self._axes.arrow(
                    p0["clv"], p0["vwap_dist"],
                    p1["clv"] - p0["clv"], p1["vwap_dist"] - p0["vwap_dist"],
                    head_width=0.02, head_length=0.02,
                    fc="gray", ec="gray", alpha=0.3,
                    length_includes_head=True, zorder=2,
                )
            for p in points:
                all_x.append(p["clv"])
                all_y.append(p["vwap_dist"])

        max_qty = max(
            max(p["fin_instr_qty"] for p in pts)
            for pts in ticker_trajectories
        )
        size_scale = 200

        last_x, last_y, last_sizes, last_colors = [], [], [], []
        hover_index = 0
        for points in ticker_trajectories:
            last = points[-1]
            last_x.append(last["clv"])
            last_y.append(last["vwap_dist"])
            norm = math.sqrt(last["fin_instr_qty"] / max_qty) if max_qty > 0 else 0.1
            last_sizes.append(max(norm * size_scale, 10))
            last_colors.append(last["clv"])
            self._hover_data.append(last)

        cmap = matplotlib.colormaps["RdYlGn"]
        self._scatter = self._axes.scatter(
            last_x, last_y, s=last_sizes, c=last_colors, cmap=cmap,
            vmin=-1, vmax=1, edgecolors="black", linewidth=0.5,
            alpha=0.8, zorder=5, picker=True, pickradius=5,
        )

        for pt in self._hover_data:
            self._axes.annotate(
                pt["ticker"],
                xy=(pt["clv"], pt["vwap_dist"]),
                xytext=(5, 5), textcoords="offset points",
                fontsize=7, alpha=0.8,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.5),
            )

        self._axes.axhline(y=0, color="gray", linestyle="--", linewidth=0.8, zorder=1)
        self._axes.axvline(x=0, color="gray", linestyle="--", linewidth=0.8, zorder=1)

        self._axes.set_xlabel("CLV")
        self._axes.set_ylabel("Desvio do VWAP (%)")
        self._axes.set_title("Quadrantes — CLV vs VWAP Distance")

        x_margin = 0.1
        self._axes.set_xlim(-1 - x_margin, 1 + x_margin)

        y_max_abs = max(abs(min(all_y)), abs(max(all_y)), 0.5)
        self._axes.set_ylim(-y_max_abs * 1.1, y_max_abs * 1.1)

        self._axes.text(0.95, 0.95, "Q1", transform=self._axes.transAxes,
                        ha="right", va="top", fontsize=10, alpha=0.4)
        self._axes.text(0.05, 0.95, "Q2", transform=self._axes.transAxes,
                        ha="left", va="top", fontsize=10, alpha=0.4)
        self._axes.text(0.05, 0.05, "Q3", transform=self._axes.transAxes,
                        ha="left", va="bottom", fontsize=10, alpha=0.4)
        self._axes.text(0.95, 0.05, "Q4", transform=self._axes.transAxes,
                        ha="right", va="bottom", fontsize=10, alpha=0.4)

        self._figure.tight_layout()

        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )
        self._canvas.draw()

        if self._summary_callback:
            self._summary_callback(self._generate_summary(ticker_trajectories))

    def _generate_summary(self, trajectories):
        counts = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
        for points in trajectories:
            last = points[-1]
            if last["clv"] > 0 and last["vwap_dist"] > 0:
                counts["Q1"] += 1
            elif last["clv"] < 0 and last["vwap_dist"] > 0:
                counts["Q2"] += 1
            elif last["clv"] < 0 and last["vwap_dist"] < 0:
                counts["Q3"] += 1
            elif last["clv"] > 0 and last["vwap_dist"] < 0:
                counts["Q4"] += 1

        total = sum(counts.values())
        if total == 0:
            return ""

        parts = [
            f"Distribuição: Q1={counts['Q1']}, Q2={counts['Q2']}, "
            f"Q3={counts['Q3']}, Q4={counts['Q4']} (total: {total})"
        ]

        q1 = counts["Q1"] / total
        q3 = counts["Q3"] / total
        q2 = counts["Q2"] / total
        q4 = counts["Q4"] / total

        if q1 > 0.5:
            parts.append(
                "Predominância de ativos com fechamento acima do VWAP e forte "
                "pressão compradora, indicando um pregão amplamente construtivo."
            )
        elif q3 > 0.5:
            parts.append(
                "Maioria dos ativos encerrou abaixo do VWAP com pressão vendedora "
                "dominante, caracterizando um pregão de distribuição."
            )
        elif q2 > 0.4 and q2 > q4:
            parts.append(
                "Apesar de muitos ativos permanecerem acima do VWAP, houve "
                "enfraquecimento no fechamento, sugerindo realização de lucros."
            )
        elif q4 > 0.4 and q4 > q2:
            parts.append(
                "Diversos ativos reagiram no fechamento, mas ainda terminaram "
                "abaixo do VWAP, indicando possível início de recuperação, "
                "ainda sem confirmação."
            )
        else:
            parts.append(
                "Distribuição equilibrada entre os quadrantes, "
                "sem sinal direcional claro."
            )

        return "\n\n".join(parts)

    def _on_pick(self, event):
        if not hasattr(event, "ind") or not event.ind:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return
        idx = event.ind[0]
        if idx >= len(self._hover_data):
            return
        pt = self._hover_data[idx]
        self._show_tooltip(pt, event.mouseevent.xdata, event.mouseevent.ydata)

    def _on_motion(self, event):
        if event.inaxes != self._axes or not self._scatter:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return
        contains, info = self._scatter.contains(event)
        if contains:
            return
        closest = None
        min_dist = 0.08
        for pt in self._hover_data:
            dx = event.xdata - pt["clv"]
            dy = event.ydata - pt["vwap_dist"]
            dist = math.sqrt(dx**2 + dy**2)
            if dist < min_dist:
                min_dist = dist
                closest = pt
        if closest:
            self._show_tooltip(closest, event.xdata, event.ydata)
        else:
            self._annot.set_visible(False)
            self._canvas.draw_idle()

    def _show_tooltip(self, pt, x, y):
        vol_str = (
            str(pt["fin_instr_qty"])
            if pt["fin_instr_qty"] < 1e6
            else f"{pt['fin_instr_qty'] / 1e6:.1f}M"
        )
        self._annot.set_text(
            f"{pt['ticker']}\n"
            f"Data: {pt['date']}\n"
            f"CLV: {pt['clv']:+.2f}\n"
            f"VWAP: {pt['vwap_dist']:+.2f}%\n"
            f"Qtd: {vol_str}"
        )
        self._annot.xy = (x, y)
        self._annot.set_visible(True)
        self._canvas.draw_idle()

    def get_figure(self):
        return self._figure
