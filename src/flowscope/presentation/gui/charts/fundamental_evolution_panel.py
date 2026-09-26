"""Painel de evolução dos fundamentos de um ticker.

Exibe small multiples — um mini-gráfico de linha por campo (Cotação, VP,
P/VP, Dividend Yield, Último dividendo, Nº de cotistas, Nº de cotas e
Shorts%) — com eixo de datas compartilhado e escala própria, a partir das
séries montadas por :mod:`flowscope.application.fundamental.evolucao`.
"""

import math
import tkinter as tk
from collections.abc import Callable, Sequence
from datetime import date

from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import date2num
from matplotlib.figure import Figure
from matplotlib.text import Annotation

from flowscope.application.fundamental.evolucao import (
    TIPO_INTEIRO,
    TIPO_MONETARIO,
    TIPO_PERCENTUAL,
    TIPO_PERCENTUAL_1,
    TIPO_QUANTIDADE,
    TIPO_RAZAO,
    PontoEvolucao,
    SerieEvolucao,
)
from flowscope.application.fundamental.formatters import (
    formatar_inteiro,
    formatar_percentual,
    formatar_quantidade,
    formatar_ratio,
    formatar_valor,
)
from flowscope.presentation.gui.charts.empty_state import (
    create_empty,
    hide_empty,
    show_empty,
)
from flowscope.presentation.gui.charts.toolbar import ToolbarBR

#: Formatação de exibição por tipo de campo.
_FORMATADORES: dict[str, Callable[[object], str]] = {
    TIPO_MONETARIO: lambda valor: f"R$ {formatar_valor(valor)}",
    TIPO_PERCENTUAL: lambda valor: formatar_percentual(valor, 2),
    TIPO_PERCENTUAL_1: lambda valor: formatar_percentual(valor, 1),
    TIPO_RAZAO: lambda valor: formatar_ratio(valor, 2),
    TIPO_QUANTIDADE: formatar_quantidade,
    TIPO_INTEIRO: formatar_inteiro,
}

#: Distância máxima, em pixels, entre o cursor e um ponto para abrir o tooltip.
_LIMIAR_TOOLTIP_PX = 20.0


