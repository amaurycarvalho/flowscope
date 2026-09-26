"""Seleção de datas e montagem de séries do painel de evolução dos fundamentos.

Concentra as funções puras do painel: a amostragem Fibonacci acumulada das
datas retidas no cache histórico e a conversão das observações datadas nas
séries dos oito campos exibidos. Não executa I/O nem desenha — o painel
(:mod:`fundamental_evolution_panel`) consome apenas o resultado.
"""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from flowscope.application.fundamental_ports import ObservacaoFundamental
from flowscope.domain.fii import AnaliseFundamental

#: Gaps sucessivos, em dias, usados para amostrar as datas rumo ao passado.
FIBONACCI_GAPS: tuple[int, ...] = (
    1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377,
)

#: Tipos de campo, que definem a formatação de exibição no painel.
TIPO_MONETARIO = "monetario"
TIPO_PERCENTUAL = "percentual"
TIPO_PERCENTUAL_1 = "percentual_1"
TIPO_RAZAO = "razao"
TIPO_QUANTIDADE = "quantidade"
TIPO_INTEIRO = "inteiro"


@dataclass(frozen=True)
class CampoEvolucao:
    """Definição de um campo exibido na evolução e como extraí-lo da análise."""

    campo: str
    titulo: str
    tipo: str
    extrator: Callable[[AnaliseFundamental], object | None]


@dataclass(frozen=True)
class PontoEvolucao:
    """Valor observado de um campo em uma data."""

    data: date
    valor: object


@dataclass(frozen=True)
class SerieEvolucao:
    """Série temporal de um campo, com os pontos amostrados."""

    campo: str
    titulo: str
    tipo: str
    pontos: tuple[PontoEvolucao, ...]

    @property
    def vazia(self: "SerieEvolucao") -> bool:
        """Indica se a série não possui nenhum ponto."""
        return not self.pontos

    @property
    def datas(self: "SerieEvolucao") -> tuple[date, ...]:
        """Retorna as datas dos pontos, na ordem da série."""
        return tuple(ponto.data for ponto in self.pontos)


def _cotacao(analise: AnaliseFundamental) -> object | None:
    """Extrai a cotação da análise."""
    return analise.cotacao


def _vp_cota(analise: AnaliseFundamental) -> object | None:
    """Extrai o VP por cota da análise."""
    return analise.vp_cota


def _p_vp(analise: AnaliseFundamental) -> object | None:
    """Extrai o P/VP das métricas da análise."""
    return analise.metricas.p_vp if analise.metricas else None


def _dividend_yield(analise: AnaliseFundamental) -> object | None:
    """Extrai o Dividend Yield das métricas da análise."""
    return analise.metricas.dividend_yield if analise.metricas else None


def _ultimo_dividendo(analise: AnaliseFundamental) -> object | None:
    """Extrai o valor do último dividendo da análise."""
    return analise.ultimo_dividendo.valor


def _cotistas(analise: AnaliseFundamental) -> object | None:
    """Extrai o número de cotistas/acionistas da análise."""
    return analise.cotistas


def _cotas(analise: AnaliseFundamental) -> object | None:
    """Extrai o número de cotas/ações emitidas da análise."""
    return analise.cotas


def _shorts_pct(analise: AnaliseFundamental) -> object | None:
    """Extrai o Shorts% das métricas de short interest da análise."""
    return analise.short.shorts_pct if analise.short else None


#: Campos exibidos, na ordem dos painéis do painel de evolução.
CAMPOS_EVOLUCAO: tuple[CampoEvolucao, ...] = (
    CampoEvolucao("cotacao", "Cotação (R$)", TIPO_MONETARIO, _cotacao),
    CampoEvolucao("vp_cota", "VP (VP/Cota) (R$)", TIPO_MONETARIO, _vp_cota),
    CampoEvolucao("p_vp", "P/VP", TIPO_RAZAO, _p_vp),
    CampoEvolucao("dividend_yield", "Dividend Yield", TIPO_PERCENTUAL, _dividend_yield),
    CampoEvolucao(
        "ultimo_dividendo", "Último dividendo (R$)", TIPO_MONETARIO, _ultimo_dividendo
    ),
    CampoEvolucao("cotistas", "Nº de cotistas", TIPO_INTEIRO, _cotistas),
    CampoEvolucao("cotas", "Nº de cotas", TIPO_QUANTIDADE, _cotas),
    CampoEvolucao("shorts_pct", "Shorts%", TIPO_PERCENTUAL_1, _shorts_pct),
)


def selecionar_datas_fibonacci(datas: Iterable[date]) -> list[date]:
    """Seleciona datas do cache por gaps acumulados de Fibonacci.

    Caminha da data mais recente para a mais antiga, recuando gaps sucessivos
    (1, 2, 3, 5, ... dias) e aproximando cada alvo para a data disponível mais
    próxima. Inclui sempre a mais antiga e a mais recente, remove duplicatas e
    devolve o resultado em ordem crescente.
    """
    disponiveis = sorted(set(datas))
    if len(disponiveis) <= 2:
        return disponiveis

    mais_antiga = disponiveis[0]
    selecionadas = {mais_antiga, disponiveis[-1]}
    atual = disponiveis[-1]

    for gap in FIBONACCI_GAPS:
        alvo = atual - timedelta(days=gap)
        if alvo <= mais_antiga:
            break
        escolhida = _mais_proxima(disponiveis, alvo)
        if escolhida >= atual or escolhida in selecionadas:
            continue
        selecionadas.add(escolhida)
        atual = escolhida

    return sorted(selecionadas)


def _mais_proxima(disponiveis: Sequence[date], alvo: date) -> date:
    """Retorna a data disponível mais próxima do alvo (empate: a mais antiga)."""
    return min(disponiveis, key=lambda data: (abs((data - alvo).days), data))


def montar_series(
    observacoes: Sequence[ObservacaoFundamental],
) -> tuple[SerieEvolucao, ...]:
    """Monta as séries dos oito campos a partir das observações datadas.

    Aplica a amostragem Fibonacci às datas observadas e, para cada campo,
    produz os pontos com valor disponível — observações sem valor viram
    lacunas. Campos sem nenhum valor resultam em séries vazias.
    """
    selecionadas = set(
        selecionar_datas_fibonacci(observacao.data for observacao in observacoes)
    )
    por_data = {
        observacao.data: observacao.analise
        for observacao in observacoes
        if observacao.data in selecionadas
    }
    datas = sorted(por_data)

    series: list[SerieEvolucao] = []
    for campo in CAMPOS_EVOLUCAO:
        pontos = tuple(
            PontoEvolucao(data, valor)
            for data in datas
            if (valor := campo.extrator(por_data[data])) is not None
        )
        series.append(
            SerieEvolucao(campo.campo, campo.titulo, campo.tipo, pontos)
        )
    return tuple(series)
