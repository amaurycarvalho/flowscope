"""Trabalho de leitura do cache histórico da evolução dos fundamentos.

A função de trabalho apenas lê o cache histórico do ticker e monta as séries;
a aplicação no painel ocorre na thread do Tk pelo gerenciador de background.
Não há aquisição de rede: a origem é exclusivamente o cache local.
"""

from datetime import date

from flowscope.application.fundamental.evolucao import (
    SerieEvolucao,
    montar_series,
)
from flowscope.presentation.gui.background.job import Politica

#: Grupo de exclusão e política da leitura da evolução.
GRUPO = "evolucao"
POLITICA = Politica.LATEST_WINS


def preparar_series(
    store: object | None, ticker: str | None
) -> tuple[SerieEvolucao, ...]:
    """Lê ``store.datas``/``historico`` do ticker e monta as séries.

    É seguro executar na thread de trabalho: apenas lê arquivos e monta
    estruturas de dados, sem tocar em widgets. Retorna vazio quando não há
    ticker, store ou datas em cache.
    """
    if not ticker or store is None:
        return ()
    datas: list[date] = store.datas(ticker)
    if not datas:
        return ()
    observacoes = store.historico(ticker, datas[0], datas[-1])
    return tuple(montar_series(observacoes))
