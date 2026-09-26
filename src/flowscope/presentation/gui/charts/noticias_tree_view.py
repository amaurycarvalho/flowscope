"""Árvore da sub-aba "Notícias" com raiz e categorias de topo.

Estende a árvore de documentos para inserir a raiz "Notícias" e, abaixo dela,
as categorias de topo, reaproveitando a inserção ano → mês → categoria de cada
seção. Mantém o mapa de qual catálogo pertence a cada nó de agrupamento, para
que a pré-visualização renderize a seção correta.
"""

import tkinter as tk

from flowscope.domain.documents import CatalogoTicker
from flowscope.domain.noticias import CatalogoNoticias
from flowscope.presentation.gui.charts.document_grouping import Agrupamento
from flowscope.presentation.gui.charts.document_tree_view import DocumentTreeView


class NoticiasTreeView(DocumentTreeView):
    """Árvore com a raiz "Notícias" e as categorias de topo."""

    def __init__(self: "NoticiasTreeView", parent: tk.Widget) -> None:
        """Constrói a árvore e inicializa o mapa de catálogos por nó."""
        super().__init__(parent)
        self.catalogos_por_no: dict[str, CatalogoTicker] = {}
        self.catalogo_raiz: CatalogoNoticias | None = None

    def limpar(self: "NoticiasTreeView") -> None:
        """Esvazia a árvore e o mapa de catálogos."""
        super().limpar()
        self.catalogos_por_no.clear()
        self.catalogo_raiz = None

    def popular_secoes(self: "NoticiasTreeView", catalogo: CatalogoNoticias) -> None:
        """Insere a raiz, as categorias de topo e a hierarquia de cada uma.

        A árvore é exibida expandida apenas até o primeiro nível: a raiz fica
        aberta e as categorias de topo ficam recolhidas.
        """
        self.catalogo_raiz = catalogo
        raiz = self.tree.insert("", "end", text=catalogo.titulo, open=True)
        self.grupos[raiz] = Agrupamento("raiz", catalogo.titulo)
        for secao in catalogo.secoes:
            if not secao.catalogo.anos:
                continue
            no_secao = self.tree.insert(raiz, "end", text=secao.nome, open=False)
            self.grupos[no_secao] = Agrupamento("ticker", secao.nome)
            self.popular_catalogo(no_secao, secao.catalogo, abrir=False)
            self._registrar_catalogo(no_secao, secao.catalogo)

    def _registrar_catalogo(
        self: "NoticiasTreeView", no: str, catalogo: CatalogoTicker
    ) -> None:
        """Associa o catálogo da seção a todos os nós de agrupamento dela."""
        if no in self.grupos:
            self.catalogos_por_no[no] = catalogo
        for filho in self.tree.get_children(no):
            self._registrar_catalogo(filho, catalogo)
