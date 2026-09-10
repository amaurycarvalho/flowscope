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
    ClasseCotistas,
    ClassePatrimonio,
    SubTipoAcao,
    SubTipoFii,
    TipoAtivo,
    classificar_exibicao,
    classificar_ticker,
)

NA = "N/A"

_LARGURA_PADRAO = 140


def _largura_coluna(
    widths: Mapping[str, object] | None, coluna_id: str
) -> int:
    """Resolve a largura inicial de uma coluna, com fallback para o padrão."""
    if not widths:
        return _LARGURA_PADRAO
    try:
        largura = int(widths.get(coluna_id, _LARGURA_PADRAO))
    except (TypeError, ValueError):
        return _LARGURA_PADRAO
    return largura if largura > 0 else _LARGURA_PADRAO

_COLUNAS = (
    ("ticker", "Ticker"),
    ("nome", "Nome"),
    ("tipo", "Tipo"),
    ("subtipo", "Sub-tipo"),
    ("ultima_data_com", "Última data-com"),
    ("ultimo_dividendo", "Último dividendo"),
    ("dividendo_anterior", "Dividendo anterior"),
    ("tendencia_dividendo", "Tendência do dividendo"),
    ("ffo_yield", "FFO Yield"),
    ("dividend_yield", "Dividend Yield"),
    ("dividend_payout", "Dividend Payout (DY/FFOY)"),
    ("ffo_trend", "FFO Trend"),
    ("p", "P (Cotação)"),
    ("vp", "VP (VP/Cota)"),
    ("p_ffo", "P/FFO"),
    ("p_vp", "P/VP"),
    ("cotistas", "Nº de cotistas"),
    ("classe_cotistas", "Classe de cotistas"),
    ("patrimonio", "Patrimônio"),
    ("classe_patrimonio", "Classe de patrimônio"),
    ("data_referencia", "Data de referência"),
)

#: Colunas cujo conteúdo é alinhado à direita.
_COLUNAS_DIREITA = frozenset(
    {
        "ultimo_dividendo",
        "dividendo_anterior",
        "ffo_yield",
        "dividend_yield",
        "dividend_payout",
        "p",
        "vp",
        "p_ffo",
        "p_vp",
        "cotistas",
        "patrimonio",
    }
)

_CLASSE_COTISTAS = {
    ClasseCotistas.MICRO: "Micro",
    ClasseCotistas.MUITO_PEQUENO: "Muito pequeno",
    ClasseCotistas.PEQUENO: "Pequeno",
    ClasseCotistas.MEDIO: "Médio",
    ClasseCotistas.GRANDE: "Grande",
    ClasseCotistas.MUITO_GRANDE: "Muito grande",
    ClasseCotistas.GIGANTE: "Gigante",
}

_CLASSE_PATRIMONIO = {
    ClassePatrimonio.MICRO: "Micro",
    ClassePatrimonio.PEQUENO: "Pequeno",
    ClassePatrimonio.MEDIO: "Médio",
    ClassePatrimonio.GRANDE: "Grande",
    ClassePatrimonio.MUITO_GRANDE: "Muito grande",
    ClassePatrimonio.GIGANTE: "Gigante",
}

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


def formatar_inteiro(valor: int | None) -> str:
    """Formata um inteiro com separador de milhar brasileiro, ou ``N/A``."""
    if valor is None:
        return NA
    return f"{valor:,}".replace(",", ".")


def formatar_patrimonio(valor: Decimal | None) -> str:
    """Formata o patrimônio líquido de forma legível (mi/bi), ou ``N/A``."""
    if valor is None:
        return NA
    if valor >= Decimal(1000000000):
        return f"R$ {_com_virgula(valor / Decimal(1000000000), 2)} bi"
    if valor >= Decimal(1000000):
        return f"R$ {_com_virgula(valor / Decimal(1000000), 2)} mi"
    return f"R$ {_agrupar(valor, 2)}"


def _agrupar(valor: Decimal, casas: int) -> str:
    """Formata um decimal com separador de milhar e vírgula decimal."""
    quantizado = valor.quantize(Decimal(1).scaleb(-casas))
    texto = f"{quantizado:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def rotulo_classe_cotistas(classe: ClasseCotistas | None) -> str:
    """Retorna o rótulo amigável da classe por número de cotistas."""
    if classe is None:
        return NA
    return _CLASSE_COTISTAS.get(classe, classe.name)


def rotulo_classe_patrimonio(classe: ClassePatrimonio | None) -> str:
    """Retorna o rótulo amigável da classe por tamanho patrimonial."""
    if classe is None:
        return NA
    return _CLASSE_PATRIMONIO.get(classe, classe.name)


