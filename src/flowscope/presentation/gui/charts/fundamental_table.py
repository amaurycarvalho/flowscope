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
    TIPO_EXIBICAO_FII,
    AnaliseFundamental,
    ClasseCotistas,
    ClassePatrimonio,
    ClassificacaoExibicao,
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
    ("p", "P (Cotação)"),
    ("preco_tipico", "Preço Típico"),
    ("p_pt", "P / PT"),
    ("vp", "VP (VP/Cota)"),
    ("p_vp", "P/VP"),
    ("p_l", "P/L"),
    ("dividend_yield", "Dividend Yield"),
    ("ultima_data_com", "Última data-com"),
    ("ultimo_dividendo", "Último dividendo"),
    ("dividendo_anterior", "Dividendo anterior"),
    ("tendencia_dividendo", "Tendência do dividendo"),
    ("ffo_yield", "FFO Yield"),
    ("dividend_payout", "Dividend Payout (DY/FFOY)"),
    ("ffo_trend", "FFO Trend"),
    ("p_ffo", "P/FFO"),
    ("cotistas", "Nº de cotistas"),
    ("classe_cotistas", "Classe de cotistas"),
    ("patrimonio", "Patrimônio"),
    ("classe_patrimonio", "Classe de patrimônio"),
    ("data_referencia", "Data de referência"),
    ("informacoes_adicionais", "Informações adicionais"),
    ("dados_fiscais", "Dados fiscais"),
)

#: Colunas congeladas à esquerda da tabela (identidade da linha).
_COLUNAS_FIXAS = _COLUNAS[:2]

#: Colunas roláveis horizontalmente.
_COLUNAS_ROLANTES = _COLUNAS[2:]

#: Largura mínima reservada ao painel rolável, limitando o painel congelado.
_LARGURA_MINIMA_ROLANTE = 200

#: Colunas cujo conteúdo é alinhado à direita.
_COLUNAS_DIREITA = frozenset(
    {
        "ultimo_dividendo",
        "dividendo_anterior",
        "ffo_yield",
        "dividend_yield",
        "dividend_payout",
        "p",
        "preco_tipico",
        "p_pt",
        "vp",
        "p_ffo",
        "p_vp",
        "p_l",
        "cotistas",
        "patrimonio",
    }
)

#: Rótulos descritivos compartilhados pelas tendências do FFO e do dividendo.
_ROTULOS_TENDENCIA = {
    "FORTE_ALTA": "Forte Alta",
    "ALTA": "Leve Alta",
    "ESTAVEL": "Estável",
    "QUEDA": "Leve Queda",
    "FORTE_QUEDA": "Forte Queda",
}

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
    """Formata um valor monetário curto com vírgula e 2 casas, ou ``N/A``."""
    if valor is None:
        return NA
    return _com_virgula(valor, 2)


def formatar_percentual(valor: Decimal | None, casas: int = 2) -> str:
    """Formata um percentual decimal como ``8,16%``, ou ``N/A``."""
    if valor is None:
        return NA
    return f"{_com_virgula(valor * Decimal(100), casas)}%"


def formatar_preco_tipico(valor: Decimal | None) -> str:
    """Formata o Preço Típico com separador de milhar e 2 casas, ou ``N/A``."""
    if valor is None:
        return NA
    return _agrupar(valor, 2)


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


def formatar_cnpj(valor: str | None) -> str:
    """Formata um CNPJ como ``99.999.999/9999-99``, ou ``N/A``."""
    if not valor:
        return NA
    digitos = "".join(caractere for caractere in valor if caractere.isdigit())
    if len(digitos) != 14:
        return valor.strip()
    return (
        f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/"
        f"{digitos[8:12]}-{digitos[12:]}"
    )


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


def _itens_imoveis(analise: AnaliseFundamental) -> list[str]:
    """Monta os itens de imóveis, omitindo-os quando não há quantidade."""
    if not analise.qtd_imoveis:
        return []
    itens = [f"Qtd Imóveis {formatar_inteiro(analise.qtd_imoveis)}"]
    if analise.cap_rate is not None:
        itens.append(f"Cap Rate {formatar_percentual(analise.cap_rate, 2)}")
    if analise.vacancia_media is not None:
        itens.append(
            f"Vacância Média {formatar_percentual(analise.vacancia_media, 2)}"
        )
    return itens


