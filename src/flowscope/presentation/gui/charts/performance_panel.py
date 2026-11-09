"""Painel de performance versus índice da "Análise Geral".

A figura pura (:class:`PerformanceFigure`) desenha as barras de excesso de
retorno em pontos percentuais e é testável sem ``DISPLAY``. A casca Tk
(:class:`PerformancePanel`) adiciona o combobox de benchmark e a ``ToolbarBR``.
"""

import logging
import tkinter as tk
from collections.abc import Callable, Mapping, Sequence
from tkinter import ttk

from matplotlib.backend_bases import MouseEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.text import Annotation

from flowscope.presentation.gui.charts.empty_state import (
    create_empty,
    hide_empty,
    show_empty,
)
from flowscope.presentation.gui.charts.toolbar import ToolbarBR

logger = logging.getLogger("flowscope")

#: Mensagem exibida quando não há dados de performance.
MENSAGEM_SEM_DADOS = "Selecione tickers FII ou ação com dados carregados"

#: Mensagem exibida quando não há ticker elegível para o benchmark.
MENSAGEM_SEM_ELEGIVEIS = "Nenhum ticker elegível para o benchmark selecionado"

#: Mensagem exibida quando a série do benchmark não foi obtida.
MENSAGEM_BENCHMARK_INDISPONIVEL = (
    "Benchmark indisponível: não foi possível obter a série do índice"
)

#: Aviso de evento societário suspeito exibido no hover.
AVISO_EVENTO = "Possível evento societário: retorno pode estar distorcido"