def _payout(
    dividend_yield: Decimal | None, ffo_yield: Decimal | None
) -> Decimal | None:
    """Calcula o Dividend Payout como ``DY / FFOY``, ou ``None``."""
    if dividend_yield is None or ffo_yield is None or ffo_yield == 0:
        return None
    return dividend_yield / ffo_yield


def _linha_analise(ticker: str, analise: AnaliseFundamental) -> tuple[str, ...]:
    """Monta a linha de uma análise fundamentalista completa."""
    classificacao = analise.classificacao
    exibicao = analise.classificacao_exibicao
    if exibicao is None:
        exibicao = classificar_exibicao(discriminador=None, fallback=classificacao)
    tipo = exibicao.tipo
    sub_tipo = exibicao.sub_tipo
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
        tipo,
        sub_tipo or NA,
        formatar_data(dividendo.data_com),
        formatar_valor(dividendo.valor),
        formatar_valor(dividendo.valor_anterior),
        _rotulo_dividendo(dividendo.tendencia),
        formatar_percentual(ffo_yield, 2),
        formatar_percentual(dy, 1),
        formatar_percentual(_payout(dy, ffo_yield), 1),
        _rotulo_ffo_trend(tendencia_ffo),
        formatar_valor(analise.cotacao),
        formatar_valor(analise.vp_cota),
        formatar_ratio(p_ffo, 2),
        formatar_ratio(p_vp, 2),
        formatar_inteiro(analise.cotistas),
        rotulo_classe_cotistas(analise.classe_cotistas),
        formatar_patrimonio(analise.patrimonio),
        rotulo_classe_patrimonio(analise.classe_patrimonio),
        formatar_data(analise.data_referencia),
    )


def _linha_sintetica(ticker: str, dados: object) -> tuple[str, ...]:
    """Monta uma linha apenas com a classificação sintática do ticker."""
    classificacao = classificar_ticker(ticker)
    exibicao = classificar_exibicao(discriminador=None, fallback=classificacao)
    return (
        ticker,
        NA,
        exibicao.tipo,
        exibicao.sub_tipo or NA,
        NA,
        NA,
        NA,
        NA,
        NA,
        NA,
        NA,
        NA,
        NA,
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


def montar_csv(dados: Mapping[str, object], delimiter: str = ";") -> str:
    """Monta o CSV da tabela fundamentalista, com cabeçalho e uma linha por ticker."""
    linhas = [delimiter.join(cabecalho for _coluna, cabecalho in _COLUNAS)]
    linhas.extend(delimiter.join(linha) for linha in montar_linhas(dados))
    return "\n".join(linhas)


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

    def __init__(
        self: "FundamentalTablePanel",
        parent: tk.Widget,
        widths: Mapping[str, object] | None = None,
        on_widths_changed: object | None = None,
    ) -> None:
        """Constrói o painel com o ``Treeview`` e as barras de rolagem."""
        self.frame = ttk.Frame(parent)
        self._columns = [coluna_id for coluna_id, _cabecalho in _COLUNAS]
        self._on_widths_changed = on_widths_changed
        self._tree = ttk.Treeview(
            self.frame, columns=self._columns, show="headings"
        )
        for coluna_id, cabecalho in _COLUNAS:
            self._tree.heading(coluna_id, text=cabecalho)
            self._tree.column(
                coluna_id,
                width=_largura_coluna(widths, coluna_id),
                minwidth=80,
                stretch=False,
                anchor="e" if coluna_id in _COLUNAS_DIREITA else "w",
            )
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
        self._tree.bind("<ButtonRelease-1>", self._on_column_resized, add="+")
        self._last_widths = self.get_column_widths()

    def get_column_widths(self: "FundamentalTablePanel") -> dict[str, int]:
        """Retorna a largura atual de cada coluna, indexada pelo id."""
        return {
            coluna_id: int(self._tree.column(coluna_id, "width"))
            for coluna_id in self._columns
        }

    def _on_column_resized(self: "FundamentalTablePanel", event: object = None) -> None:
        """Notifica o callback quando a largura das colunas muda."""
        atuais = self.get_column_widths()
        if atuais == self._last_widths:
            return
        self._last_widths = atuais
        if callable(self._on_widths_changed):
            self._on_widths_changed(atuais)

    def update(self: "FundamentalTablePanel", data: Mapping[str, object]) -> None:
        """Substitui as linhas exibidas pelos dados informados por ticker."""
        for item in self._tree.get_children():
            self._tree.delete(item)
        for linha in montar_linhas(data):
            self._tree.insert("", "end", values=linha)

    def reset(self: "FundamentalTablePanel") -> None:
        """Limpa o painel exibindo nenhuma linha."""
        self.update({})