def selecionar_ticks(datas: Sequence[date], maximo: int = 4) -> list[date]:
    """Seleciona até ``maximo`` datas para rotular o eixo, sem repetir."""
    datas = list(datas)
    if len(datas) <= maximo:
        return datas
    passo = (len(datas) - 1) / (maximo - 1)
    indices = sorted({round(i * passo) for i in range(maximo)})
    return [datas[indice] for indice in indices]


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
        """Constrói a figura, os oito eixos e a barra de ferramentas."""
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
            for indice in range(self._LINHAS * self._COLUNAS)
        ]
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        self._toolbar = ToolbarBR(
            self._canvas, self.frame, copy_chart_callback=copy_chart_callback
        )

        self._all_axes = list(self._axes)
        self._empty_label = create_empty(self._figure, self._all_axes)
        self._anotacoes: list[Annotation | None] = [None] * len(self._axes)
        self._series_plot: list[SerieEvolucao | None] = [None] * len(self._axes)
        self._canvas.mpl_connect("motion_notify_event", self._on_motion)

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
        self._definir_titulo(series, ticker)
        self._desenhar_paineis(series)
        self._configurar_eixos_x()
        self._canvas.draw()

    def _definir_titulo(
        self: "FundamentalEvolutionPanel",
        series: Sequence[SerieEvolucao],
        ticker: str | None,
    ) -> None:
        """Atualiza o título da figura com o ticker e o nº de datas."""
        n_datas = len({ponto.data for serie in series for ponto in serie.pontos})
        rotulo = f"Evolução dos Fundamentos — {ticker}" if ticker else (
            "Evolução dos Fundamentos"
        )
        self._figure.suptitle(
            f"{rotulo}  ({n_datas} datas no cache)", fontsize=11
        )

    def _desenhar_paineis(
        self: "FundamentalEvolutionPanel",
        series: Sequence[SerieEvolucao],
    ) -> None:
        """Desenha cada painel e registra a série e a anotação de hover."""
        for indice, ax in enumerate(self._axes):
            serie = series[indice] if indice < len(series) else None
            ax.clear()
            ax.set_axis_on()
            self._anotacoes[indice] = self._desenhar_serie(ax, serie)
            self._series_plot[indice] = self._serie_para_plot(serie)

    @staticmethod
    def _serie_para_plot(
        serie: SerieEvolucao | None,
    ) -> SerieEvolucao | None:
        """Retorna a série quando há pontos, ou ``None`` para o estado vazio."""
        if serie is None or serie.vazia:
            return None
        return serie

    def _configurar_eixos_x(
        self: "FundamentalEvolutionPanel",
    ) -> None:
        """Configura o eixo de datas de todos os painéis."""
        for indice, ax in enumerate(self._axes):
            self._configurar_eixo_x(ax, indice)

    def _desenhar_serie(
        self: "FundamentalEvolutionPanel",
        ax: Axes,
        serie: SerieEvolucao | None,
    ) -> Annotation | None:
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
            return None

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
        return self._criar_anotacao(ax)

    def _criar_anotacao(
        self: "FundamentalEvolutionPanel", ax: Axes
    ) -> Annotation:
        """Cria a anotação de hover oculta de um painel."""
        return ax.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox={
                "boxstyle": "round,pad=0.3", "fc": "yellow",
                "ec": "gray", "alpha": 0.8,
            },
            fontsize=8, visible=False, zorder=10,
        )

    def _configurar_eixo_x(
        self: "FundamentalEvolutionPanel",
        ax: Axes,
        indice: int,
    ) -> None:
        """Exibe os rótulos de data no painel inferior com dado de cada coluna."""
        serie = self._series_plot[indice]
        if serie is None:
            ax.set_xticks([])
            ax.tick_params(axis="x", labelbottom=False)
            return
        ticks = selecionar_ticks(serie.datas)
        ax.set_xticks(ticks)
        ax.set_xticklabels([data.strftime("%d/%m/%y") for data in ticks])
        if indice != self._ultimo_com_dado(indice % self._COLUNAS):
            ax.tick_params(axis="x", labelbottom=False)
            return
        ax.tick_params(axis="x", labelsize=7, labelrotation=30)

    def _ultimo_com_dado(
        self: "FundamentalEvolutionPanel", coluna: int
    ) -> int | None:
        """Retorna o painel inferior da coluna que possui série desenhada."""
        return max(
            (
                i for i in range(len(self._axes))
                if i % self._COLUNAS == coluna
                and self._series_plot[i] is not None
            ),
            default=None,
        )

    def _on_motion(
        self: "FundamentalEvolutionPanel", event: MouseEvent
    ) -> None:
        """Exibe o tooltip do ponto mais próximo do cursor, se houver."""
        ax = event.inaxes
        indice = self._indice_do_eixo(ax)
        if indice is None:
            self._ocultar_anotacoes()
            self._canvas.draw_idle()
            return
        serie = self._series_plot[indice]
        anotacao = self._anotacoes[indice]
        if serie is None or anotacao is None:
            self._ocultar_anotacoes()
            self._canvas.draw_idle()
            return
        ponto = self._ponto_mais_proximo(ax, serie, event.x, event.y)
        if ponto is None:
            self._ocultar_anotacoes()
            self._canvas.draw_idle()
            return
        self._mostrar_anotacao(serie, anotacao, ponto)
        self._canvas.draw_idle()

    def _indice_do_eixo(
        self: "FundamentalEvolutionPanel", ax: Axes | None
    ) -> int | None:
        """Retorna o índice do eixo na grade, ou ``None`` se não pertencer."""
        if ax is None:
            return None
        try:
            return self._axes.index(ax)
        except ValueError:
            return None

    def _ponto_mais_proximo(
        self: "FundamentalEvolutionPanel",
        ax: Axes,
        serie: SerieEvolucao,
        x: float,
        y: float,
    ) -> PontoEvolucao | None:
        """Retorna o ponto da série dentro do limiar de pixels do cursor."""
        xs = [date2num(ponto.data) for ponto in serie.pontos]
        ys = [float(ponto.valor) for ponto in serie.pontos]
        exibicao = ax.transData.transform(list(zip(xs, ys)))
        distancias = [math.hypot(px - x, py - y) for px, py in exibicao]
        indice = min(range(len(distancias)), key=distancias.__getitem__)
        if distancias[indice] > _LIMIAR_TOOLTIP_PX:
            return None
        return serie.pontos[indice]

    def _mostrar_anotacao(
        self: "FundamentalEvolutionPanel",
        serie: SerieEvolucao,
        anotacao: Annotation,
        ponto: PontoEvolucao,
    ) -> None:
        """Preenche e exibe a anotação com a data e o valor do ponto."""
        self._ocultar_anotacoes()
        anotacao.set_text(
            f"Data: {ponto.data:%d/%m/%y}\n"
            f"Valor: {formatar_ponto(serie.tipo, ponto.valor)}"
        )
        anotacao.xy = (date2num(ponto.data), float(ponto.valor))
        anotacao.set_visible(True)

    def _ocultar_anotacoes(self: "FundamentalEvolutionPanel") -> None:
        """Oculta todas as anotações de hover dos painéis."""
        for anotacao in self._anotacoes:
            if anotacao is not None:
                anotacao.set_visible(False)

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
        self._anotacoes = [None] * len(self._axes)
        self._series_plot = [None] * len(self._axes)
        self._canvas.draw()

    def reset(self: "FundamentalEvolutionPanel") -> None:
        """Limpa o painel e exibe o estado vazio."""
        self._show_empty()

    def get_figure(self: "FundamentalEvolutionPanel") -> Figure:
        """Retorna a figura matplotlib utilizada pelo painel."""
        return self._figure
