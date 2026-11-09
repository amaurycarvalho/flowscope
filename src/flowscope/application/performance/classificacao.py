"""Classificação FII × Ação e seleção dos benchmarks da sub-aba."""

from collections.abc import Callable, Mapping, Sequence

from flowscope.application.performance.modelos import (
    BENCHMARKS_POR_TIPO,
    ORDEM_BENCHMARKS,
    TIPO_ACAO,
    TIPO_FII,
)
from flowscope.domain.fii.classification import (
    TIPO_EXIBICAO_FII,
    TIPO_EXIBICAO_PAPEL,
    TipoAtivo,
    classificar_ticker,
)

ResolverFiagro = Callable[[str], bool]


def classificar_elegiveis(
    tickers: Sequence[str],
    fundamental_data: Mapping[str, object] | None = None,
    resolver_fiagro: ResolverFiagro | None = None,
) -> dict[str, str]:
    """Classifica os tickers elegíveis como ``FII`` ou ``ACAO``.

    A precedência é a classificação da análise fundamentalista e, como
    fallback, :func:`classificar_ticker`. ETF, BDR e desconhecidos ficam fora.
    """
    dados = fundamental_data or {}
    resultado: dict[str, str] = {}
    for ticker in tickers:
        tipo = _tipo_do_ticker(ticker, dados, resolver_fiagro)
        if tipo is TipoAtivo.FII:
            resultado[ticker] = TIPO_FII
        elif tipo is TipoAtivo.ACAO:
            resultado[ticker] = TIPO_ACAO
    return resultado


def _tipo_do_ticker(
    ticker: str,
    fundamental_data: Mapping[str, object],
    resolver_fiagro: ResolverFiagro | None,
) -> TipoAtivo | None:
    """Resolve o tipo do ticker pela fundamentação e, depois, pela sintaxe."""
    tipo = _tipo_fundamental(fundamental_data.get(ticker))
    if tipo is not None:
        return tipo
    return classificar_ticker(ticker, resolver_fiagro=resolver_fiagro).tipo


def _tipo_fundamental(analise: object) -> TipoAtivo | None:
    """Extrai o tipo de uma observação fundamentalista, tolerando formatos.

    Usa primeiro a classificação determinística e, quando ela é desconhecida,
    o discriminador FII/Papel derivado do Fundamentus (`classificacao_exibicao`).
    """
    if analise is None:
        return None
    tipo = _tipo_deterministico(_campo(analise, "classificacao"))
    if tipo in (TipoAtivo.FII, TipoAtivo.ACAO):
        return tipo
    return _tipo_de_exibicao(_campo(analise, "classificacao_exibicao"))


def _tipo_deterministico(classificacao: object) -> TipoAtivo | None:
    """Interpreta o campo ``tipo`` da classificação determinística."""
    tipo = _campo(classificacao, "tipo")
    if isinstance(tipo, TipoAtivo):
        return tipo
    if isinstance(tipo, str):
        try:
            return TipoAtivo(tipo.lower())
        except ValueError:
            return None
    return None


def _tipo_de_exibicao(exibicao: object) -> TipoAtivo | None:
    """Traduz o discriminador de exibição FII/Papel em tipo de ativo."""
    tipo = _campo(exibicao, "tipo")
    if tipo == TIPO_EXIBICAO_FII:
        return TipoAtivo.FII
    if tipo != TIPO_EXIBICAO_PAPEL:
        return None
    sub_tipo = _campo(exibicao, "sub_tipo")
    rotulo = sub_tipo if isinstance(sub_tipo, str) else ""
    if "BDR" in rotulo:
        return TipoAtivo.BDR
    if "ETF" in rotulo:
        return TipoAtivo.ETF
    return TipoAtivo.ACAO


def _campo(objeto: object, nome: str) -> object:
    """Lê um campo de um objeto ou de um dicionário."""
    if isinstance(objeto, Mapping):
        return objeto.get(nome)
    return getattr(objeto, nome, None)


def benchmarks_disponiveis(classificacao: Mapping[str, str]) -> list[str]:
    """Retorna os benchmarks oferecidos, na ordem de exibição."""
    tipos = set(classificacao.values())
    opcoes: list[str] = []
    for benchmark in ORDEM_BENCHMARKS:
        if any(benchmark in BENCHMARKS_POR_TIPO[t] for t in tipos):
            opcoes.append(benchmark)
    return opcoes


def benchmark_padrao(
    tickers: Sequence[str], classificacao: Mapping[str, str]
) -> str | None:
    """Escolhe o benchmark inicial pelo primeiro ticker FII ou ação."""
    for ticker in tickers:
        tipo = classificacao.get(ticker)
        if tipo == TIPO_FII:
            return "IFIX"
        if tipo == TIPO_ACAO:
            return "IBOV"
    opcoes = benchmarks_disponiveis(classificacao)
    return opcoes[0] if opcoes else None


def tickers_para_benchmark(
    classificacao: Mapping[str, str], benchmark: str
) -> list[str]:
    """Retorna os tickers elegíveis para o benchmark informado."""
    tipo = TIPO_FII
    if benchmark != "IFIX":
        tipo = TIPO_ACAO
    return [t for t, valor in classificacao.items() if valor == tipo]
