"""Árvore hierárquica de documentos com os mapas de nós.

Constrói o ``Treeview``, popula a raiz do ticker com os ramos Guidance,
Documentos e Direitos e obrigações e mantém os mapas de agrupamento, de
arquivos por nó e o índice reverso caminho → nó.
"""

import tkinter as tk
from collections.abc import Iterable
from pathlib import Path
from tkinter import ttk

from flowscope.application.avaliar_guidance import CATEGORIA_RELATORIO
from flowscope.application.documentos.document_guidance import (
    EntradaGuidanceArvore,
)
from flowscope.domain.documents import (
    CatalogoTicker,
    CategoriaDocumentos,
    DocumentoArquivo,
)
from flowscope.presentation.gui.charts.document_grouping import (
    Agrupamento,
    agrupar_guidance,
)
from flowscope.presentation.gui.widgets.mousewheel import vincular_roda

#: Rótulo do ramo de documentos.
RAMO_DOCUMENTOS = "Documentos"

#: Rótulo do ramo de guidance.
RAMO_GUIDANCE = "Guidance"

#: Rótulo do ramo de direitos e obrigações.
RAMO_DIREITOS = "Direitos e obrigações"


def _tem_relatorio(catalogo: CatalogoTicker) -> bool:
    """Indica se o catálogo tem algum documento da categoria ``Relatorio``."""
    for ano in catalogo.anos:
        for mes in ano.meses:
            for categoria in mes.categorias:
                if categoria.nome == CATEGORIA_RELATORIO:
                    return True
    return False


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
        self.guidances: dict[str, EntradaGuidanceArvore] = {}
        self.por_caminho: dict[Path, DocumentoArquivo] = {}
        self.nos_por_caminho: dict[Path, str] = {}

    def limpar(self: "DocumentTreeView") -> None:
        """Esvazia a árvore e os mapas de nós."""
        self.itens.clear()
        self.grupos.clear()
        self.guidances.clear()
        self.por_caminho.clear()
        self.nos_por_caminho.clear()
        filhos = self.tree.get_children()
        if filhos:
            self.tree.delete(*filhos)

    def popular(
        self: "DocumentTreeView",
        catalogo: CatalogoTicker,
        guidances: Iterable[EntradaGuidanceArvore] = (),
    ) -> None:
        """Insere a raiz do ticker com os ramos Guidance, Documentos e Direitos."""
        raiz = self.tree.insert("", "end", text=catalogo.ticker, open=True)
        self.grupos[raiz] = Agrupamento("ticker", catalogo.ticker)
        if _tem_relatorio(catalogo):
            self._popular_guidance(raiz, list(guidances))
        no_docs = self.tree.insert(raiz, "end", text=RAMO_DOCUMENTOS, open=False)
        self.grupos[no_docs] = Agrupamento("documentos", RAMO_DOCUMENTOS)
        self.popular_catalogo(no_docs, catalogo, abrir=False)
        self._popular_direitos(raiz)

    def _popular_guidance(
        self: "DocumentTreeView",
        raiz: str,
        guidances: list[EntradaGuidanceArvore],
    ) -> None:
        """Insere o ramo Guidance com anos, meses e folhas por entrada."""
        no_ramo = self.tree.insert(raiz, "end", text=RAMO_GUIDANCE, open=False)
        self.grupos[no_ramo] = Agrupamento("guidance", RAMO_GUIDANCE)
        for ano, meses in agrupar_guidance(guidances):
            no_ano = self.tree.insert(no_ramo, "end", text=str(ano), open=False)
            self.grupos[no_ano] = Agrupamento(
                "guidance_ano", str(ano), ano=ano
            )
            for mes, entradas in meses:
                no_mes = self.tree.insert(
                    no_ano, "end", text=f"{mes:02d}", open=False
                )
                self.grupos[no_mes] = Agrupamento(
                    "guidance_mes", f"{mes:02d}", ano=ano, mes=mes
                )
                for entrada in entradas:
                    no_folha = self.tree.insert(
                        no_mes, "end", text=entrada.texto
                    )
                    self.guidances[no_folha] = entrada

    def _popular_direitos(self: "DocumentTreeView", raiz: str) -> None:
        """Insere o ramo placeholder de Direitos e obrigações."""
        no_ramo = self.tree.insert(raiz, "end", text=RAMO_DIREITOS, open=False)
        self.grupos[no_ramo] = Agrupamento("direitos_obrigacoes", RAMO_DIREITOS)
        for tipo, titulo in (("direitos", "Direitos"), ("obrigacoes", "Obrigações")):
            no_sub = self.tree.insert(no_ramo, "end", text=titulo, open=False)
            self.grupos[no_sub] = Agrupamento(tipo, titulo)

    def popular_catalogo(
        self: "DocumentTreeView",
        no_pai: str,
        catalogo: CatalogoTicker,
        *,
        abrir: bool = True,
    ) -> None:
        """Insere a hierarquia ano → mês → categoria sob o nó pai.

        ``abrir`` define se os nós inseridos começam expandidos; o ramo
        Documentos usa ``False`` para exibir a árvore apenas até o primeiro
        nível.
        """
        for ano in catalogo.anos:
            no_ano = self.tree.insert(no_pai, "end", text=str(ano.ano), open=abrir)
            self.grupos[no_ano] = Agrupamento("ano", str(ano.ano), ano=ano.ano)
            for mes in ano.meses:
                no_mes = self.tree.insert(
                    no_ano, "end", text=f"{mes.mes:02d}", open=abrir
                )
                self.grupos[no_mes] = Agrupamento(
                    "mes", f"{mes.mes:02d}", ano=ano.ano, mes=mes.mes
                )
                for categoria in mes.categorias:
                    self._inserir_categoria(
                        no_mes, ano.ano, mes.mes, categoria, abrir=abrir
                    )

    def _inserir_categoria(
        self: "DocumentTreeView",
        no_mes: str,
        ano: int,
        mes: int,
        categoria: CategoriaDocumentos,
        *,
        abrir: bool = True,
    ) -> None:
        """Insere a categoria, seus arquivos e os registra nos mapas."""
        no_cat = self.tree.insert(no_mes, "end", text=categoria.nome, open=abrir)
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
            self.nos_por_caminho[arquivo.caminho] = no

    def estado_expansao(self: "DocumentTreeView") -> set[tuple]:
        """Captura a chave semântica dos nós de grupo abertos."""
        return {
            _chave_grupo(grupo)
            for no, grupo in self.grupos.items()
            if self.tree.item(no, "open")
        }

    def restaurar_expansao(
        self: "DocumentTreeView", abertos: set[tuple]
    ) -> None:
        """Reabre os nós de grupo cuja chave semântica está em ``abertos``."""
        for no, grupo in self.grupos.items():
            if _chave_grupo(grupo) in abertos:
                self.tree.item(no, open=True)

    def no_por_caminho(self: "DocumentTreeView", caminho: Path) -> str | None:
        """Devolve o iid do nó do arquivo, ou ``None`` quando ausente."""
        return self.nos_por_caminho.get(caminho)

    def focar_caminho(self: "DocumentTreeView", caminho: Path) -> bool:
        """Foca o nó do caminho, expandindo os ancestrais e rolando até ele.

        Devolve ``False`` sem alterar a seleção quando o caminho não está na
        árvore apresentada.
        """
        no = self.nos_por_caminho.get(caminho)
        if no is None:
            return False
        self.expandir_ancestrais(no)
        self.tree.selection_set(no)
        self.tree.see(no)
        return True

    def expandir_ancestrais(self: "DocumentTreeView", no: str) -> None:
        """Abre todos os ancestrais do nó, da raiz ao pai imediato."""
        pai = self.tree.parent(no)
        while pai:
            self.tree.item(pai, open=True)
            pai = self.tree.parent(pai)

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


def _chave_grupo(grupo: Agrupamento) -> tuple:
    """Deriva a chave semântica estável de um agrupamento."""
    return (grupo.tipo, grupo.titulo, grupo.ano, grupo.mes, grupo.categoria)
