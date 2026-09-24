"""Serialização compacta da tabela de fundamentos carregada.

Reaproveita a montagem de linhas da tabela fundamentalista para produzir um
bloco textual enxuto, com uma linha por ticker, usado como contexto do chat.
A aba "Chat AI" usa sempre a watchlist completa; o ticker referido é inferido
pela LLM a partir da pergunta.
"""

from collections.abc import Iterable, Mapping

from flowscope.presentation.gui.charts.fundamental_formatters import NA
from flowscope.presentation.gui.charts.fundamental_rows import (
    _COLUNAS,
    montar_linhas,
)

#: Orientação exibida no contexto quando não há fundamentos carregados.
ORIENTACAO_SEM_DADOS = (
    "Nenhum dado de fundamentos carregado no momento. Para consultar "
    "fundamentos, carregue os dados da data desejada pelo botão de carregar "
    "a análise."
)

#: Valores de célula considerados vazios e omitidos do bloco compacto.
_VAZIOS = frozenset({NA, "", "--"})


def tickers_do_escopo(
    dados: Mapping[str, object],
    ticker: str | None,
    watchlist: Iterable[str],
) -> list[str]:
    """Resolve os tickers do escopo do bloco de fundamentos.

    Com ``ticker`` informado o escopo é apenas esse ticker; sem ele, é a
    watchlist completa, na ordem em que foi exibida. A aba "Chat AI" usa a
    watchlist completa.
    """
    if ticker:
        return [ticker] if ticker in dados else []
    return [t for t in watchlist if t in dados]


def _itens_compactos(
    cabecalhos: list[str], valores: tuple[str, ...]
) -> list[str]:
    """Formata os pares ``cabeçalho=valor`` omitindo células vazias."""
    return [
        f"{cabecalho}={valor}"
        for cabecalho, valor in zip(cabecalhos, valores)
        if valor not in _VAZIOS
    ]


def serializar_fundamentos(
    dados: Mapping[str, object], tickers: Iterable[str]
) -> str:
    """Serializa os fundamentos dos tickers informados, um por linha."""
    selecionados = [t for t in tickers if t in dados]
    if not selecionados:
        return ""
    cabecalhos = [cabecalho for _coluna, cabecalho in _COLUNAS]
    blocos: list[str] = []
    for valores in montar_linhas({t: dados[t] for t in selecionados}):
        ticker = valores[0]
        itens = _itens_compactos(cabecalhos[1:], valores[1:])
        blocos.append(f"[{ticker}] " + "; ".join(itens))
    return "\n".join(blocos)


def montar_contexto_fundamentos(
    dados: Mapping[str, object],
    ticker: str | None,
    watchlist: Iterable[str],
) -> str:
    """Monta o bloco de fundamentos do escopo, ou a orientação de carga."""
    if not dados:
        return ORIENTACAO_SEM_DADOS
    tickers = tickers_do_escopo(dados, ticker, watchlist)
    if not tickers:
        return ORIENTACAO_SEM_DADOS
    return serializar_fundamentos(dados, tickers)
