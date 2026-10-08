"""Trabalho de leitura do cache histórico da evolução dos fundamentos.

A função de trabalho apenas lê o cache histórico do ticker e monta as séries;
a aplicação no painel ocorre na thread do Tk pelo gerenciador de background.
Não há aquisição de rede: a origem é exclusivamente o cache local.
"""

from datetime import date

from flowscope.application.fundamental.evolucao import (
    METODO_FIBONACCI,
    SerieEvolucao,
    definir_janela,
    montar_series,
    selecionar_datas,
)
from flowscope.presentation.gui.background.job import Politica

#: Grupo de exclusão e política da leitura da evolução.
GRUPO = "evolucao"
POLITICA = Politica.LATEST_WINS


def preparar_series(
    store: object | None,
    ticker: str | None,
    *,
    periodo_dias: int = 30,
    metodo: str = METODO_FIBONACCI,
    ancora: date | None = None,
) -> tuple[SerieEvolucao, ...]:
    """Lê ``store.datas``/``historico`` do ticker e monta as séries.

    Restringe as observações à janela do período ancorada em ``ancora``
    (a data de referência; quando ausente, a observação mais recente) e aplica
    o método de amostragem selecionado. É seguro executar na thread de trabalho:
    apenas lê arquivos e monta estruturas de dados, sem tocar em widgets.
    Retorna vazio quando não há ticker, store ou datas em cache.
    """
    if not ticker or store is None:
        return ()
    datas: list[date] = store.datas(ticker)
    selecionadas = _selecionadas_na_janela(
        ticker, datas, ancora, periodo_dias, metodo
    )
    if not selecionadas:
        return ()
    observacoes = store.historico(
        ticker, min(selecionadas), max(selecionadas)
    )
    filtradas = [
        observacao
        for observacao in observacoes
        if observacao.data in selecionadas
    ]
    return tuple(montar_series(filtradas))


def _selecionadas_na_janela(
    ticker: str,
    datas: list[date],
    ancora: date | None,
    periodo_dias: int,
    metodo: str,
) -> set[date]:
    """Recorta a janela do período e aplica o método de amostragem."""
    if not datas:
        return set()
    referencia = ancora if ancora is not None else max(datas)
    janela = definir_janela(datas, referencia, periodo_dias)
    if janela is None:
        return set()
    inicio, fim = janela
    dentro = [data for data in datas if inicio <= data <= fim]
    return set(
        selecionar_datas(
            dentro,
            metodo,
            semente=_semente(ticker, inicio, fim, metodo, len(dentro)),
        )
    )


def _semente(
    ticker: str, inicio: date, fim: date, metodo: str, quantidade: int
) -> str:
    """Semente estável para o sorteio de Monte Carlo entre renders."""
    return f"{ticker}|{inicio.isoformat()}|{fim.isoformat()}|{metodo}|{quantidade}"
