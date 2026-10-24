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
from flowscope.application.renda_fixa import (
    render_adicionais,
    render_agregado,
    render_ausencia,
    render_data_referencia,
    render_documentos,
    render_geral,
    render_inferencia,
    render_ltv_titulo,
)
from flowscope.domain.documents import (
    CatalogoTicker,
    CategoriaDocumentos,
    DocumentoArquivo,
)
from flowscope.domain.renda_fixa import (
    ArvoreTitulos,
    AusenciaFonte,
    GalhoTipo,
    InferenciaTitulo,
    PapelTitulo,
    TituloAgregado,
    TituloRendaFixa,
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
        self.titulos: dict[str, object] = {}
        self.nos_titulos: dict[str, str] = {}
        self.por_caminho: dict[Path, DocumentoArquivo] = {}
        self.nos_por_caminho: dict[Path, str] = {}

    def limpar(self: "DocumentTreeView") -> None:
        """Esvazia a árvore e os mapas de nós."""
        for mapa in (
            self.itens,
            self.grupos,
            self.guidances,
            getattr(self, "titulos", None),
            getattr(self, "nos_titulos", None),
            self.por_caminho,
            self.nos_por_caminho,
        ):
            if mapa is not None:
                mapa.clear()
        filhos = self.tree.get_children()
        if filhos:
            self.tree.delete(*filhos)

    def popular(
        self: "DocumentTreeView",
        catalogo: CatalogoTicker,
        guidances: Iterable[EntradaGuidanceArvore] = (),
        titulos: ArvoreTitulos | None = None,
    ) -> None:
        """Insere a raiz do ticker com os ramos Guidance, Documentos e Direitos."""
        raiz = self.tree.insert("", "end", text=catalogo.ticker, open=True)
        self.grupos[raiz] = Agrupamento("ticker", catalogo.ticker)
        if _tem_relatorio(catalogo):
            self._popular_guidance(raiz, list(guidances))
        no_docs = self.tree.insert(raiz, "end", text=RAMO_DOCUMENTOS, open=False)
        self.grupos[no_docs] = Agrupamento("documentos", RAMO_DOCUMENTOS)
        self.popular_catalogo(no_docs, catalogo, abrir=False)
        self._popular_direitos(raiz, titulos)

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

    def _popular_direitos(
        self: "DocumentTreeView",
        raiz: str,
        titulos: ArvoreTitulos | None,
    ) -> None:
        """Insere o ramo de Direitos e obrigações, com títulos quando houver."""
        no_ramo = self.tree.insert(raiz, "end", text=RAMO_DIREITOS, open=False)
        self.grupos[no_ramo] = Agrupamento(
            "direitos_obrigacoes", RAMO_DIREITOS, texto=_texto_ramo(titulos)
        )
        if titulos is None or titulos.vazio:
            for tipo, titulo in (
                ("direitos", "Direitos"),
                ("obrigacoes", "Obrigações"),
            ):
                no_sub = self.tree.insert(no_ramo, "end", text=titulo, open=False)
                self.grupos[no_sub] = Agrupamento(tipo, titulo)
            return
        self._inserir_data_referencia(no_ramo, titulos)
        for galho, tipo in (
            (titulos.obrigacoes, "obrigacoes"),
            (titulos.direitos, "direitos"),
        ):
            self._inserir_papel(no_ramo, galho.papel, galho.tipos, tipo)

    def _inserir_data_referencia(
        self: "DocumentTreeView", no_ramo: str, titulos: ArvoreTitulos
    ) -> None:
        """Insere o nó de data de referência e proveniência das fontes."""
        texto = render_data_referencia(
            titulos.data_referencia, titulos.fontes
        )
        no = self.tree.insert(no_ramo, "end", text="data-referencia")
        self.grupos[no] = Agrupamento(
            "data_referencia", "data-referencia", texto=texto
        )

    def _inserir_papel(
        self: "DocumentTreeView",
        no_ramo: str,
        papel: PapelTitulo,
        tipos: tuple[GalhoTipo, ...],
        tipo_grupo: str,
    ) -> None:
        """Insere o sub-ramo do papel e os seus tipos de título."""
        no_papel = self.tree.insert(
            no_ramo, "end", text=papel.rotulo, open=False
        )
        self.grupos[no_papel] = Agrupamento(
            tipo_grupo, papel.rotulo, texto=_resumo_papel(papel, tipos)
        )
        if not tipos:
            self._inserir_placeholder(no_papel, papel)
            return
        no_titulos = self.tree.insert(
            no_papel, "end", text="Títulos", open=False
        )
        self.grupos[no_titulos] = Agrupamento(
            "titulos", "Títulos", texto=_texto_tipos(papel, tipos)
        )
        for galho in tipos:
            self._inserir_tipo(no_titulos, papel, galho)

    def _inserir_placeholder(
        self: "DocumentTreeView", no_papel: str, papel: PapelTitulo
    ) -> None:
        """Insere a indicação de ausência de dados de um papel vazio."""
        mensagem = f"Sem dados de {papel.rotulo}."
        no = self.tree.insert(no_papel, "end", text=mensagem)
        self.grupos[no] = Agrupamento("placeholder", mensagem, texto=mensagem)

    def _inserir_tipo(
        self: "DocumentTreeView",
        no_titulos: str,
        papel: PapelTitulo,
        galho: GalhoTipo,
    ) -> None:
        """Insere um tipo de título com os seus itens."""
        no_tipo = self.tree.insert(
            no_titulos, "end", text=galho.tipo.rotulo, open=False
        )
        chave = f"{papel.segmento}:{galho.tipo.segmento}"
        self.grupos[no_tipo] = Agrupamento(
            "titulo_tipo",
            galho.tipo.rotulo,
            chave=chave,
            texto=_texto_tipo(galho),
        )
        for item in galho.itens:
            self._inserir_item(no_tipo, papel, galho, item)

    def _inserir_item(
        self: "DocumentTreeView",
        no_tipo: str,
        papel: PapelTitulo,
        galho: GalhoTipo,
        item: object,
    ) -> None:
        """Insere um título individual, agregado ou ausência de fonte."""
        if isinstance(item, TituloRendaFixa):
            self._inserir_titulo(no_tipo, papel, galho, item)
            return
        if isinstance(item, InferenciaTitulo):
            self._inserir_inferencia(no_tipo, papel, galho, item)
            return
        if isinstance(item, TituloAgregado):
            no = self.tree.insert(no_tipo, "end", text=item.rotulo)
            chave = f"{papel.segmento}:{galho.tipo.segmento}:agregado"
            self.titulos[no] = item
            self.nos_titulos[chave] = no
            self.grupos[no] = Agrupamento(
                "titulo_agregado", item.rotulo, chave=chave,
                texto=render_agregado(item),
            )
            return
        if isinstance(item, AusenciaFonte):
            no = self.tree.insert(no_tipo, "end", text=item.rotulo)
            chave = f"{papel.segmento}:{galho.tipo.segmento}:sem-fonte"
            self.titulos[no] = item
            self.nos_titulos[chave] = no
            self.grupos[no] = Agrupamento(
                "titulo_sem_fonte", item.rotulo, chave=chave,
                texto=render_ausencia(item),
            )

    def _inserir_titulo(
        self: "DocumentTreeView",
        no_tipo: str,
        papel: PapelTitulo,
        galho: GalhoTipo,
        item: TituloRendaFixa,
    ) -> None:
        """Insere um título individual e registra o nó no mapa de títulos."""
        no = self.tree.insert(no_tipo, "end", text=item.nome_exibicao)
        chave = f"{papel.segmento}:{galho.tipo.segmento}:{item.id}"
        self.titulos[no] = item
        self.nos_titulos[chave] = no
        self.grupos[no] = Agrupamento(
            "titulo_renda_fixa",
            item.nome_exibicao,
            chave=chave,
            texto=_texto_titulo(item),
        )

    def _inserir_inferencia(
        self: "DocumentTreeView",
        no_tipo: str,
        papel: PapelTitulo,
        galho: GalhoTipo,
        item: InferenciaTitulo,
    ) -> None:
        """Insere um item inferido com o rótulo explícito de proveniência."""
        texto = f"{item.nome_exibicao} (inferido pela IA)"
        no = self.tree.insert(no_tipo, "end", text=texto)
        chave = f"{papel.segmento}:{galho.tipo.segmento}:{item.id}"
        self.titulos[no] = item
        self.nos_titulos[chave] = no
        self.grupos[no] = Agrupamento(
            "titulo_inferido",
            texto,
            chave=chave,
            texto=render_inferencia(item),
        )

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

    def chave_selecionada(self: "DocumentTreeView") -> str | None:
        """Retorna a chave semântica de um nó de título selecionado."""
        no = self.selecionado()
        if no is None:
            return None
        grupo = self.grupos.get(no)
        return grupo.chave if grupo is not None else None

    def focar_chave(self: "DocumentTreeView", chave: str) -> bool:
        """Foca o nó de título com a chave semântica informada."""
        no = self.nos_titulos.get(chave)
        if no is None:
            return False
        self.expandir_ancestrais(no)
        self.tree.selection_set(no)
        self.tree.see(no)
        return True


def _texto_ramo(titulos: ArvoreTitulos | None) -> str:
    """Resume o ramo de Direitos e obrigações para a pré-visualização."""
    if titulos is None or titulos.vazio:
        return "# Direitos e obrigações\n\nSem dados de Direitos e Obrigações."
    linhas = ["# Direitos e obrigações", ""]
    for papel, galho in (
        (PapelTitulo.OBRIGACAO, titulos.obrigacoes),
        (PapelTitulo.DIREITO, titulos.direitos),
    ):
        total = sum(len(tipo.itens) for tipo in galho.tipos)
        linhas.append(f"- {papel.rotulo}: {total} item(ns)")
    return "\n".join(linhas)


def _texto_tipos(papel: PapelTitulo, tipos: tuple[GalhoTipo, ...]) -> str:
    """Resume os tipos de um papel para a pré-visualização."""
    linhas = [f"# {papel.rotulo} — Títulos", ""]
    for galho in tipos:
        linhas.append(f"- {galho.tipo.rotulo}: {len(galho.itens)} item(ns)")
    return "\n".join(linhas)


def _texto_tipo(galho: GalhoTipo) -> str:
    """Lista os itens de um tipo com a data de referência disponível."""
    linhas = [f"# {galho.tipo.rotulo}", ""]
    for item in galho.itens:
        nome = str(getattr(item, "nome_exibicao", getattr(item, "rotulo", "")))
        data = getattr(item, "data_referencia", None)
        sufixo = f" — {data.isoformat()}" if data is not None else ""
        linhas.append(f"- {nome}{sufixo}")
    return "\n".join(linhas)


def _resumo_papel(papel: PapelTitulo, tipos: tuple[GalhoTipo, ...]) -> str | None:
    """Resume os tipos e a quantidade de itens de um papel."""
    if not tipos:
        return None
    linhas = [f"# {papel.rotulo}", ""]
    for galho in tipos:
        linhas.append(
            f"- {galho.tipo.rotulo}: {len(galho.itens)} item(ns)"
        )
    return "\n".join(linhas)


def _texto_titulo(item: TituloRendaFixa) -> str:
    """Monta o Markdown de pré-visualização de um título individual."""
    return "\n\n".join(
        (
            render_geral(item),
            render_adicionais(item),
            render_ltv_titulo(item),
            render_documentos(item),
        )
    )


def _chave_grupo(grupo: Agrupamento) -> tuple:
    """Deriva a chave semântica estável de um agrupamento."""
    return (
        grupo.tipo,
        grupo.titulo,
        grupo.ano,
        grupo.mes,
        grupo.categoria,
        grupo.chave,
    )
