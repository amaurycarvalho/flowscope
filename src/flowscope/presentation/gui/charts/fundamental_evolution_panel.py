"""Painel de evolução dos fundamentos de um ticker.

Exibe small multiples — um mini-gráfico de linha por campo (Cotação, VP,
P/VP, Dividend Yield, Último dividendo, Nº de cotistas e Nº de cotas) — com
eixo de datas compartilhado e escala própria, a partir das séries montadas
pelo módulo :mod:`fundamental_evolution_data`.
"""

import tkinter as tk
from collections.abc import Callable, Sequence

from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import AutoDateLocator, DateFormatter
from matplotlib.figure import Figure

from flowscope.presentation.gui.charts.empty_state import (
    create_empty,
    hide_empty,
    show_empty,
)
from flowscope.presentation.gui.charts.fundamental_evolution_data import (
    TIPO_INTEIRO,
    TIPO_MONETARIO,
    TIPO_PERCENTUAL,
    TIPO_QUANTIDADE,
    TIPO_RAZAO,
    SerieEvolucao,
)
from flowscope.presentation.gui.charts.fundamental_formatters import (
    formatar_inteiro,
    formatar_percentual,
    formatar_quantidade,
    formatar_ratio,
    formatar_valor,
)
from flowscope.presentation.gui.charts.toolbar import ToolbarBR

#: Formatação de exibição por tipo de campo.
_FORMATADORES: dict[str, Callable[[object], str]] = {
    TIPO_MONETARIO: lambda valor: f"R$ {formatar_valor(valor)}",
    TIPO_PERCENTUAL: lambda valor: formatar_percentual(valor, 2),
    TIPO_RAZAO: lambda valor: formatar_ratio(valor, 2),
    TIPO_QUANTIDADE: formatar_quantidade,
    TIPO_INTEIRO: formatar_inteiro,
}


def formatar_ponto(tipo: str, valor: object) -> str:
    """Formata o valor de um ponto conforme o tipo do campo."""
    formatador = _FORMATADORES.get(tipo)
    if formatador is None:
        return str(valor)
    try:
        return formatador(valor)
    except (TypeError, ValueError, ArithmeticError):
        return str(valor)


class FundamentalEvolutionPanel:
    """Small multiples da evolução dos fundamentos de um ticker."""

    #: Número de linhas e colunas da grade de painéis.
    _LINHAS = 4
    _COLUNAS = 2

    def __init__(
        self: "FundamentalEvolutionPanel",
        parent: tk.Widget,
        *,
        copy_chart_callback: Callable[[Figure], None] | None = None,
    ) -> None:
        """Constrói a figura, os sete eixos e a barra de ferramentas."""
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(6, 6), dpi=100)
        self._figure.subplots_adjust(
            top=0.90, bottom=0.07, left=0.09, right=0.97,
            hspace=0.55, wspace=0.25,
        )
        grade = self._figure.add_gridspec(
            self._LINHAS, self._COLUNAS, hspace=0.55, wspace=0.25
        )
        self._axes: list[Axes] = [
            self._figure.add_subplot(
                grade[indice // self._COLUNAS, indice % self._COLUNAS]
            )
            for indice in range(self._LINHAS * self._COLUNAS - 1)
        ]
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._toolbar = ToolbarBR(
            self._canvas, self.frame, copy_chart_callback=copy_chart_callback
        )

        self._all_axes = list(self._axes)
        self._empty_label = create_empty(self._figure, self._all_axes)

    def update(
        self: "FundamentalEvolutionPanel",
        series: Sequence[SerieEvolucao] = (),
        ticker: str | None = None,
    ) -> None:
        """Redesenha os painéis com as séries informadas."""
        series = tuple(series)
        if not any(not serie.vazia for serie in series):
            self._show_empty(ticker)
            return

        hide_empty(self._empty_label)
        n_datas = len({ponto.data for serie in series for ponto in serie.pontos})
        rotulo = f"Evolução dos Fundamentos — {ticker}" if ticker else (
            "Evolução dos Fundamentos"
        )
        self._figure.suptitle(
            f"{rotulo}  ({n_datas} datas no cache)", fontsize=11
        )

        for indice, ax in enumerate(self._axes):
            serie = series[indice] if indice < len(series) else None
            ax.clear()
            ax.set_axis_on()
            self._desenhar_serie(ax, serie)
            self._configurar_eixo_x(ax, indice, serie)

        self._canvas.draw()

    def _desenhar_serie(
        self: "FundamentalEvolutionPanel",
        ax: Axes,
        serie: SerieEvolucao | None,
    ) -> None:
        """Desenha a linha de um campo ou o rótulo de ausência de dado."""
        if serie is None or serie.vazia:
            ax.text(
                0.5, 0.5, "sem dado",
                transform=ax.transAxes, ha="center", va="center",
                color="lightgray", fontsize=9,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            if serie is not None:
                ax.set_title(serie.titulo, fontsize=9)
            return

        datas = list(serie.datas)
        valores = [float(ponto.valor) for ponto in serie.pontos]
        ax.plot(
            datas, valores, marker="o", markersize=3, linewidth=1.4,
            color="#1f77b4", zorder=3,
        )
        ax.plot(
            [datas[-1]], [valores[-1]], marker="o", markersize=6,
            color="#d62728", zorder=4,
        )
        ax.annotate(
            formatar_ponto(serie.tipo, serie.pontos[-1].valor),
            xy=(datas[-1], valores[-1]), xytext=(6, 6),
            textcoords="offset points", fontsize=8,
            color="#d62728", fontweight="bold",
        )
        ax.set_title(serie.titulo, fontsize=9)
        ax.grid(True, alpha=0.25)
        ax.tick_params(axis="y", labelsize=7)

    def _configurar_eixo_x(
        self: "FundamentalEvolutionPanel",
        ax: Axes,
        indice: int,
        serie: SerieEvolucao | None,
    ) -> None:
        """Exibe os rótulos de data apenas no painel inferior de cada coluna."""
        if serie is None or serie.vazia:
            ax.tick_params(axis="x", labelbottom=False)
            return
        coluna = indice % self._COLUNAS
        ultimo = max(
            i for i in range(len(self._axes)) if i % self._COLUNAS == coluna
        )
        if indice != ultimo:
            ax.tick_params(axis="x", labelbottom=False)
            return
        ax.xaxis.set_major_locator(AutoDateLocator(maxticks=4))
        ax.xaxis.set_major_formatter(DateFormatter("%m/%y"))
        ax.tick_params(axis="x", labelsize=7, labelrotation=30)

    def _show_empty(
        self: "FundamentalEvolutionPanel", ticker: str | None = None
    ) -> None:
        """Limpa os painéis e exibe o rótulo de estado vazio."""
        if ticker:
            self._empty_label.set_text(f"Sem histórico em cache para {ticker}")
        else:
            self._empty_label.set_text("Selecione um ticker com histórico")
        self._figure.suptitle("")
        show_empty(self._figure, self._all_axes, self._empty_label)
        self._canvas.draw()

    def reset(self: "FundamentalEvolutionPanel") -> None:
        """Limpa o painel e exibe o estado vazio."""
        self._show_empty()

    def get_figure(self: "FundamentalEvolutionPanel") -> Figure:
        """Retorna a figura matplotlib utilizada pelo painel."""
        return self._figure
