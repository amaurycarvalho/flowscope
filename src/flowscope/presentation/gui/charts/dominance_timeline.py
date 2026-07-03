import math
import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.domain.strategies.classifiers import (
    classify_dominance,
    classify_conviction,
)
from flowscope.presentation.gui.charts.toolbar import ToolbarBR
from flowscope.presentation.gui.charts.empty_state import create_empty, show_empty, hide_empty


class DominanceTimelineChart:
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
        self._annot = self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("pick_event", self._on_pick)
        self._canvas.mpl_connect("motion_notify_event", self._on_motion)

    def update(self, data: dict, ticker: str | None = None) -> None:
        self._hover_data.clear()
        self._bars = None

        if not data or not ticker or ticker not in data:
            show_empty(self._figure, self._all_axes, self._empty_label)
            self._canvas.draw()
            return

        hide_empty(self._empty_label)
        self._axes.clear()

        info = data[ticker]
        all_inds = info.get("all_indicators", {})
        clv_dict = all_inds.get("clv") or {}
        eff_dict = all_inds.get("daily_efficiency") or {}
        dmf_dict = all_inds.get("daily_money_flow") or {}

        common_dates = sorted(
            d for d in clv_dict
            if clv_dict[d] is not None
        )
        if not common_dates:
            show_empty(self._figure, self._all_axes, self._empty_label)
            self._canvas.draw()
            return

        rows = []
        for dt in reversed(common_dates):
            clv = float(clv_dict[dt])
            eff = float(eff_dict.get(dt) or 0)
            dmf = float(dmf_dict.get(dt) or 0)
            rows.append({
                "date": dt,
                "clv": clv,
                "efficiency": eff,
                "daily_mfv": dmf,
            })

        y_pos = list(range(len(rows)))
        clvs = [r["clv"] for r in rows]
        dmfs = [r["daily_mfv"] for r in rows]
        labels = [str(r["date"]) for r in rows]

        bar_colors = []
        for clv in clvs:
            cls = classify_dominance(clv)
            bar_colors.append(cls.color)

        self._axes.axvline(x=0, color="gray", linestyle="-", linewidth=0.8, zorder=1)

        self._bars = self._axes.barh(
            y_pos, clvs, height=0.6, color=bar_colors,
            zorder=3, picker=True,
        )

        max_dmf = max(abs(d) for d in dmfs) if dmfs else 1.0
        stem_ys, stem_xmins, stem_xmaxs, stem_colors = [], [], [], []
        for i, (clv, dmf) in enumerate(zip(clvs, dmfs)):
            if dmf == 0.0 or abs(clv) < 0.05:
                continue
            norm = abs(dmf) / max_dmf if max_dmf > 0 else 0
            stem_len = max(math.sqrt(norm) * 0.15, 0.015)
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
        self._axes.set_yticklabels(labels, fontsize=7)
        self._axes.set_xlabel("CLV", fontsize=9)
        self._axes.set_title(f"Evolução da Dominância — {ticker}", fontsize=10)
        self._axes.set_xlim(-1.2, 1.2)
        self._axes.set_ylim(-0.5, len(rows) - 0.5)

        buyer_days = sum(1 for r in rows if r["clv"] > 0)
        seller_days = sum(1 for r in rows if r["clv"] < 0)
        total_dir = buyer_days + seller_days
        buyer_pct = (buyer_days / total_dir * 100) if total_dir else 0
        seller_pct = (seller_days / total_dir * 100) if total_dir else 0

        self._axes.text(0.95, -0.10, f"Compradores {buyer_pct:.0f}% →",
                        transform=self._axes.transAxes, ha="right", va="top",
                        fontsize=8, color="green", fontweight="bold")
        self._axes.text(0.05, -0.10, f"← Vendedores {seller_pct:.0f}%",
                        transform=self._axes.transAxes, ha="left", va="top",
                        fontsize=8, color="red", fontweight="bold")

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
        dom_cls = classify_dominance(pt["clv"])
        conv_cls = classify_conviction(pt["efficiency"])
        dmf_str = f"R$ {pt['daily_mfv']:,.0f}" if pt["daily_mfv"] != 0 else "N/A"
        self._annot.set_text(
            f"Data: {pt['date']}\n"
            f"Dominância: {dom_cls.label} (CLV: {pt['clv']:+.2f})\n"
            f"Convicção: {conv_cls.label} (Efic: {pt['efficiency']*100:.1f}%)\n"
            f"MFV do pregão: {dmf_str}"
        )
        self._annot.xy = (x, y)
        self._annot.set_visible(True)
        self._canvas.draw_idle()

    def reset(self):
        show_empty(self._figure, self._all_axes, self._empty_label)
        self._canvas.draw()

    def get_figure(self):
        return self._figure
