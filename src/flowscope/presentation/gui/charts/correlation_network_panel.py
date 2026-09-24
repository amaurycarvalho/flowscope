"""Painel da rede de correlação e cointegração da "Análise Geral".

Desenha um grafo force-directed em que cada ticker é um nó e cada par
relevante é uma aresta: a cor da aresta representa a correlação assinada
de curto prazo (escala fixa de −1 a +1), o estilo e a espessura
representam a cointegração de longo prazo, a cor do nó representa a
comunidade e o tamanho, a centralidade.
"""

import tkinter as tk
from collections.abc import Callable, Mapping

import networkx as nx
from matplotlib import colormaps
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from flowscope.domain.network_analysis import NetworkResult, analyze_network
from flowscope.presentation.gui.charts.empty_state import (
    create_empty,
    hide_empty,
    show_empty,
)
from flowscope.presentation.gui.charts.network_data import (
    AVISO_COINT_INDISPONIVEL,
    MENSAGEM_SEM_TICKERS,
    DadosRede,
    extrair_series,
    formatar_modularidade,
    mensagem_indisponivel,
    rotulo_diagnostico,
)
from flowscope.presentation.gui.charts.toolbar import ToolbarBR

#: Semente fixa do layout force-directed para reprodutibilidade.
_SEED = 42

#: Faixa de tamanho dos nós conforme a centralidade.
_MIN_NODE_SIZE = 120.0
_MAX_NODE_SIZE = 900.0

#: Número de cores distintas do colormap de comunidades.
_N_COMPORTAMENTOS = 20