def _itens_indicadores_acao(analise: AnaliseFundamental) -> list[str]:
    """Monta os indicadores de ação exibidos em Informações adicionais."""
    itens: list[str] = []
    if analise.lpa is not None:
        itens.append(f"LPA {formatar_valor(analise.lpa)}")
    if analise.roe is not None:
        itens.append(f"ROE {formatar_percentual(analise.roe, 2)}")
    if analise.roic is not None:
        itens.append(f"ROIC {formatar_percentual(analise.roic, 2)}")
    return itens


def _itens_indexadores(analise: AnaliseFundamental) -> list[str]:
    """Monta os percentuais por indexador disponíveis do FII."""
    return [
        f"{rotulo} {formatar_percentual(valor, 2)}"
        for rotulo, valor in analise.indexadores.items()
        if valor is not None
    ]


#: Separador dos itens concatenados nas colunas adicionais.
_SEPARADOR_ITENS = " | "


def _informacoes_adicionais(
    analise: AnaliseFundamental, exibicao: ClassificacaoExibicao
) -> str:
    """Concatena os itens de Informações adicionais, ou ``N/A`` quando vazio."""
    if exibicao.tipo == TIPO_EXIBICAO_FII:
        itens = _itens_imoveis(analise)
        itens.extend(_itens_indexadores(analise))
    else:
        itens = _itens_indicadores_acao(analise)
    return _SEPARADOR_ITENS.join(itens) if itens else NA


def _item_identidade(
    rotulo: str, nome: str | None, cnpj: str | None
) -> str | None:
    """Monta ``Rótulo Nome (CNPJ)`` omitindo as partes ausentes."""
    partes: list[str] = []
    if nome:
        partes.append(nome)
    if cnpj:
        partes.append(f"({formatar_cnpj(cnpj)})")
    if not partes:
        return None
    return f"{rotulo} {' '.join(partes)}"


def _dados_fiscais(
    analise: AnaliseFundamental, exibicao: ClassificacaoExibicao
) -> str:
    """Concatena os itens de Dados fiscais, ou ``N/A`` quando vazio."""
    itens: list[str] = []
    if analise.cnpj:
        itens.append(f"CNPJ {formatar_cnpj(analise.cnpj)}")
    if exibicao.tipo == TIPO_EXIBICAO_FII:
        administrador = _item_identidade(
            "Administrador", analise.nome_administrador, analise.cnpj_administrador
        )
        if administrador is not None:
            itens.append(administrador)
        gestor = _item_identidade(
            "Gestor", analise.nome_gestor, analise.cnpj_gestor
        )
        if gestor is not None:
            itens.append(gestor)
    return _SEPARADOR_ITENS.join(itens) if itens else NA


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
        formatar_valor(analise.cotacao),
        formatar_preco_tipico(analise.preco_tipico),
        formatar_percentual(analise.pct_preco_tipico, 2),
        formatar_valor(analise.vp_cota),
        formatar_ratio(p_vp, 2),
        formatar_ratio(analise.p_l, 2),
        formatar_percentual(dy, 1),
        formatar_data(dividendo.data_com),
        formatar_valor(dividendo.valor),
        formatar_valor(dividendo.valor_anterior),
        rotulo_tendencia(dividendo.tendencia),
        formatar_percentual(ffo_yield, 2),
        formatar_percentual(_payout(dy, ffo_yield), 2),
        rotulo_tendencia(tendencia_ffo),
        formatar_ratio(p_ffo, 2),
        formatar_inteiro(analise.cotistas),
        rotulo_classe_cotistas(analise.classe_cotistas),
        formatar_patrimonio(analise.patrimonio),
        rotulo_classe_patrimonio(analise.classe_patrimonio),
        formatar_data(analise.data_referencia),
        _informacoes_adicionais(analise, exibicao),
        _dados_fiscais(analise, exibicao),
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
        *(NA for _ in range(len(_COLUNAS) - 4)),
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


def rotulo_tendencia(tendencia: Enum | None) -> str:
    """Retorna o rótulo descritivo de uma tendência (FFO ou dividendo)."""
    if tendencia is None:
        return NA
    return _ROTULOS_TENDENCIA.get(tendencia.value, tendencia.value)


