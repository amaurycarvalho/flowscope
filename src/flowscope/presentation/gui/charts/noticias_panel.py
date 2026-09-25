"""Painel de navegação e pré-visualização das notícias em cache.

Sub-aba "Notícias" da Análise Geral: árvore (ano → mês → agência → artigos),
pré-visualização do texto do artigo, resumo por LLM e os botões "Atualizar",
"Abrir", "I.A." e "Resumir pendentes". A abertura usa a URL do artigo no
navegador padrão; artigos sem texto extraível exibem uma mensagem informativa.
"""

import logging
import queue
import tkinter as tk
from collections.abc import Callable
from datetime import date, datetime, timezone
from pathlib import Path
from tkinter import ttk

from flowscope.application.document_text_port import DocumentTextStore
from flowscope.domain.llm import LLMPort
from flowscope.infrastructure.b3.noticias_aquisicao import SECAO_GERAL
from flowscope.infrastructure.b3.noticias_catalogo import (
    CatalogoNoticias,
    NoticiasCatalog,
)
from flowscope.infrastructure.b3.noticias_vinculo import baixar_conteudo_vinculado
from flowscope.infrastructure.document_catalog import DocumentoArquivo
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.infrastructure.document_texts import JsonDocumentTextStore
from flowscope.presentation.gui.charts.document_flow_mixin import (
    CARREGANDO,
    GERANDO_RESUMO,
    DocumentFlowMixin,
)
from flowscope.presentation.gui.charts.document_grouping import (
    Agrupamento,
    render_grupo,
)
from flowscope.presentation.gui.charts.document_preview import (
    SELETOR_CONTEUDO_DETALHE,
    texto_preview,
)
from flowscope.presentation.gui.charts.document_summary import (
    DocumentSummaryService,
)
from flowscope.presentation.gui.charts.noticias_tree_view import NoticiasTreeView
from flowscope.presentation.gui.document_actions import abrir_url
from flowscope.presentation.gui.widgets.mousewheel import vincular_roda
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText

logger = logging.getLogger("flowscope")

__all__ = ["CARREGANDO", "GERANDO_RESUMO", "NoticiasPanel"]


def _hoje() -> date:
    """Retorna a data corrente em UTC, usada como período padrão."""
    return datetime.now(timezone.utc).date()