class CorrelationNetworkPanel:
    """Grafo de correlação/cointegração dos tickers selecionados."""

    def __init__(
        self: "CorrelationNetworkPanel",
        parent: tk.Widget,
        *,
        copy_chart_callback: Callable[[Figure], None] | None = None,
    ) -> None:
        """Constrói a figura, o eixo único e a barra de ferramentas."""
        self.frame = tk.Frame(parent)
        self._figure = Figure(figsize=(7, 6), dpi=100)
        self._figure.subplots_adjust(left=0.05, right=0.90, top=0.88, bottom=0.10)
        self._ax = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._toolbar = ToolbarBR(
            self._canvas, self.frame, copy_chart_callback=copy_chart_callback
        )
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        self._empty_label = create_empty(self._figure, [self._ax])
        self._empty_label.set_wrap(True)
        self._colorbar = None
        self._resultado: NetworkResult | None = None
        self._positions: dict = {}

    def update(
        self: "CorrelationNetworkPanel",
        current_data: Mapping[str, object],
        tickers: list[str] | None = None,
    ) -> None:
        """Recalcula e redesenha a rede a partir dos dados já carregados."""
        dados = extrair_series(dict(current_data), tickers)
        self._resultado = analyze_network(dados.series)
        self._render(dados, self._resultado)

    def _render(
        self: "CorrelationNetworkPanel",
        dados: DadosRede,
        resultado: NetworkResult,
    ) -> None:
        """Desenha o grafo ou apresenta o estado vazio correspondente."""
        if not resultado.correlation_available:
            self._show_empty(mensagem_indisponivel(dados, resultado))
            return
        self._remove_colorbar()
        hide_empty(self._empty_label)
        self._ax.clear()
        self._ax.set_axis_on()
        self._positions = self._layout(resultado)
        self._draw_edges(resultado)
        self._draw_nodes(resultado)
        self._draw_colorbar()
        self._draw_legend()
        self._figure.suptitle(
            f"Rede de Correlação — {len(resultado.tickers)} tickers", fontsize=12
        )
        self._ax.set_title(rotulo_diagnostico(resultado.diagnostics), fontsize=9)
        self._ax.text(
            0.01, 0.99, formatar_modularidade(resultado.modularity),
            transform=self._ax.transAxes, fontsize=8, color="#444444", va="top",
        )
        self._ax.axis("off")
        if not resultado.cointegration_available:
            self._draw_warning()
        self._canvas.draw()

    def _layout(self: "CorrelationNetworkPanel", resultado: NetworkResult) -> dict:
        """Calcula as posições dos nós com semente fixa."""
        if resultado.graph.number_of_nodes() == 0:
            return {}
        return nx.spring_layout(resultado.graph, seed=_SEED)

    def _draw_edges(
        self: "CorrelationNetworkPanel", resultado: NetworkResult
    ) -> None:
        """Desenha as arestas com cor por correlação e estilo por cointegração."""
        cmap = colormaps["coolwarm"]
        norm = Normalize(vmin=-1.0, vmax=1.0)
        for origem, destino, attrs in resultado.graph.edges(data=True):
            if origem not in self._positions or destino not in self._positions:
                continue
            cointegrated = bool(attrs.get("cointegrated"))
            self._ax.plot(
                [self._positions[origem][0], self._positions[destino][0]],
                [self._positions[origem][1], self._positions[destino][1]],
                color=cmap(norm(float(attrs.get("correlation", 0.0)))),
                linewidth=2.6 if cointegrated else 1.0,
                linestyle="-" if cointegrated else "--",
                alpha=0.9 if cointegrated else 0.55,
                zorder=1,
            )

    def _draw_nodes(
        self: "CorrelationNetworkPanel", resultado: NetworkResult
    ) -> None:
        """Desenha os nós com cor por comunidade e tamanho por centralidade."""
        nodes = list(resultado.graph.nodes())
        if not nodes:
            return
        cmap = colormaps["tab20"]
        colors = [
            cmap(resultado.communities.get(node, 0) % _N_COMPORTAMENTOS)
            for node in nodes
        ]
        sizes = [self._node_size(resultado.centrality.get(node, 0.0)) for node in nodes]
        nx.draw_networkx_nodes(
            resultado.graph, self._positions, ax=self._ax, nodelist=nodes,
            node_color=colors, node_size=sizes,
            edgecolors="black", linewidths=0.6,
        )
        nx.draw_networkx_labels(
            resultado.graph, self._positions, ax=self._ax, font_size=8
        )

    def _node_size(self: "CorrelationNetworkPanel", centrality: float) -> float:
        """Calcula o tamanho do nó a partir da centralidade, na faixa fixa."""
        valor = max(0.0, min(1.0, centrality))
        return _MIN_NODE_SIZE + (_MAX_NODE_SIZE - _MIN_NODE_SIZE) * valor

    def _draw_colorbar(self: "CorrelationNetworkPanel") -> None:
        """Adiciona a colorbar da correlação assinada."""
        mappable = ScalarMappable(
            norm=Normalize(vmin=-1.0, vmax=1.0), cmap=colormaps["coolwarm"]
        )
        mappable.set_array([])
        self._colorbar = self._figure.colorbar(
            mappable, ax=self._ax, fraction=0.046, pad=0.04
        )
        self._colorbar.set_label("Correlação assinada", fontsize=8)
        self._colorbar.ax.tick_params(labelsize=7)

    def _draw_legend(self: "CorrelationNetworkPanel") -> None:
        """Exibe a legenda que distingue arestas cointegradas das demais."""
        handles = [
            Line2D([0], [0], color="#333333", linewidth=2.6, label="Cointegrado"),
            Line2D(
                [0], [0], color="#333333", linewidth=1.0, linestyle="--",
                label="Não cointegrado",
            ),
        ]
        self._ax.legend(handles=handles, loc="lower left", fontsize=8)

    def _draw_warning(self: "CorrelationNetworkPanel") -> None:
        """Sinaliza que a cointegração está indisponível por densidade."""
        self._ax.text(
            0.5, -0.02, AVISO_COINT_INDISPONIVEL,
            transform=self._ax.transAxes, ha="center", va="top",
            fontsize=8, color="#b8860b",
        )

    def _remove_colorbar(self: "CorrelationNetworkPanel") -> None:
        """Remove a colorbar anterior, se existir."""
        if self._colorbar is not None:
            self._colorbar.remove()
            self._colorbar = None

    def _show_empty(
        self: "CorrelationNetworkPanel", mensagem: str
    ) -> None:
        """Limpa o eixo e exibe a mensagem de estado vazio."""
        self._remove_colorbar()
        self._positions = {}
        self._empty_label.set_text(mensagem)
        self._figure.suptitle("")
        show_empty(self._figure, [self._ax], self._empty_label)
        self._canvas.draw()

    def reset(self: "CorrelationNetworkPanel") -> None:
        """Limpa o painel e exibe o estado vazio."""
        self._show_empty(MENSAGEM_SEM_TICKERS)

    def get_figure(self: "CorrelationNetworkPanel") -> Figure:
        """Retorna a figura matplotlib utilizada pelo painel."""
        return self._figure