class FundamentalTablePanel:
    """Tabela fundamentalista alimentada pela watchlist de tickers.

    A tabela é composta por dois ``ttk.Treeview`` sincronizados: um painel
    congelado com as colunas ``Ticker`` e ``Nome`` e um painel rolável com as
    demais colunas. Ambos compartilham a barra de rolagem vertical.
    """

    def __init__(
        self: "FundamentalTablePanel",
        parent: tk.Widget,
        widths: Mapping[str, object] | None = None,
        on_widths_changed: object | None = None,
    ) -> None:
        """Constrói o painel com os dois ``Treeview`` e as barras de rolagem."""
        self.frame = ttk.Frame(parent)
        self._on_widths_changed = on_widths_changed
        self._columns = [coluna_id for coluna_id, _cabecalho in _COLUNAS]
        self._columns_fixas = [coluna_id for coluna_id, _ in _COLUNAS_FIXAS]
        self._columns_rolantes = [coluna_id for coluna_id, _ in _COLUNAS_ROLANTES]
        self._syncing_selection = False
        self._largura_fixo_atual = -1

        self._frame_fixo = ttk.Frame(self.frame)
        self._tree_fixo = ttk.Treeview(
            self._frame_fixo,
            columns=self._columns_fixas,
            show="headings",
            selectmode="browse",
        )
        for coluna_id, cabecalho in _COLUNAS_FIXAS:
            self._configurar_coluna(self._tree_fixo, coluna_id, cabecalho, widths)
        self._tree_fixo.grid(row=0, column=0, sticky="nsew")

        self._frame_rolavel = ttk.Frame(self.frame)
        self._tree_rolavel = ttk.Treeview(
            self._frame_rolavel,
            columns=self._columns_rolantes,
            show="headings",
            selectmode="browse",
        )
        for coluna_id, cabecalho in _COLUNAS_ROLANTES:
            self._configurar_coluna(
                self._tree_rolavel, coluna_id, cabecalho, widths
            )
        self._tree_rolavel.grid(row=0, column=0, sticky="nsew")

        self._scrollbar_v = ttk.Scrollbar(
            self.frame, orient="vertical", command=self._on_vscroll
        )
        self._scrollbar_h = ttk.Scrollbar(
            self._frame_rolavel,
            orient="horizontal",
            command=self._tree_rolavel.xview,
        )
        self._tree_rolavel.configure(
            yscrollcommand=self._on_yscroll,
            xscrollcommand=self._scrollbar_h.set,
        )
        self._scrollbar_h.grid(row=1, column=0, sticky="ew")

        self._espacador = ttk.Frame(
            self._frame_fixo, height=self._scrollbar_h.winfo_reqheight()
        )
        self._espacador.grid(row=1, column=0, sticky="ew")

        self._divisor = ttk.Separator(self.frame, orient="vertical")
        self._frame_fixo.grid(row=0, column=0, sticky="nsew")
        self._divisor.grid(row=0, column=1, sticky="ns")
        self._frame_rolavel.grid(row=0, column=2, sticky="nsew")
        self._scrollbar_v.grid(row=0, column=3, sticky="ns")

        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=0)
        self.frame.columnconfigure(1, weight=0)
        self.frame.columnconfigure(2, weight=1)
        self._frame_fixo.rowconfigure(0, weight=1)
        self._frame_fixo.columnconfigure(0, weight=1)
        self._frame_fixo.grid_propagate(False)
        self._frame_rolavel.rowconfigure(0, weight=1)
        self._frame_rolavel.columnconfigure(0, weight=1)

        for tree in (self._tree_fixo, self._tree_rolavel):
            tree.bind("<ButtonRelease-1>", self._on_column_resized, add="+")
            self._vincular_roda(tree)
        self._tree_fixo.bind("<<TreeviewSelect>>", self._on_select_fixo)
        self._tree_rolavel.bind("<<TreeviewSelect>>", self._on_select_rolavel)
        self.frame.bind("<Configure>", self._on_frame_configure, add="+")

        self._last_widths = self.get_column_widths()
        self._ajustar_largura_fixo(self._last_widths)

    @staticmethod
    def _configurar_coluna(
        tree: ttk.Treeview,
        coluna_id: str,
        cabecalho: str,
        widths: Mapping[str, object] | None,
    ) -> None:
        """Configura cabeçalho, largura e alinhamento de uma coluna."""
        tree.heading(coluna_id, text=cabecalho)
        tree.column(
            coluna_id,
            width=_largura_coluna(widths, coluna_id),
            minwidth=80,
            stretch=False,
            anchor="e" if coluna_id in _COLUNAS_DIREITA else "w",
        )

    def _on_vscroll(self: "FundamentalTablePanel", *args: object) -> None:
        """Move os dois ``Treeview`` conforme o comando da barra vertical."""
        self._tree_rolavel.yview(*args)
        self._tree_fixo.yview(*args)

    def _on_yscroll(
        self: "FundamentalTablePanel", first: str, last: str
    ) -> None:
        """Atualiza a barra vertical e alinha o painel congelado."""
        self._scrollbar_v.set(first, last)
        self._tree_fixo.yview_moveto(float(first))

    def _vincular_roda(self: "FundamentalTablePanel", tree: ttk.Treeview) -> None:
        """Associa os eventos de roda do mouse do painel ao rolável."""
        tree.bind("<MouseWheel>", self._on_mousewheel, add="+")
        tree.bind("<Button-4>", self._on_mousewheel, add="+")
        tree.bind("<Button-5>", self._on_mousewheel, add="+")

    def _on_mousewheel(self: "FundamentalTablePanel", event: object) -> str:
        """Encaminha a roda do mouse para o painel rolável."""
        numero = getattr(event, "num", None)
        delta = getattr(event, "delta", 0)
        if numero == 4:
            passo = -1
        elif numero == 5:
            passo = 1
        else:
            passo = -1 if delta > 0 else 1
        self._tree_rolavel.yview_scroll(passo, "units")
        return "break"

    def _on_select_fixo(self: "FundamentalTablePanel", event: object = None) -> None:
        """Espelha a seleção do painel congelado no rolável."""
        self._espelhar_selecao(self._tree_fixo, self._tree_rolavel)

    def _on_select_rolavel(
        self: "FundamentalTablePanel", event: object = None
    ) -> None:
        """Espelha a seleção do painel rolável no congelado."""
        self._espelhar_selecao(self._tree_rolavel, self._tree_fixo)

    def _espelhar_selecao(
        self: "FundamentalTablePanel",
        origem: ttk.Treeview,
        destino: ttk.Treeview,
    ) -> None:
        """Copia a linha selecionada de um painel para o outro."""
        if self._syncing_selection:
            return
        selecionados = origem.selection()
        if tuple(destino.selection()) == tuple(selecionados):
            return
        self._syncing_selection = True
        try:
            for item in destino.selection():
                if item not in selecionados:
                    destino.selection_remove(item)
            if selecionados:
                destino.selection_set(selecionados[0])
                destino.focus(selecionados[0])
        finally:
            self._syncing_selection = False

    def get_column_widths(self: "FundamentalTablePanel") -> dict[str, int]:
        """Retorna a largura atual de cada coluna, indexada pelo id."""
        larguras = {
            coluna_id: int(self._tree_fixo.column(coluna_id, "width"))
            for coluna_id in self._columns_fixas
        }
        larguras.update(
            {
                coluna_id: int(self._tree_rolavel.column(coluna_id, "width"))
                for coluna_id in self._columns_rolantes
            }
        )
        return larguras

    def _on_column_resized(self: "FundamentalTablePanel", event: object = None) -> None:
        """Notifica o callback quando a largura das colunas muda."""
        atuais = self.get_column_widths()
        self._ajustar_largura_fixo(atuais)
        if atuais == self._last_widths:
            return
        self._last_widths = atuais
        if callable(self._on_widths_changed):
            self._on_widths_changed(atuais)

    def _on_frame_configure(
        self: "FundamentalTablePanel", event: object = None
    ) -> None:
        """Recalcula a fronteira quando o painel muda de tamanho."""
        self._ajustar_largura_fixo()

    def _ajustar_largura_fixo(
        self: "FundamentalTablePanel",
        widths: Mapping[str, int] | None = None,
    ) -> None:
        """Ajusta a largura do painel congelado à soma das colunas fixas."""
        larguras = widths if widths is not None else self.get_column_widths()
        soma = sum(larguras[coluna_id] for coluna_id in self._columns_fixas)
        disponivel = self.frame.winfo_width()
        if disponivel > 1:
            limite = max(0, disponivel - _LARGURA_MINIMA_ROLANTE)
            soma = min(soma, limite)
        if soma != self._largura_fixo_atual:
            self._frame_fixo.configure(width=soma)
            self._largura_fixo_atual = soma

    def update(self: "FundamentalTablePanel", data: Mapping[str, object]) -> None:
        """Substitui as linhas exibidas pelos dados informados por ticker."""
        for tree in (self._tree_fixo, self._tree_rolavel):
            for item in tree.get_children():
                tree.delete(item)
        for linha in montar_linhas(data):
            iid = linha[0]
            self._tree_fixo.insert("", "end", iid=iid, values=linha[:2])
            self._tree_rolavel.insert("", "end", iid=iid, values=linha[2:])

    def reset(self: "FundamentalTablePanel") -> None:
        """Limpa o painel exibindo nenhuma linha."""
        self.update({})
