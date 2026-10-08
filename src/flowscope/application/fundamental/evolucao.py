"""Seleção de datas e montagem de séries do painel de evolução dos fundamentos.

Concentra as funções puras do painel: a definição da janela de período, a
amostragem das datas retidas no cache histórico conforme o método selecionado
(Fibonacci e variantes, Monte Carlo e duplo, todos os dias) e a conversão das
observações datadas nas séries dos oito campos exibidos. Não executa I/O nem
desenha — o painel (:mod:`fundamental_evolution_panel`) consome apenas o
resultado.
"""

import random
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


#: Métodos de amostragem aceitos, alinhados ao ``SamplingConfig`` da GUI.
METODO_FIBONACCI = "fibonacci"
METODO_FIBONACCI_REVERSO = "fibonacci_reverse"
METODO_FIBONACCI_DUPLO = "fibonacci_double"
METODO_MONTE_CARLO = "monte_carlo"
METODO_MONTE_CARLO_DUPLO = "monte_carlo_double"
METODO_TODOS_OS_DIAS = "all_days"

#: Datas intermediárias sorteadas por método de Monte Carlo.
MONTE_CARLO_INTERMEDIARIAS = 5
MONTE_CARLO_DUPLO_INTERMEDIARIAS = 12

#: Número de alvos de cada margem no método Fibonacci duplo.
FIBONACCI_DUPLO_MARGEM = 3


def definir_janela(
    datas: Iterable[date], ancora: date, periodo_dias: int
) -> tuple[date, date] | None:
    """Retorna o intervalo ``[inicio, fim]`` da janela de amostragem.

    Ancora na data informada; quando a janela não contiver nenhuma observação,
    recua a âncora para a observação mais recente disponível. Retorna ``None``
    quando não há observações.
    """
    disponiveis = sorted(set(datas))
    if not disponiveis:
        return None
    largura = max(periodo_dias, 0)
    inicio = ancora - timedelta(days=largura)
    fim = ancora
    if any(inicio <= data <= fim for data in disponiveis):
        return inicio, fim
    fim = disponiveis[-1]
    return fim - timedelta(days=largura), fim


def selecionar_datas(
    disponiveis: Iterable[date],
    metodo: str,
    *,
    semente: object | None = None,
) -> list[date]:
    """Seleciona as datas exibidas conforme o método de amostragem.

    Preserva o contrato de exibição: as observações mais antiga e mais recente
    sempre aparecem e, com duas ou menos observações, todas são devolvidas.
    """
    datas = sorted(set(disponiveis))
    if len(datas) <= 2:
        return datas
    if metodo == METODO_FIBONACCI_REVERSO:
        return selecionar_datas_fibonacci_reverso(datas)
    if metodo == METODO_FIBONACCI_DUPLO:
        return selecionar_datas_fibonacci_duplo(datas)
    if metodo == METODO_TODOS_OS_DIAS:
        return datas
    if metodo == METODO_MONTE_CARLO:
        return selecionar_datas_monte_carlo(
            datas, MONTE_CARLO_INTERMEDIARIAS, semente=semente
        )
    if metodo == METODO_MONTE_CARLO_DUPLO:
        return selecionar_datas_monte_carlo(
            datas, MONTE_CARLO_DUPLO_INTERMEDIARIAS, semente=semente
        )
    return selecionar_datas_fibonacci(datas)


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
    return _caminhar_fibonacci(disponiveis, do_recente=True)


def selecionar_datas_fibonacci_reverso(datas: Iterable[date]) -> list[date]:
    """Seleciona datas concentrando-se nas mais antigas da janela.

    Espelha a amostragem de Fibonacci: caminha da data mais antiga para a mais
    recente com os mesmos gaps sucessivos, incluindo sempre os extremos.
    """
    disponiveis = sorted(set(datas))
    if len(disponiveis) <= 2:
        return disponiveis
    return _caminhar_fibonacci(disponiveis, do_recente=False)


def selecionar_datas_fibonacci_duplo(datas: Iterable[date]) -> list[date]:
    """Seleciona datas concentrando-se nas duas margens da janela.

    Combina os primeiros alvos do caminho recente e do caminho antigo com a
    observação mais próxima do centro da janela, sempre incluindo os extremos.
    """
    disponiveis = sorted(set(datas))
    if len(disponiveis) <= 2:
        return disponiveis
    recentes = _caminhar_fibonacci(
        disponiveis, do_recente=True, passos=FIBONACCI_DUPLO_MARGEM
    )
    antigas = _caminhar_fibonacci(
        disponiveis, do_recente=False, passos=FIBONACCI_DUPLO_MARGEM
    )
    centro_alvo = disponiveis[0] + (disponiveis[-1] - disponiveis[0]) / 2
    centro = _mais_proxima(disponiveis, centro_alvo)
    return sorted(set(recentes) | set(antigas) | {centro})


def selecionar_datas_monte_carlo(
    datas: Iterable[date], quantidade: int, *, semente: object | None = None
) -> list[date]:
    """Seleciona os extremos e uma amostra aleatória das datas intermediárias.

    O sorteio usa :class:`random.Random` semeado por ``semente`` para que a
    amostra seja estável entre renders com a mesma configuração.
    """
    disponiveis = sorted(set(datas))
    if len(disponiveis) <= 2:
        return disponiveis
    intermediarias = disponiveis[1:-1]
    sorteio = random.Random(semente)
    escolhidas = sorteio.sample(
        intermediarias, min(quantidade, len(intermediarias))
    )
    return sorted({disponiveis[0], disponiveis[-1], *escolhidas})


def _caminhar_fibonacci(
    disponiveis: Sequence[date],
    *,
    do_recente: bool,
    passos: int | None = None,
) -> list[date]:
    """Caminha de um extremo com gaps de Fibonacci, aproximando aos alvos."""
    atual, limite = (
        (disponiveis[-1], disponiveis[0])
        if do_recente
        else (disponiveis[0], disponiveis[-1])
    )
    passo = -1 if do_recente else 1
    selecionadas = {disponiveis[0], disponiveis[-1]}
    gaps = FIBONACCI_GAPS if passos is None else FIBONACCI_GAPS[:passos]
    for gap in gaps:
        if gap >= abs((limite - atual).days):
            break
        escolhida = _mais_proxima(disponiveis, atual + timedelta(days=passo * gap))
        avancou = (escolhida - atual).days * passo > 0
        if not avancou or escolhida in selecionadas:
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

    Não faz amostragem: recebe as observações já selecionadas e, para cada
    campo, produz os pontos com valor disponível — observações sem valor viram
    lacunas. Campos sem nenhum valor resultam em séries vazias.
    """
    por_data = {
        observacao.data: observacao.analise for observacao in observacoes
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