class PerformanceFigure:
    """Figura pura das barras de excesso de retorno versus índice."""

    def __init__(self: "PerformanceFigure") -> None:
        """Constrói a figura, o eixo único e o estado vazio."""
        self._figure = Figure(figsize=(7, 4), dpi=100)
        self._figure.subplots_adjust(left=0.10, right=0.97, top=0.90, bottom=0.22)
        self._ax = self._figure.add_subplot(111)
        self._empty_label = create_empty(self._figure, [self._ax])
        self._empty_label.set_wrap(True)
        self._dados: dict = {}
        self._benchmark: str | None = None
        self._hover: list[dict] = []
        self._bars: list[Rectangle] = []
        self._annot = self._criar_anotacao()

    def _draw(self: "PerformanceFigure") -> None:
        """Redesenha a figura; a casca Tk sobrescreve com o canvas."""

    def update(
        self: "PerformanceFigure",
        dados: Mapping[str, object],
        benchmark: str | None = None,
    ) -> None:
        """Atualiza a figura a partir do payload de performance."""
        self._dados = dict(dados or {})
        self._benchmark = benchmark or self._default()
        self._render_benchmark(self._benchmark)

    def _default(self: "PerformanceFigure") -> str | None:
        """Retorna o benchmark padrão do payload ou a primeira opção."""
        default = self._dados.get("default")
        if isinstance(default, str):
            return default
        opcoes = self._dados.get("benchmarks", [])
        return opcoes[0] if opcoes else None

    def benchmarks(self: "PerformanceFigure") -> list[str]:
        """Retorna as opções de benchmark oferecidas no payload."""
        opcoes = self._dados.get("benchmarks", [])
        return list(opcoes) if isinstance(opcoes, Sequence) else []

    def benchmark_atual(self: "PerformanceFigure") -> str | None:
        """Retorna o benchmark atualmente exibido."""
        return self._benchmark

    def _render_benchmark(self: "PerformanceFigure", benchmark: str | None) -> None:
        """Desenha as barras do benchmark ou o estado vazio correspondente."""
        resultado = self._resultado(benchmark)
        if resultado is None or not resultado.get("index_available", True):
            self._show_empty(self._mensagem(resultado))
            return
        tickers = resultado.get("tickers", [])
        if not tickers:
            self._show_empty(MENSAGEM_SEM_ELEGIVEIS)
            return
        self._draw_bars(benchmark, tickers)

    def _resultado(self: "PerformanceFigure", benchmark: str | None) -> dict | None:
        """Retorna o resultado serializado de um benchmark."""
        if benchmark is None:
            return None
        resultados = self._dados.get("results", {})
        if not isinstance(resultados, Mapping):
            return None
        resultado = resultados.get(benchmark)
        return resultado if isinstance(resultado, dict) else None

    def _mensagem(self: "PerformanceFigure", resultado: dict | None) -> str:
        """Escolhe a mensagem de estado vazio conforme a causa."""
        if resultado is None:
            return MENSAGEM_SEM_DADOS if not self._dados else MENSAGEM_SEM_ELEGIVEIS
        return MENSAGEM_BENCHMARK_INDISPONIVEL

    def _draw_bars(
        self: "PerformanceFigure", benchmark: str | None, tickers: list
    ) -> None:
        """Desenha as barras a partir de zero e guarda o estado de hover."""
        itens = [item for item in tickers if isinstance(item, Mapping)]
        if not itens:
            logger.warning(
                "Performance %s: entradas de ticker inválidas no resultado",
                benchmark,
            )
            self._show_empty(MENSAGEM_SEM_ELEGIVEIS)
            return
        hide_empty(self._empty_label)
        self._ax.clear()
        self._ax.set_axis_on()
        valores = [_excesso_seguro(item) for item in itens]
        posicoes = list(range(len(itens)))
        cores = ["#2e7d32" if valor >= 0 else "#c62828" for valor in valores]
        self._bars = list(self._ax.bar(posicoes, valores, color=cores))
        self._hover = [dict(item) for item in itens]
        self._configure_axes(benchmark, itens, posicoes, valores)
        self._annot = self._criar_anotacao()
        self._figure.tight_layout()
        self._draw()

    def _configure_axes(
        self: "PerformanceFigure",
        benchmark: str | None,
        itens: list[Mapping],
        posicoes: list[int],
        valores: list[float],
    ) -> None:
        """Configura rótulos, título, linha do zero e limite vertical."""
        self._ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8)
        self._ax.set_xticks(posicoes)
        self._ax.set_xticklabels(
            [str(item.get("ticker", "")) for item in itens], rotation=45, ha="right"
        )
        self._ax.set_ylabel(f"Excesso vs {benchmark} (p.p.)")
        self._ax.set_title(f"Performance vs {benchmark}")
        max_abs = max((abs(valor) for valor in valores), default=0.0)
        if max_abs > 0:
            self._ax.set_ylim(-max_abs * 1.15, max_abs * 1.15)

    def _criar_anotacao(self: "PerformanceFigure") -> Annotation:
        """Cria a anotação invisível usada no hover."""
        return self._ax.annotate(
            "", xy=(0, 0), xytext=(8, 8), textcoords="offset points",
            bbox={
                "boxstyle": "round,pad=0.3", "fc": "yellow",
                "ec": "gray", "alpha": 0.9,
            },
            fontsize=9, visible=False,
        )

    def hover_text(self: "PerformanceFigure", indice: int) -> str:
        """Compõe o texto de hover para a barra informada."""
        item = self._hover[indice]
        linhas = [
            str(item.get("ticker", "")),
            f"Retorno do ticker: {_formatar_pct(item.get('ticker_return'))}",
            f"Retorno do índice: {_formatar_pct(item.get('index_return'))}",
            f"Excesso: {_formatar_pp(item.get('excess_pp'))}",
        ]
        if item.get("suspicious_event"):
            linhas.append(AVISO_EVENTO)
        return "\n".join(linhas)

    def _on_hover(self: "PerformanceFigure", event: MouseEvent) -> None:
        """Exibe a anotação quando o cursor está sobre uma barra."""
        if event.inaxes != self._ax:
            self._ocultar_anotacao()
            return
        for indice, barra in enumerate(self._bars):
            if barra.contains(event)[0]:
                self._mostrar_anotacao(indice, event)
                return
        self._ocultar_anotacao()

    def _mostrar_anotacao(
        self: "PerformanceFigure", indice: int, event: MouseEvent
    ) -> None:
        """Posiciona e exibe a anotação da barra sob o mouse."""
        self._annot.set_text(self.hover_text(indice))
        self._annot.xy = (event.xdata, event.ydata)
        self._annot.set_visible(True)
        self._draw()

    def _ocultar_anotacao(self: "PerformanceFigure") -> None:
        """Oculta a anotação de hover."""
        self._annot.set_visible(False)
        self._draw()

    def _show_empty(self: "PerformanceFigure", mensagem: str) -> None:
        """Limpa o eixo e exibe a mensagem de estado vazio."""
        self._hover = []
        self._bars = []
        self._empty_label.set_text(mensagem)
        self._figure.suptitle("")
        show_empty(self._figure, [self._ax], self._empty_label)
        self._draw()

    def reset(self: "PerformanceFigure") -> None:
        """Limpa o painel e exibe o estado vazio."""
        self._dados = {}
        self._benchmark = None
        self._show_empty(MENSAGEM_SEM_DADOS)

    def get_figure(self: "PerformanceFigure") -> Figure:
        """Retorna a figura matplotlib utilizada pelo painel."""
        return self._figure


