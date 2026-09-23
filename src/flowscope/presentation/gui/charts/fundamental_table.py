"""Painel da tabela fundamentalista da sub-aba Fundamentos.

Renderiza, em um ``ttk.Treeview``, uma linha por ticker da watchlist com as
colunas de identidade, dividendo e — para FIIs elegíveis — as métricas FFO.
Ativos não elegíveis exibem ``N/A`` nas colunas fundamentalistas.

A montagem de colunas e linhas e os formatadores de exibição ficam em módulos
irmãos (:mod:`fundamental_rows` e :mod:`fundamental_formatters`) e são
reexportados aqui para manter a API pública do painel.
"""

import tkinter as tk
from collections.abc import Mapping
from tkinter import ttk

from flowscope.presentation.gui.charts.fundamental_formatters import (
    NA,
    formatar_cnpj,
    formatar_data,
    formatar_dias,
    formatar_inteiro,
    formatar_margem,
    formatar_patrimonio,
    formatar_percentual,
    formatar_preco_tipico,
    formatar_quantidade,
    formatar_ratio,
    formatar_valor,
    rotulo_classe_cotistas,
    rotulo_classe_patrimonio,
    rotulo_classificacao_short,
    rotulo_sub_tipo,
    rotulo_tendencia,
    rotulo_tipo,
)
from flowscope.presentation.gui.charts.fundamental_rows import (
    _COLUNAS,
    _COLUNAS_DIREITA,
    _COLUNAS_FIXAS,
    _COLUNAS_ROLANTES,
    _largura_coluna,
    montar_csv,
    montar_linhas,
)
from flowscope.presentation.gui.widgets.mousewheel import (
    passo_da_roda,
    vincular_roda,
)

__all__ = [
    "NA",
    "FundamentalTablePanel",
    "formatar_cnpj",
    "formatar_data",
    "formatar_dias",
    "formatar_inteiro",
    "formatar_margem",
    "formatar_patrimonio",
    "formatar_percentual",
    "formatar_preco_tipico",
    "formatar_quantidade",
    "formatar_ratio",
    "formatar_valor",
    "montar_csv",
    "montar_linhas",
    "rotulo_classe_cotistas",
    "rotulo_classe_patrimonio",
    "rotulo_classificacao_short",
    "rotulo_sub_tipo",
    "rotulo_tendencia",
    "rotulo_tipo",
]

#: Largura mínima reservada ao painel rolável, limitando o painel congelado.
_LARGURA_MINIMA_ROLANTE = 200


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
        on_row_activated: object | None = None,
        on_ticker_selected: object | None = None,
    ) -> None:
        """Constrói o painel com os dois ``Treeview`` e as barras de rolagem."""
        self.frame = ttk.Frame(parent)
        self._on_widths_changed = on_widths_changed
        self._on_row_activated = on_row_activated
        self._on_ticker_selected = on_ticker_selected
        self._columns = [coluna_id for coluna_id, _cabecalho in _COLUNAS]
        self._columns_fixas = [coluna_id for coluna_id, _ in _COLUNAS_FIXAS]
        self._columns_rolantes = [coluna_id for coluna_id, _ in _COLUNAS_ROLANTES]
        self._syncing_selection = False
        self._ultimo_ticker_notificado: str | None = None
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
        self._tree_fixo.bind("<Double-1>", self._on_row_double_click)
        self._tree_rolavel.bind("<Double-1>", self._on_row_double_click)
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
        vincular_roda(tree, self._tree_rolavel)

    def _on_mousewheel(self: "FundamentalTablePanel", event: object) -> str:
        """Encaminha a roda do mouse para o painel rolável."""
        self._tree_rolavel.yview_scroll(passo_da_roda(event), "units")
        return "break"

    def _on_select_fixo(self: "FundamentalTablePanel", event: object = None) -> None:
        """Espelha a seleção do painel congelado no rolável e notifica o ticker."""
        self._espelhar_selecao(self._tree_fixo, self._tree_rolavel)
        self._notificar_selecao(self._tree_fixo)

    def _on_select_rolavel(
        self: "FundamentalTablePanel", event: object = None
    ) -> None:
        """Espelha a seleção do painel rolável no congelado e notifica o ticker."""
        self._espelhar_selecao(self._tree_rolavel, self._tree_fixo)
        self._notificar_selecao(self._tree_rolavel)

    def _notificar_selecao(self: "FundamentalTablePanel", tree: ttk.Treeview) -> None:
        """Notifica o ticker selecionado uma única vez por mudança."""
        selecionados = tree.selection()
        if not selecionados:
            return
        ticker = selecionados[0]
        if ticker == self._ultimo_ticker_notificado:
            return
        self._ultimo_ticker_notificado = ticker
        if callable(self._on_ticker_selected):
            self._on_ticker_selected(ticker)

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

    def _on_row_double_click(
        self: "FundamentalTablePanel", event: object = None
    ) -> str:
        """Aciona o callback com o ticker da linha clicada."""
        tree = getattr(event, "widget", None)
        if tree is None:
            return "break"
        selecionados = tree.selection()
        if selecionados and callable(self._on_row_activated):
            self._on_row_activated(selecionados[0])
        return "break"

    def get_selected_ticker(self: "FundamentalTablePanel") -> str | None:
        """Retorna o ticker da linha selecionada, ou ``None``."""
        selecionados = self._tree_fixo.selection()
        return selecionados[0] if selecionados else None

    def has_ticker(self: "FundamentalTablePanel", ticker: str) -> bool:
        """Indica se a tabela possui uma linha para o ticker informado."""
        return bool(ticker) and self._tree_fixo.exists(ticker)

    def first_ticker(self: "FundamentalTablePanel") -> str | None:
        """Retorna o ticker da primeira linha da tabela, ou ``None``."""
        filhos = self._tree_fixo.get_children()
        return filhos[0] if filhos else None

    def select_ticker(self: "FundamentalTablePanel", ticker: str) -> None:
        """Seleciona a linha do ticker informado, se existir."""
        if not self.has_ticker(ticker):
            return
        self._tree_fixo.selection_set(ticker)
        self._tree_fixo.focus(ticker)
        self._tree_fixo.see(ticker)
        self._tree_rolavel.see(ticker)

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
        self._ultimo_ticker_notificado = None

    def reset(self: "FundamentalTablePanel") -> None:
        """Limpa o painel exibindo nenhuma linha."""
        self.update({})
