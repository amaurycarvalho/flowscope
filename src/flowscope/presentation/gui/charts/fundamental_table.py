"""Painel da tabela fundamentalista da sub-aba Fundamentos.

Renderiza, em um ``ttk.Treeview``, uma linha por ticker da watchlist com as
colunas de identidade, dividendo e — para FIIs elegíveis — as métricas FFO.
Ativos não elegíveis exibem ``N/A`` nas colunas fundamentalistas.
"""

import tkinter as tk
from collections.abc import Mapping
from datetime import date
from decimal import Decimal
from enum import Enum
from tkinter import ttk

from flowscope.domain.fii import (
    AnaliseFundamental,
    SubTipoAcao,
    SubTipoFii,
    TipoAtivo,
    classificar_ticker,
)

NA = "N/A"

_COLUNAS = (
    ("ticker", "Ticker"),
    ("nome", "Nome"),
    ("tipo", "Tipo"),
    ("subtipo", "Sub-tipo"),
    ("ultima_data_com", "Última data-com"),
    ("ultimo_dividendo", "Último dividendo"),
    ("tendencia_dividendo", "Tendência do dividendo"),
    ("ffo_yield", "FFO Yield"),
    ("dividend_yield", "Dividend Yield"),
    ("p_ffo", "P/FFO"),
    ("p_vp", "P/VP"),
    ("ffo_trend", "FFO Trend"),
)

_TIPOS = {
    TipoAtivo.ACAO: "Ação",
    TipoAtivo.FII: "FII",
    TipoAtivo.ETF: "ETF",
    TipoAtivo.BDR: "BDR",
    TipoAtivo.DESCONHECIDO: "Desconhecido",
}

_SUB_TIPO_ACAO = {
    SubTipoAcao.ORDINARIA: "Ordinária",
    SubTipoAcao.PREFERENCIAL: "Preferencial",
    SubTipoAcao.ETF: "ETF",
}

_SUB_TIPO_FII = {
    SubTipoFii.TIJOLO: "Tijolo",
    SubTipoFii.PAPEL: "Papel",
    SubTipoFii.HIBRIDO: "Híbrido",
    SubTipoFii.FIAGRO: "Fiagro",
    SubTipoFii.FIINFRA: "Fiinfra",
    SubTipoFii.DESCONHECIDO: "Desconhecido",
}


def rotulo_tipo(tipo: TipoAtivo | None) -> str:
    """Retorna o rótulo amigável de um tipo de ativo."""
    if tipo is None:
        return NA
    return _TIPOS.get(tipo, tipo.name)


def rotulo_sub_tipo(sub_tipo: Enum | None) -> str:
    """Retorna o rótulo amigável de um sub-tipo de ativo."""
    if sub_tipo is None:
        return NA
    if isinstance(sub_tipo, SubTipoFii):
        return _SUB_TIPO_FII.get(sub_tipo, sub_tipo.name)
    if isinstance(sub_tipo, SubTipoAcao):
        return _SUB_TIPO_ACAO.get(sub_tipo, sub_tipo.name)
    return sub_tipo.name


def formatar_data(data: date | None) -> str:
    """Formata uma data no padrão DD/MM/AAAA, ou ``N/A``."""
    if data is None:
        return NA
    return data.strftime("%d/%m/%Y")


def _com_virgula(valor: Decimal, casas: int) -> str:
    """Formata um decimal com vírgula e a quantidade de casas informada."""
    quantizado = valor.quantize(Decimal(1).scaleb(-casas))
    return f"{quantizado:.{casas}f}".replace(".", ",")


def formatar_valor(valor: Decimal | None) -> str:
    """Formata um valor monetário curto com vírgula, ou ``N/A``."""
    if valor is None:
        return NA
    texto = f"{valor:.6f}".rstrip("0").rstrip(".")
    if texto.startswith("."):
        texto = f"0{texto}"
    return texto.replace(".", ",")


def formatar_percentual(valor: Decimal | None, casas: int = 2) -> str:
    """Formata um percentual decimal como ``8,16%``, ou ``N/A``."""
    if valor is None:
        return NA
    return f"{_com_virgula(valor * Decimal(100), casas)}%"


