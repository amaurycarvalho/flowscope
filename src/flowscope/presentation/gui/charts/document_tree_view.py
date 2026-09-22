"""Árvore hierárquica de documentos com os mapas de nós.

Constrói o ``Treeview``, popula a hierarquia ticker → ano → mês → categoria →
arquivo e mantém os mapas de agrupamento e de arquivos por nó e por caminho.
"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from flowscope.infrastructure.document_catalog import (
    CatalogoTicker,
    CategoriaDocumentos,
    DocumentoArquivo,
)
from flowscope.presentation.gui.charts.document_grouping import Agrupamento
from flowscope.presentation.gui.widgets.mousewheel import vincular_roda


class DocumentTreeView:
    """Widget de árvore com os mapas de agrupamentos e arquivos."""

    def __init__(self: "DocumentTreeView", parent: tk.Widget) -> None:
        """Constrói o ``Treeview`` com rolagem e inicializa os mapas."""
        self.frame = tk.Frame(parent)
        self.tree = ttk.Treeview(self.frame, show="tree")
        self.rolagem = ttk.Scrollbar(
            self.frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=self.rolagem.set)
        self.rolagem.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vincular_roda(self.tree, self.tree)
        self.itens: dict[str, DocumentoArquivo] = {}
        self.grupos: dict[str, Agrupamento] = {}
        self.por_caminho: dict[Path, DocumentoArquivo] = {}

    def limpar(self: "DocumentTreeView") -> None:
        """Esvazia a árvore e os mapas de nós."""
        self.itens.clear()
        self.grupos.clear()
        self.por_caminho.clear()
        filhos = self.tree.get_children()
        if filhos:
            self.tree.delete(*filhos)

    def popular(self: "DocumentTreeView", catalogo: CatalogoTicker) -> None:
        """Insere a hierarquia do catálogo e mapeia os agrupamentos."""
        raiz = self.tree.insert("", "end", text=catalogo.ticker, open=True)
        self.grupos[raiz] = Agrupamento("ticker", catalogo.ticker)
        for ano in catalogo.anos:
            no_ano = self.tree.insert(raiz, "end", text=str(ano.ano), open=True)
            self.grupos[no_ano] = Agrupamento("ano", str(ano.ano), ano=ano.ano)
            for mes in ano.meses:
                no_mes = self.tree.insert(
                    no_ano, "end", text=f"{mes.mes:02d}", open=True
                )
                self.grupos[no_mes] = Agrupamento(
                    "mes", f"{mes.mes:02d}", ano=ano.ano, mes=mes.mes
                )
                for categoria in mes.categorias:
                    self._inserir_categoria(no_mes, ano.ano, mes.mes, categoria)

    def _inserir_categoria(
        self: "DocumentTreeView",
        no_mes: str,
        ano: int,
        mes: int,
        categoria: CategoriaDocumentos,
    ) -> None:
        """Insere a categoria, seus arquivos e os registra nos mapas."""
        no_cat = self.tree.insert(no_mes, "end", text=categoria.nome, open=True)
        self.grupos[no_cat] = Agrupamento(
            "categoria",
            categoria.nome,
            ano=ano,
            mes=mes,
            categoria=categoria.nome,
        )
        for arquivo in categoria.arquivos:
            no = self.tree.insert(no_cat, "end", text=arquivo.nome)
            self.itens[no] = arquivo
            self.por_caminho[arquivo.caminho] = arquivo

    def selecionado(self: "DocumentTreeView") -> str | None:
        """Retorna o iid do nó selecionado, ou ``None``."""
        selecao = self.tree.selection()
        if not selecao:
            return None
        return selecao[0]

    def arquivo_selecionado(self: "DocumentTreeView") -> DocumentoArquivo | None:
        """Retorna o arquivo do nó selecionado, ou ``None`` para pastas."""
        no = self.selecionado()
        if no is None:
            return None
        return self.itens.get(no)
