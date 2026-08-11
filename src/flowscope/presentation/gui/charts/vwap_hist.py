"""Gráfico de distribuição de preços em torno do VWAP para os ativos.

A classe ``VWAPHistChart`` apresenta violinos com a distribuição
percentual de preços em relação ao VWAP, incluindo ferramentas de
inspeção por movimento do mouse e copia da figura para a área de
transferência.
"""

import tkinter as tk
from collections.abc import Callable

from matplotlib.backend_bases import MouseEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.text import Annotation

from flowscope.presentation.gui.charts.empty_state import (
    create_empty,
    hide_empty,
    show_empty,
)
from flowscope.presentation.gui.charts.toolbar import ToolbarBR
from flowscope.presentation.gui.charts.vwap_data import (
    collect_ticker_data,
    compute_violin_shapes,
)


class VWAPHistChart:
    """Exibe violinos com a distribuição percentual de preços em relação ao VWAP."""

    def __init__(
        self: "VWAPHistChart",
        parent: tk.Widget,
        *,
        copy_chart_callback: Callable[[Figure], None] | None = None,
    ) -> None:
        """Cria o gráfico de distribuição de preços com sua toolbar."""
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
        self._annot = self._create_annotation()
        self._canvas.mpl_connect("motion_notify_event", self._on_hover)

    def _create_annotation(self: "VWAPHistChart") -> Annotation:
        """Cria a anotação invisível usada para mostrar o conteúdo sob o mouse."""
        return self._axes.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.3", "fc": "yellow", "ec": "gray", "alpha": 0.8},
            fontsize=9, visible=False,
        )

    def _clear_hover_state(self: "VWAPHistChart") -> None:
        """Limpa o estado de inspeção acumulado na última atualização."""
        self._hover_tickers.clear()
        self._hover_vwaps.clear()
        self._hover_buckets.clear()
        self._hover_last_pct.clear()
        self._violin_polygons.clear()

    def _show_empty(self: "VWAPHistChart") -> None:
        """Exibe o estado vazio e redesenha a tela do gráfico."""
        show_empty(self._figure, self._all_axes, self._empty_label)
        self._canvas.draw()

    def _store_hover_state(
        self: "VWAPHistChart",
        tickers: list[str],
        vwap_values_abs: list[float],
        violin_shapes: list[tuple[list[float], list[float]]],
        last_prices_pct: list[float],
    ) -> None:
        """Armazena os dados necessários para a inspeção por movimento do mouse."""
        self._hover_tickers = tickers
        self._hover_vwaps = vwap_values_abs
        self._hover_buckets = [[(y, v) for y, v in zip(ys, vs)] for ys, vs in violin_shapes]
        self._hover_last_pct = last_prices_pct

    def _draw_violins(
        self: "VWAPHistChart",
        x_positions: list[int],
        violin_shapes: list[tuple[list[float], list[float]]],
        max_vol: float,
        violin_width: float = 0.35,
    ) -> None:
        """Desenha os violinos normalizados pela largura e pelo volume máximo."""
        for idx, (y_vals, vol_vals) in enumerate(violin_shapes):
            if not vol_vals:
                continue
            norm_vol = [max(v / max_vol * violin_width, 0.02) for v in vol_vals]
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

    def _draw_markers(
        self: "VWAPHistChart",
        x_positions: list[int],
        min_prices_pct: list[float],
        max_prices_pct: list[float],
        last_prices_pct: list[float],
    ) -> None:
        """Desenha a linha do zero, os intervalos e os marcadores de último preço."""
        self._axes.axhline(y=0, color="gray", linestyle="--", linewidth=0.8, zorder=1)
        self._axes.vlines(
            x_positions, min_prices_pct, max_prices_pct,
            colors="black", linewidth=1.5, zorder=4,
        )
        self._axes.scatter(
            x_positions, [0] * len(x_positions),
            color="black", marker="o", s=40, zorder=5,
        )
        self._axes.scatter(
            x_positions, last_prices_pct,
            color="red", marker="D", s=40, zorder=6, label="Último preço",
        )

    def _collect_all_y(
        self: "VWAPHistChart",
        violin_shapes: list[tuple[list[float], list[float]]],
        min_prices_pct: list[float],
        max_prices_pct: list[float],
        last_prices_pct: list[float],
    ) -> list[float]:
        """Reúne todos os valores percentuais para definir o limite do eixo Y."""
        all_y: list[float] = []
        for y_vals, _ in violin_shapes:
            all_y.extend(y_vals)
        all_y.extend(min_prices_pct)
        all_y.extend(max_prices_pct)
        all_y.extend(last_prices_pct)
        return all_y

    def _configure_axes(
        self: "VWAPHistChart",
        x_positions: list[int],
        tickers: list[str],
        all_y: list[float],
    ) -> None:
        """Configura rótulos, título, legenda e o limite vertical da figura."""
        self._axes.set_xticks(x_positions)
        self._axes.set_xticklabels(tickers, rotation=45)
        self._axes.set_title("VWAP — Distribuição de Preços")
        self._axes.set_ylabel("Diferença do VWAP (%)")
        self._axes.legend(loc="best")
        if all_y:
            max_abs = max(abs(min(all_y)), abs(max(all_y)))
            self._axes.set_ylim(-max_abs * 1.1, max_abs * 1.1)

    def _refresh_annotation(self: "VWAPHistChart") -> None:
        """Recria a anotação sobre os eixos após a limpeza da figura."""
        self._annot = self._create_annotation()

    def update(self: "VWAPHistChart", data: dict) -> None:
        """Atualiza o gráfico com a distribuição de preços em relação ao VWAP."""
        self._clear_hover_state()
        if not data:
            self._show_empty()
            return

        hide_empty(self._empty_label)
        self._axes.clear()

        (tickers, violin_data, vwap_values_abs, min_prices_pct,
         max_prices_pct, last_prices_pct) = collect_ticker_data(data)

        if not tickers:
            self._show_empty()
            return

        x_positions = list(range(len(tickers)))
        violin_shapes, max_vol, _bucket_size = compute_violin_shapes(violin_data)

        self._draw_violins(x_positions, violin_shapes, max_vol)
        self._store_hover_state(tickers, vwap_values_abs, violin_shapes, last_prices_pct)
        self._draw_markers(x_positions, min_prices_pct, max_prices_pct, last_prices_pct)
        all_y = self._collect_all_y(violin_shapes, min_prices_pct, max_prices_pct, last_prices_pct)
        self._configure_axes(x_positions, tickers, all_y)

        self._figure.tight_layout()
        self._refresh_annotation()
        self._canvas.draw()

    def _build_hover_text(self: "VWAPHistChart", idx: int) -> str:
        """Compõe o texto da anotação para o violino na posição informada."""
        ticker = self._hover_tickers[idx]
        vwap_abs = self._hover_vwaps[idx]
        buckets = self._hover_buckets[idx]
        if not buckets:
            return f"{ticker}\nVWAP: R$ {vwap_abs:.2f}"

        prices_pct = [b[0] for b in buckets]
        vols = [b[1] for b in buckets]
        min_pct = min(prices_pct)
        max_pct = max(prices_pct)
        total_vol = sum(vols)
        vol_str = f"{total_vol:.0f}" if total_vol < 1e6 else f"{total_vol / 1e6:.1f}M"
        last_pct = self._hover_last_pct[idx]
        return (
            f"{ticker}\n"
            f"VWAP: R$ {vwap_abs:.2f}\n"
            f"Δ Máx: {max_pct:+.2f}% / Δ Mín: {min_pct:+.2f}%\n"
            f"LastPric: {last_pct:+.2f}%\n"
            f"Volume: {vol_str}"
        )

    def _on_hover(self: "VWAPHistChart", event: MouseEvent) -> None:
        """Exibe o conteúdo do violino sob o mouse quando o cursor o sobrepõe."""
        if event.inaxes != self._axes or not self._violin_polygons:
            self._annot.set_visible(False)
            self._canvas.draw_idle()
            return

        for idx, poly in self._violin_polygons:
            if poly.contains(event)[0]:
                self._annot.set_text(self._build_hover_text(idx))
                self._annot.xy = (event.xdata, event.ydata)
                self._annot.set_visible(True)
                self._canvas.draw_idle()
                return

        self._annot.set_visible(False)
        self._canvas.draw_idle()

    def reset(self: "VWAPHistChart") -> None:
        """Limpa o gráfico e exibe o estado vazio."""
        self._show_empty()

    def get_figure(self: "VWAPHistChart") -> Figure:
        """Retorna a figura matplotlib utilizada pelo gráfico."""
        return self._figure