def formatar_ratio(valor: Decimal | None, casas: int = 2) -> str:
    """Formata uma razão como ``12,25x``, ou ``N/A``."""
    if valor is None:
        return NA
    return f"{_com_virgula(valor, casas)}x"


def _linha_analise(ticker: str, analise: AnaliseFundamental) -> tuple[str, ...]:
    """Monta a linha de uma análise fundamentalista completa."""
    classificacao = analise.classificacao
    dividendo = analise.ultimo_dividendo
    metricas = analise.metricas
    ffo_yield = metricas.ffo_yield if metricas else None
    dy = metricas.dividend_yield if metricas else None
    p_ffo = metricas.p_ffo if metricas else None
    p_vp = metricas.p_vp if metricas else None
    tendencia_ffo = metricas.ffo_trend if metricas else None
    return (
        ticker,
        analise.nome or NA,
        rotulo_tipo(classificacao.tipo),
        rotulo_sub_tipo(classificacao.sub_tipo),
        formatar_data(dividendo.data_com),
        formatar_valor(dividendo.valor),
        _rotulo_dividendo(dividendo.tendencia),
        formatar_percentual(ffo_yield, 2),
        formatar_percentual(dy, 1),
        formatar_ratio(p_ffo, 2),
        formatar_ratio(p_vp, 2),
        _rotulo_ffo_trend(tendencia_ffo),
    )


def _linha_sintetica(ticker: str, dados: object) -> tuple[str, ...]:
    """Monta uma linha apenas com a classificação sintática do ticker."""
    classificacao = classificar_ticker(ticker)
    return (
        ticker,
        NA,
        rotulo_tipo(classificacao.tipo),
        rotulo_sub_tipo(classificacao.sub_tipo),
        NA,
        NA,
        NA,
        NA,
        NA,
        NA,
        NA,
        NA,
    )


def montar_linhas(dados: Mapping[str, object]) -> list[tuple[str, ...]]:
    """Transforma os dados por ticker em linhas prontas para a tabela."""
    linhas: list[tuple[str, ...]] = []
    for ticker, payload in dados.items():
        if isinstance(payload, AnaliseFundamental):
            linhas.append(_linha_analise(ticker, payload))
        else:
            linhas.append(_linha_sintetica(ticker, payload))
    return linhas


def _rotulo_dividendo(tendencia: Enum | None) -> str:
    """Retorna o rótulo da tendência do dividendo."""
    if tendencia is None:
        return NA
    return tendencia.value


def _rotulo_ffo_trend(tendencia: Enum | None) -> str:
    """Retorna o rótulo da tendência do FFO."""
    if tendencia is None:
        return NA
    return tendencia.value


class FundamentalTablePanel:
    """Tabela fundamentalista alimentada pela watchlist de tickers."""

    def __init__(self: "FundamentalTablePanel", parent: tk.Widget) -> None:
        """Constrói o painel com o ``Treeview`` e as barras de rolagem."""
        self.frame = ttk.Frame(parent)
        self._columns = [coluna_id for coluna_id, _cabecalho in _COLUNAS]
        self._tree = ttk.Treeview(
            self.frame, columns=self._columns, show="headings"
        )
        for coluna_id, cabecalho in _COLUNAS:
            self._tree.heading(coluna_id, text=cabecalho)
            self._tree.column(coluna_id, width=140, minwidth=80, stretch=False)
        scrollbar_v = ttk.Scrollbar(
            self.frame, orient="vertical", command=self._tree.yview
        )
        scrollbar_h = ttk.Scrollbar(
            self.frame, orient="horizontal", command=self._tree.xview
        )
        self._tree.configure(
            yscrollcommand=scrollbar_v.set,
            xscrollcommand=scrollbar_h.set,
        )
        self._tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_v.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

    def update(self: "FundamentalTablePanel", data: Mapping[str, object]) -> None:
        """Substitui as linhas exibidas pelos dados informados por ticker."""
        for item in self._tree.get_children():
            self._tree.delete(item)
        for linha in montar_linhas(data):
            self._tree.insert("", "end", values=linha)

    def reset(self: "FundamentalTablePanel") -> None:
        """Limpa o painel exibindo nenhuma linha."""
        self.update({})