class PerformancePanel(PerformanceFigure):
    """Casca Tk com combobox de benchmark e a barra de ferramentas padrão."""

    def __init__(
        self: "PerformancePanel",
        parent: tk.Widget,
        *,
        copy_chart_callback: Callable[[Figure], None] | None = None,
    ) -> None:
        """Monta a figura pura, o combobox e a embute no canvas Tk."""
        super().__init__()
        self.frame = tk.Frame(parent)
        controles = tk.Frame(self.frame)
        controles.pack(side=tk.TOP, fill=tk.X)
        tk.Label(controles, text="Benchmark:").pack(side=tk.LEFT)
        self._benchmark_var = tk.StringVar()
        self._combo = ttk.Combobox(
            controles, textvariable=self._benchmark_var,
            state="readonly", width=10,
        )
        self._combo.pack(side=tk.LEFT, padx=6)
        self._combo.bind("<<ComboboxSelected>>", self._on_benchmark_changed)
        self._canvas = FigureCanvasTkAgg(self._figure, master=self.frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        self._toolbar = ToolbarBR(
            self._canvas, self.frame, copy_chart_callback=copy_chart_callback
        )
        self._canvas.mpl_connect("motion_notify_event", self._on_hover)

    def update(
        self: "PerformancePanel",
        dados: Mapping[str, object],
        benchmark: str | None = None,
    ) -> None:
        """Atualiza o combobox e a figura a partir do payload."""
        dados = dados or {}
        self._aplicar_combobox(dados)
        selecionado = self._benchmark_var.get() or None
        super().update(dados, benchmark=benchmark or selecionado)

    def _aplicar_combobox(self: "PerformancePanel", dados: Mapping) -> None:
        """Configura as opções e o default do combobox readonly."""
        opcoes = dados.get("benchmarks", [])
        opcoes = list(opcoes) if isinstance(opcoes, Sequence) else []
        self._combo["values"] = opcoes
        self._combo["state"] = "readonly" if opcoes else "disabled"
        default = dados.get("default")
        atual = self._benchmark_var.get()
        escolhido = None
        if isinstance(default, str) and default in opcoes:
            escolhido = default
        elif atual in opcoes:
            escolhido = atual
        elif opcoes:
            escolhido = opcoes[0]
        self._benchmark_var.set(escolhido or "")

    def _on_benchmark_changed(self: "PerformancePanel", event: object = None) -> None:
        """Redesenha a figura ao trocar o benchmark."""
        self._benchmark = self._benchmark_var.get() or None
        self._render_benchmark(self._benchmark)

    def _draw(self: "PerformancePanel") -> None:
        """Redesenha a figura pelo canvas Tk."""
        self._canvas.draw()


def _excesso_seguro(item: Mapping) -> float:
    """Devolve o excesso como float, registrando entradas inválidas."""
    try:
        return float(item.get("excess_pp", 0.0))
    except (TypeError, ValueError):
        logger.warning(
            "Performance: excesso inválido para o ticker %r: %r",
            item.get("ticker"),
            item.get("excess_pp"),
        )
        return 0.0


def _formatar_pct(valor: object) -> str:
    """Formata um retorno fracionário como percentual brasileiro."""
    try:
        numero = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "N/A"
    return f"{numero * 100:+.2f}%".replace(".", ",")


def _formatar_pp(valor: object) -> str:
    """Formata o excesso em pontos percentuais."""
    try:
        numero = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "N/A"
    return f"{numero:+.2f}".replace(".", ",") + " p.p."
