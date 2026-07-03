import math
import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.domain.strategies.classifiers import classify_dominance
from flowscope.presentation.gui.charts.toolbar import ToolbarBR
from flowscope.presentation.gui.charts.empty_state import create_empty, show_empty, hide_empty


class DominanceRankingChart:
    def __init__(self, parent, *, copy_chart_callback=None):
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 3), dpi=100)
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._toolbar = ToolbarBR(
            self._canvas, self.frame, copy_chart_callback=copy_chart_callback
        )

        self._all_axes = [self._axes]
        self._empty_label = create_empty(self._figure, self._all_axes)

        self._hover_data: list[dict] = []
        self._bars = None
        self._circles = None
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("pick_event", self._on_pick)
        self._canvas.mpl_connect("motion_notify_event", self._on_motion)

    def update(self, data: dict) -> None:
        self._hover_data.clear()
        self._bars = None
        self._circles = None

        if not data:
            show_empty(self._figure, self._all_axes, self._empty_label)
            self._canvas.draw()
            return

        hide_empty(self._empty_label)
        self._axes.clear()

        rows = []
        max_mfv = 0.0
        for ticker, info in data.items():
            all_inds = info.get("all_indicators", {})
            clv_dict = all_inds.get("clv")
            if not clv_dict:
                continue
            last_date = max(clv_dict.keys())
            clv = clv_dict[last_date]
            if clv is None:
                continue
            clv_f = float(clv)
            mfv = info.get("money_flow_volume")
            mfv_f = float(mfv) if mfv is not None else 0.0
            if abs(mfv_f) > max_mfv:
                max_mfv = abs(mfv_f)
            rows.append({
                "ticker": ticker,
                "clv": clv_f,
                "mfv": mfv_f,
                "date": last_date,
            })

        if not rows:
            show_empty(self._figure, self._all_axes, self._empty_label)
            self._canvas.draw()
            return

        rows.sort(key=lambda r: r["clv"])

        tickers = [r["ticker"] for r in rows]
        clvs = [r["clv"] for r in rows]
        mfvs = [r["mfv"] for r in rows]
        y_pos = list(range(len(rows)))

        bar_colors = []
        for clv in clvs:
            cls = classify_dominance(clv)
            bar_colors.append(cls.color)

        self._axes.axvline(x=0, color="gray", linestyle="-", linewidth=0.8, zorder=1)

        self._bars = self._axes.barh(
            y_pos, clvs, height=0.6, color=bar_colors, zorder=3, picker=True,
        )

        stem_lens = []
        for mfv in mfvs:
            if mfv == 0.0:
                stem_lens.append(0.0)
            else:
                norm = abs(mfv) / max_mfv if max_mfv > 0 else 0
                stem_lens.append(max(math.sqrt(norm) * 0.10, 0.015))

        for i, (ticker, clv) in enumerate(zip(tickers, clvs)):
            stem_len = stem_lens[i]
            if clv >= 0:
                label_x = clv + stem_len + 0.02
                ha = "left"
            else:
                label_x = clv - stem_len - 0.02
                ha = "right"
            if label_x > 1.18:
                label_x = 1.18
                ha = "right"
            elif label_x < -1.18:
                label_x = -1.18
                ha = "left"
            self._axes.text(
                label_x, y_pos[i], ticker,
                ha=ha, va="center", fontsize=8, zorder=4,
            )

        stem_ys, stem_xmins, stem_xmaxs, stem_colors = [], [], [], []
        for i, (clv, mfv) in enumerate(zip(clvs, mfvs)):
            if mfv == 0.0 or abs(clv) < 0.05:
                continue
            stem_len = stem_lens[i]
            cls = classify_dominance(clv)
            stem_ys.append(y_pos[i])
            intensity = abs(cls.score)
            if intensity == 0:
                gray = "#C0C0C0"
            elif intensity == 1:
                gray = "#555555"
            elif intensity == 2:
                gray = "#222222"
            else:
                gray = "#0A0A0A"
            stem_colors.append(gray)
            if clv >= 0:
                stem_xmins.append(0.0)
                stem_xmaxs.append(clv + stem_len)
            else:
                stem_xmins.append(clv - stem_len)
                stem_xmaxs.append(0.0)

        if stem_ys:
            self._axes.hlines(
                stem_ys, stem_xmins, stem_xmaxs,
                colors=stem_colors, linewidth=2, zorder=5,
            )

        self._hover_data = rows

        self._axes.set_yticks(y_pos)
        self._axes.set_yticklabels([])
        self._axes.set_xlabel("CLV")
        self._axes.set_title("Dominância do Pregão")
        self._axes.set_xlim(-1.2, 1.2)
        self._axes.set_ylim(-0.5, len(rows) - 0.5)

        self._axes.text(0.95, -0.08, "Compradores →",
                        transform=self._axes.transAxes, ha="right", va="top",
                        fontsize=9, color="green", fontweight="bold")
        self._axes.text(0.05, -0.08, "← Vendedores",
                        transform=self._axes.transAxes, ha="left", va="top",
                        fontsize=9, color="red", fontweight="bold")

        self._figure.tight_layout()
        self._attach_annot()
        self._canvas.draw()

    def _attach_annot(self):
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False, zorder=10,
        )

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
        if event.inaxes != self._axes:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return
        if self._bars is None:
            return
        closest = None
        min_dist = 0.3
        for pt in self._hover_data:
            idx = self._hover_data.index(pt)
            dy = abs(event.ydata - idx)
            if dy > min_dist:
                continue
            if pt["clv"] >= 0:
                if event.xdata < 0 or event.xdata > pt["clv"]:
                    continue
            else:
                if event.xdata > 0 or event.xdata < pt["clv"]:
                    continue
            if dy < min_dist:
                min_dist = dy
                closest = pt
        if closest:
            self._show_tooltip(closest, event.xdata, event.ydata)
        else:
            self._annot.set_visible(False)
            self._canvas.draw_idle()

    def _show_tooltip(self, pt, x, y):
        cls = classify_dominance(pt["clv"])
        mfv_str = f"R$ {pt['mfv']:,.0f}" if pt["mfv"] != 0 else "N/A"
        self._annot.set_text(
            f"{pt['ticker']}\n"
            f"CLV: {pt['clv']:+.2f}\n"
            f"Dominância: {cls.label}\n"
            f"MFV: {mfv_str}\n"
            f"Data: {pt['date']}"
        )
        self._annot.xy = (x, y)
        self._annot.set_visible(True)
        self._canvas.draw_idle()

    def reset(self):
        show_empty(self._figure, self._all_axes, self._empty_label)
        self._canvas.draw()

    def get_figure(self):
        return self._figure