class NoticiasPanel(DocumentFlowMixin):
    """Árvore de notícias em cache com pré-visualização e resumo sob demanda."""

    def __init__(
        self: "NoticiasPanel",
        parent: tk.Widget,
        *,
        catalog: NoticiasCatalog | None = None,
        summary_store: JsonDocumentSummaryStore | None = None,
        text_store: DocumentTextStore | None = None,
        llm_factory: Callable[[], LLMPort] | None = None,
        llm_available: Callable[[], bool] | None = None,
        open_callback: Callable[[str], None] | None = None,
        status_callback: Callable[[str, str], None] | None = None,
        acquire_callback: Callable[[], None] | None = None,
        ia_callback: Callable[[], None] | None = None,
        resumir_callback: Callable[[], None] | None = None,
        resumir_ativo_callback: Callable[[], bool] | None = None,
        reference_date_provider: Callable[[], date] | None = None,
        debounce_ms: int = 150,
    ) -> None:
        """Constrói a árvore, a caixa de pré-visualização e os controles."""
        self._catalog = catalog or NoticiasCatalog()
        base = self._catalog.base_dir
        store = (
            summary_store
            or getattr(self._catalog, "summary_store", None)
            or JsonDocumentSummaryStore(cache_dir=base)
        )
        self._summary = DocumentSummaryService(store, base, llm_factory, llm_available)
        self._text_store: DocumentTextStore = (
            text_store
            or getattr(self._catalog, "text_store", None)
            or JsonDocumentTextStore(cache_dir=base)
        )
        self._open_callback = open_callback or abrir_url
        self._status_callback = status_callback
        self._acquire_callback = acquire_callback
        self._ia_callback = ia_callback
        self._resumir_callback = resumir_callback
        self._resumir_ativo_callback = resumir_ativo_callback
        self._reference_date_provider = reference_date_provider or _hoje
        self._debounce_ms = debounce_ms
        self._itens: dict[str, DocumentoArquivo] = {}
        self._grupos: dict[str, object] = {}
        self._por_caminho: dict[Path, DocumentoArquivo] = {}
        self._catalogo_noticias: CatalogoNoticias | None = None
        self._catalogo_selecionado = None
        self._preview_cache: dict[Path, str] = {}
        self._reference_date: date | None = None
        self._after_id: str | None = None
        self._fila: queue.Queue = queue.Queue()
        self._req_id = 0

        self.frame = tk.Frame(parent)
        self._build_toolbar()
        self._build_container()
        self.reset()

    def _build_toolbar(self: "NoticiasPanel") -> None:
        """Constrói a barra com os controles de atualizar e abrir."""
        barra = tk.Frame(self.frame)
        barra.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))
        self._refresh_btn = ttk.Button(
            barra, text="Atualizar", command=self._on_refresh
        )
        self._refresh_btn.pack(side=tk.LEFT, padx=2)
        self._open_btn = ttk.Button(
            barra, text="Abrir", command=self._on_open_selected, state=tk.DISABLED
        )
        self._open_btn.pack(side=tk.LEFT, padx=2)
        self._ia_btn = ttk.Button(barra, text="I.A.", command=self._on_ia)
        self._ia_btn.pack(side=tk.LEFT, padx=2)
        self._resumir_btn = ttk.Button(
            barra,
            text="Resumir pendentes",
            command=self._on_resumir,
            state=tk.DISABLED,
        )
        self._resumir_btn.pack(side=tk.LEFT, padx=2)

    def _build_container(self: "NoticiasPanel") -> None:
        """Constrói a área de conteúdo com a árvore e a pré-visualização."""
        self._container = tk.Frame(self.frame)
        self._container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._content = tk.PanedWindow(
            self._container, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=6
        )
        self._view = NoticiasTreeView(self._content)
        self._tree = self._view.tree
        self._itens = self._view.itens
        self._grupos = self._view.grupos
        self._por_caminho = self._view.por_caminho
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<Return>", self._on_double_click)
        self._content.add(self._view.frame, stretch="always")
        self._content.add(self._build_preview(), stretch="always")
        self._content.pack(fill=tk.BOTH, expand=True)

        self._empty_label = tk.Label(
            self._container, text="", fg="gray", justify=tk.CENTER
        )

    def _build_preview(self: "NoticiasPanel") -> tk.Frame:
        """Constrói a caixa de texto somente-leitura da pré-visualização."""
        quadro = tk.Frame(self._content)
        self._preview = ReadonlyText(quadro, wrap=tk.WORD, padx=8, pady=8)
        self._preview_scrollbar = ttk.Scrollbar(
            quadro, orient=tk.VERTICAL, command=self._preview.yview
        )
        self._preview.configure(yscrollcommand=self._preview_scrollbar.set)
        self._preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vincular_roda(self._preview, self._preview)
        return quadro

    def update(self: "NoticiasPanel", reference_date: date) -> None:
        """Remonta a árvore a partir do cache local.

        A exibição é somente-leitura e lê apenas o índice de metadados e o
        conteúdo em cache: nenhuma consulta à B3 é feita aqui. A listagem e a
        aquisição de novos artigos ocorrem apenas pelo botão "Atualizar". A
        data de referência é guardada para o fluxo de aquisição.
        """
        self._reference_date = reference_date
        self._limpar()
        catalogo = self._catalog.secoes(reference_date)
        if catalogo.vazio:
            self._show_empty("Sem notícias em cache")
        else:
            self._show_content()
            self._popular(catalogo)
        self.refresh_resumir_button()

    def _texto_do_arquivo(self: "NoticiasPanel", arquivo: DocumentoArquivo) -> str:
        """Extrai o corpo do artigo, resolvendo o documento vinculado da "Geral".

        O corpo do Plantão B3 é extraído de ``#conteudoDetalhe``. Quando ele é
        apenas um apontador para um documento (notícias "Geral" com URL embutida),
        o conteúdo vinculado é baixado e anexado ao texto; sem URL suportada ou
        em falha, mantém-se apenas o corpo. Roda na thread de trabalho.
        """
        texto = texto_preview(arquivo.caminho, SELETOR_CONTEUDO_DETALHE)
        if getattr(arquivo, "secao", "") != SECAO_GERAL:
            return texto
        vinculado = baixar_conteudo_vinculado(texto)
        if not vinculado:
            return texto
        return f"{texto}\n\n---\n\n{vinculado}".strip()

    def all_buttons(self: "NoticiasPanel") -> list[tk.Widget]:
        """Retorna os botões do painel para o bloqueio global da interface."""
        return [self._refresh_btn, self._open_btn, self._ia_btn, self._resumir_btn]

    def texto_atual(self: "NoticiasPanel") -> str:
        """Retorna o conteúdo atual do campo de pré-visualização."""
        return self._preview.get("1.0", "end-1c")

    def refresh_open_button(self: "NoticiasPanel") -> None:
        """Reavalia o estado do botão "Abrir" conforme a seleção."""
        self._atualizar_botao_abrir()

    def mostrar_carregando(self: "NoticiasPanel") -> None:
        """Exibe o estado de carregamento enquanto a aquisição ocorre."""
        self._limpar()
        self._show_empty("Carregando notícias…")

    def reset(self: "NoticiasPanel") -> None:
        """Limpa a árvore e exibe o estado vazio inicial."""
        self._reference_date = None
        self._limpar()
        self._show_empty("Clique em Atualizar para buscar notícias")

    def _limpar(self: "NoticiasPanel") -> None:
        """Esvazia a árvore, os mapas de nós e a caixa de texto."""
        self._req_id += 1
        self._view.limpar()
        self._catalogo_noticias = None
        self._preview_cache.clear()
        self._set_preview_text("")
        self._atualizar_botao_abrir()

    def _popular(self: "NoticiasPanel", catalogo: CatalogoNoticias) -> None:
        """Insere a raiz e as categorias de topo na árvore."""
        self._catalogo_noticias = catalogo
        self._view.popular_secoes(catalogo)

    def _show_empty(self: "NoticiasPanel", mensagem: str) -> None:
        """Exibe a mensagem de estado vazio no lugar do conteúdo."""
        self._content.pack_forget()
        self._empty_label.config(text=mensagem)
        self._empty_label.pack(fill=tk.BOTH, expand=True)

    def _show_content(self: "NoticiasPanel") -> None:
        """Exibe a árvore e a pré-visualização no lugar do estado vazio."""
        self._empty_label.pack_forget()
        self._content.pack(fill=tk.BOTH, expand=True)

    def _on_select(self: "NoticiasPanel", event: tk.Event | None = None) -> None:
        """Exibe a lista do agrupamento ou agenda a pré-visualização do artigo."""
        self._req_id += 1
        self._atualizar_botao_abrir()
        no = self._no_selecionado()
        if no is None:
            return
        grupo = self._grupos.get(no)
        if grupo is not None:
            self._catalogo_selecionado = self._view.catalogos_por_no.get(no)
            self._mostrar_grupo(grupo)
            return
        arquivo = self._itens.get(no)
        if arquivo is not None:
            self._agendar_preview(arquivo)

    def _mostrar_grupo(self: "NoticiasPanel", grupo: Agrupamento) -> None:
        """Renderiza a raiz com todas as seções ou uma seção selecionada."""
        if grupo.tipo == "raiz":
            texto = self._render_raiz()
        elif self._catalogo_selecionado is not None:
            texto = render_grupo(
                self._catalogo_selecionado,
                grupo,
                self._por_caminho,
                self._summary.mensagem_indisponivel(),
            )
        else:
            return
        self._set_preview_text(texto)

    def _render_raiz(self: "NoticiasPanel") -> str:
        """Concatena a lista Markdown de todas as categorias com itens."""
        catalogo = self._catalogo_noticias
        if catalogo is None:
            return ""
        mensagem = self._summary.mensagem_indisponivel()
        return "\n\n".join(
            render_grupo(
                secao.catalogo,
                Agrupamento("ticker", secao.nome),
                self._por_caminho,
                mensagem,
            )
            for secao in catalogo.secoes
            if secao.catalogo.anos
        )

    def _atualizar_botao_abrir(self: "NoticiasPanel") -> None:
        """Habilita o botão "Abrir" somente com notícia com URL selecionada."""
        arquivo = self._arquivo_selecionado()
        tem_url = arquivo is not None and bool(getattr(arquivo, "url", None))
        self._open_btn.config(state=tk.NORMAL if tem_url else tk.DISABLED)

    def _no_selecionado(self: "NoticiasPanel") -> str | None:
        """Retorna o iid do nó selecionado, ou ``None``."""
        return self._view.selecionado()

    def _arquivo_selecionado(self: "NoticiasPanel") -> DocumentoArquivo | None:
        """Retorna o artigo do nó selecionado, ou ``None`` para pastas."""
        return self._view.arquivo_selecionado()

    def _on_double_click(self: "NoticiasPanel", event: tk.Event | None = None) -> str:
        """Alterna pastas ou abre o artigo no navegador padrão."""
        no = self._no_selecionado()
        if no is None:
            return "break"
        arquivo = self._itens.get(no)
        if arquivo is None:
            self._tree.item(no, open=not self._tree.item(no, "open"))
            return "break"
        self._abrir(arquivo)
        return "break"

    def _on_open_selected(self: "NoticiasPanel") -> None:
        """Abre o artigo selecionado, se houver."""
        arquivo = self._arquivo_selecionado()
        if arquivo is not None:
            self._abrir(arquivo)

    def _on_ia(self: "NoticiasPanel") -> None:
        """Aciona o callback de abertura do diálogo de configuração de LLM."""
        if self._ia_callback is not None:
            self._ia_callback()

    def _on_resumir(self: "NoticiasPanel") -> None:
        """Aciona o callback de resumo em lote dos itens pendentes."""
        if self._resumir_callback is not None:
            self._resumir_callback()

    def _abrir(self: "NoticiasPanel", arquivo: DocumentoArquivo) -> None:
        """Abre a URL do artigo no navegador, tolerando falha."""
        url = getattr(arquivo, "url", None)
        if not url:
            self._status("Notícia sem URL para abrir.", "⚠")
            return
        try:
            self._open_callback(url)
        except Exception:  # navegador padrão indisponível
            logger.warning("Falha ao abrir notícia %s", url, exc_info=True)
            self._status(f"Não foi possível abrir {arquivo.nome}", "⚠")

    def _on_refresh(self: "NoticiasPanel") -> None:
        """Aciona a aquisição (se houver) e remonta as notícias do período."""
        if self._acquire_callback is not None:
            self._acquire_callback()
            return
        self.update(self._reference_date or self._reference_date_provider())

    def _status(self: "NoticiasPanel", msg: str, icon: str = "") -> None:
        """Repassa uma mensagem para a barra de status, quando houver callback."""
        if self._status_callback is not None:
            self._status_callback(msg, icon)
