import tkinter as tk
import warnings

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from flowscope.domain.strategies.classifiers import classify_money_flow
from flowscope.presentation.gui.charts.toolbar import ToolbarBR


class FinancialFlowPanel:
    def __init__(self, parent, *, copy_chart_callback=None, summary_callback=None):
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(5, 4), dpi=100)
        self._gs = self._figure.add_gridspec(
            nrows=2, ncols=1, height_ratios=[3, 2],
            hspace=0.3,
        )
        self._ax_gauge = self._figure.add_subplot(self._gs[0])
        self._ax_bs = self._figure.add_subplot(self._gs[1])

        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._toolbar = ToolbarBR(
            self._canvas, self.frame, copy_chart_callback=copy_chart_callback,
        )

        self._summary_callback = summary_callback
        self._hover_data: list[dict] = []
        self._annot = self._ax_gauge.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="gray", alpha=0.8),
            fontsize=9, visible=False,
        )
        self._canvas.mpl_connect("motion_notify_event", self._on_motion)

    def update(self, data: dict, ticker: str | None = None) -> None:
        for ax in [self._ax_gauge, self._ax_bs]:
            ax.clear()
        self._hover_data.clear()

        if not data or not ticker or ticker not in data:
            self._ax_gauge.set_title("Fluxo Financeiro")
            self._ax_gauge.set_xlim(-1, 1)
            self._ax_bs.set_xlim(0, 1)
            self._canvas.draw()
            return

        info = data[ticker]
        daily = info.get("daily_data", [])
        if not daily:
            self._ax_gauge.set_title(f"Fluxo Financeiro — {ticker}")
            self._ax_gauge.set_xlim(-1, 1)
            self._ax_bs.set_xlim(0, 1)
            self._canvas.draw()
            return

        all_inds = info.get("all_indicators", {})
        daily_sorted = sorted(daily, key=lambda x: x["date"])
        last = daily_sorted[-1]

        clv_dict = all_inds.get("clv") or {}
        dmf_dict = all_inds.get("daily_money_flow") or {}
        bp_dict = all_inds.get("buying_pressure") or {}
        sp_dict = all_inds.get("selling_pressure") or {}
        rp_dict = all_inds.get("range_percentual") or {}
        accumulated_mfv = info.get("money_flow_volume")

        last_date = last["date"]
        clv = float(clv_dict.get(last_date, 0) or 0) if last_date else 0
        dmf = float(dmf_dict.get(last_date, 0) or 0) if last_date else 0
        bp = float(bp_dict.get(last_date, 0) or 0) if last_date else 0
        sp = float(sp_dict.get(last_date, 0) or 0) if last_date else 0
        rp = float(rp_dict.get(last_date, 0) or 0) if last_date else 0
        fin_vol = float(last.get("fin_vol", 0) or 0)

        score = clv

        classification = classify_money_flow(score)

        n_days = len(daily_sorted)
        mfv_text = ""
        if accumulated_mfv is not None:
            mfv_text = f"Acum. {n_days}d: R${float(accumulated_mfv):+,.0f}"

        fin_vol_millions = fin_vol / 1_000_000

        self._build_gauge(clv, dmf, score, classification, mfv_text, rp,
                          last_date, ticker, fin_vol_millions)
        self._build_bs_bar(bp, sp)

        self._hover_data.append({
            "date": last_date,
            "dmf": dmf,
            "clv": clv,
            "score": score,
            "classification": classification.label,
            "fin_vol": fin_vol,
            "mfv_acum": float(accumulated_mfv) if accumulated_mfv else None,
            "range_pct": rp,
        })

        if self._summary_callback:
            summary = self._generate_summary(dmf, score, classification, clv, bp)
            self._summary_callback(summary)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self._figure.tight_layout()
        self._canvas.draw()

    def _build_gauge(self, clv, dmf, score, classification, mfv_text, rp,
                     last_date, ticker, fin_vol_millions):
        ax = self._ax_gauge
        ax.clear()

        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(0, 1)

        ax.axhline(y=0.5, xmin=0, xmax=1, color="#E0E0E0", linewidth=2, zorder=1)

        bar_height = 0.35
        bar_y = 0.5 - bar_height / 2

        if dmf > 0:
            ax.barh(0.5, abs(clv), height=bar_height, color="#4CAF50",
                    zorder=2, left=0, alpha=0.85)
            ax.barh(0.5, 1, height=bar_height, color="#E8F5E9",
                    zorder=1, left=0, alpha=0.3)
        elif dmf < 0:
            ax.barh(0.5, abs(clv), height=bar_height, color="#EF5350",
                    zorder=2, left=clv, alpha=0.85)
            ax.barh(0.5, 1, height=bar_height, color="#FFEBEE",
                    zorder=1, left=-1, alpha=0.3)
        else:
            ax.barh(0.5, 1, height=bar_height, color="#F5F5F5",
                    zorder=1, left=-1)

        ax.axvline(x=0, color="#9E9E9E", linewidth=1, linestyle="-", zorder=3)

        ax.plot(clv, 0.5, marker="v", color="#333333", markersize=10,
                zorder=5, clip_on=False)
        ax.plot(clv, 0.5, marker="v", color="white", markersize=6,
                zorder=6, clip_on=False)

        unit = "M"
        dmf_display = abs(dmf) / 1_000_000
        if abs(dmf) >= 1e9:
            dmf_display = abs(dmf) / 1e9
            unit = "Bi"
        if dmf != 0:
            dmf_label = f"{dmf:+.2f}  (R${dmf_display:+,.1f}{unit})"
        else:
            dmf_label = "R$ 0,00"
        ax.text(0, 0.88, dmf_label, ha="center", va="bottom", fontsize=11,
                fontweight="bold", color="#333333")

        ax.text(-1.15, 0.5, "◄ Vendedor", ha="left", va="center", fontsize=8,
                color="#EF5350", fontweight="bold")
        ax.text(1.15, 0.5, "Comprador ►", ha="right", va="center", fontsize=8,
                color="#4CAF50", fontweight="bold")

        cls_color = classification.color
        cls_label = classification.label
        ax.text(0, 0.12, cls_label, ha="center", va="center", fontsize=10,
                fontweight="bold", color=cls_color,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=cls_color,
                          alpha=0.85))

        if mfv_text:
            ax.text(1.15, 0.12, mfv_text, ha="right", va="center", fontsize=7,
                    color="#666666", style="italic")

        ax.text(-1.15, 0.12, f"Range: {rp:.2f}%", ha="left", va="center",
                fontsize=7, color="#666666", style="italic")

        vol_text = f"Vol. Financeiro: R${fin_vol_millions:+,.1f}M"
        ax.text(-1.15, -0.05, vol_text, ha="left", va="top", fontsize=6,
                color="#999999")

        ax.set_title(f"Fluxo Financeiro — {ticker}", fontsize=10, loc="center",
                     pad=8)
        ax.set_yticks([])
        ax.set_xticks([-1, -0.5, 0, 0.5, 1])
        ax.set_xticklabels(["-100%", "-50%", "0%", "50%", "100%"], fontsize=7)
        ax.set_xlabel("CLV / Score Normalizado", fontsize=7, color="#666666")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

    def _build_bs_bar(self, bp, sp):
        ax = self._ax_bs
        ax.clear()

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        if bp + sp > 0:
            bp_pct = bp / (bp + sp) * 100
            sp_pct = sp / (bp + sp) * 100
        else:
            bp_pct = 50
            sp_pct = 50

        if bp > 0:
            ax.barh(0.5, bp, height=0.35, color="#4CAF50", zorder=2,
                    left=0, alpha=0.85)
        if sp > 0:
            ax.barh(0.5, sp, height=0.35, color="#EF5350", zorder=2,
                    left=bp, alpha=0.85)
        if bp == 0 and sp == 0:
            ax.barh(0.5, 1, height=0.35, color="#E0E0E0", zorder=1, left=0)

        bp_label = f"Compra {bp_pct:.0f}%"
        sp_label = f"Venda {sp_pct:.0f}%"
        if bp > 0.1:
            ax.text(bp / 2, 0.5, bp_label, ha="center", va="center",
                    fontsize=10, fontweight="bold", color="white")
        else:
            ax.text(0.02, 0.5, bp_label, ha="left", va="center",
                    fontsize=10, fontweight="bold", color="#4CAF50")
        if sp > 0.1:
            ax.text(bp + sp / 2, 0.5, sp_label, ha="center", va="center",
                    fontsize=10, fontweight="bold", color="white")
        else:
            ax.text(0.98, 0.5, sp_label, ha="right", va="center",
                    fontsize=10, fontweight="bold", color="#EF5350")

        ax.set_title("Pressão no Range", fontsize=9, loc="left", pad=6)
        ax.set_yticks([])
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

    def _generate_summary(self, dmf, score, classification, clv, bp):
        parts = []
        if dmf > 0:
            if classification.score >= 3:
                parts.append("O ativo fechou com forte fluxo financeiro comprador")
            elif classification.score >= 1:
                parts.append("O ativo fechou com fluxo comprador moderado")
            else:
                parts.append("O ativo fechou com leve fluxo comprador")
        elif dmf < 0:
            if classification.score <= -3:
                parts.append("O ativo fechou com forte fluxo financeiro vendedor")
            elif classification.score <= -1:
                parts.append("O ativo fechou com fluxo vendedor moderado")
            else:
                parts.append("O ativo fechou com leve fluxo vendedor")
        else:
            parts.append("O fluxo financeiro foi neutro")

        if clv > 0.3:
            parts.append("e o fechamento ocorreu próximo da máxima")
        elif clv < -0.3:
            parts.append("e o fechamento ocorreu próximo da mínima")
        else:
            parts.append("e o fechamento ocorreu na região central do range")

        if bp > 0.65:
            parts.append(", com ampla dominância compradora no range.")
        elif sp > 0.65:
            parts.append(", com ampla dominância vendedora no range.")
        else:
            parts.append(", com disputa equilibrada no range.")

        conviction = "elevada" if abs(classification.score) >= 3 else \
                     "moderada" if abs(classification.score) >= 1 else \
                     "baixa"
        parts.append(f" Convicção financeira {conviction}.")

        return "".join(parts)

    def _on_motion(self, event):
        if event.inaxes != self._ax_gauge or not self._hover_data:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return

        self._show_tooltip(self._hover_data[0], event.xdata, event.ydata)

    def _show_tooltip(self, pt, x, y):
        lines = [f"Data: {pt['date']}"]
        lines.append(f"DMF (Daily Money Flow): R${pt['dmf']:+,.2f}")
        if pt["mfv_acum"] is not None:
            lines.append(f"MFV Acumulado: R${pt['mfv_acum']:+,.2f}")
        lines.append(f"CLV: {pt['clv']:+.4f}")
        lines.append(f"Score: {pt['score']:+.4f}")
        lines.append(f"Classificação: {pt['classification']}")
        lines.append(f"Vol. Financeiro: R${pt['fin_vol']:+,.2f}")
        lines.append(f"Range: {pt['range_pct']:.2f}%")

        self._annot.set_text("\n".join(lines))
        self._annot.xy = (x, y)
        self._annot.set_visible(True)
        self._canvas.draw_idle()

    def get_figure(self):
        return self._figure
