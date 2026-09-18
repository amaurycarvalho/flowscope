"""Painel de navegação e pré-visualização dos documentos em cache.

Exibe uma árvore hierárquica (ticker → ano → mês → categoria → arquivos). Ao
selecionar um agrupamento, mostra uma lista Markdown dos documentos contidos;
ao selecionar um arquivo, mostra o resumo longo seguido do texto integral. A
extração e a geração de resumo ocorrem em thread de trabalho, com descarte de
resultados obsoletos, e o campo de texto é somente-leitura copiável.
"""

import logging
import queue
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk

from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.llm import LLMPort
from flowscope.infrastructure.document_catalog import (
    CatalogoTicker,
    DocumentCatalog,
    DocumentoArquivo,
)
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.presentation.gui.charts.document_grouping import (
    Agrupamento,
    render_grupo,
)
from flowscope.presentation.gui.charts.document_preview import (
    SEM_TEXTO,
    texto_preview,
)
from flowscope.presentation.gui.charts.document_summary import (
    DocumentSummaryService,
)
from flowscope.presentation.gui.charts.document_tree_view import DocumentTreeView
from flowscope.presentation.gui.document_actions import abrir_no_aplicativo
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText

logger = logging.getLogger("flowscope")

#: Texto exibido enquanto a pré-visualização é extraída em segundo plano.
CARREGANDO = "Carregando…"

#: Texto exibido enquanto o resumo é gerado em segundo plano.
GERANDO_RESUMO = "Gerando resumo…"


class DocumentTreePanel:
    """Árvore de documentos em cache com pré-visualização e resumo sob demanda."""

    def __init__(
        self: "DocumentTreePanel",
        parent: tk.Widget,
        *,
        catalog: DocumentCatalog | None = None,
        summary_store: JsonDocumentSummaryStore | None = None,
        llm_factory: Callable[[], LLMPort] | None = None,
        llm_available: Callable[[], bool] | None = None,
        open_callback: Callable[[Path], None] | None = None,
        status_callback: Callable[[str, str], None] | None = None,
        acquire_callback: Callable[[str], None] | None = None,
        ia_callback: Callable[[], None] | None = None,
        debounce_ms: int = 150,
    ) -> None:
        """Constrói a árvore, a caixa de pré-visualização e os controles."""
        self._catalog = catalog or DocumentCatalog()
        store = (
            summary_store
            or getattr(self._catalog, "summary_store", None)
            or JsonDocumentSummaryStore()
        )
        self._summary = DocumentSummaryService(
            store, self._catalog.base_dir, llm_factory, llm_available
        )
        self._open_callback = open_callback or abrir_no_aplicativo
        self._status_callback = status_callback
        self._acquire_callback = acquire_callback
        self._ia_callback = ia_callback
        self._debounce_ms = debounce_ms
        self._itens: dict[str, DocumentoArquivo] = {}
        self._grupos: dict[str, Agrupamento] = {}
        self._por_caminho: dict[Path, DocumentoArquivo] = {}
        self._catalogo_atual: CatalogoTicker | None = None
        self._preview_cache: dict[Path, str] = {}
        self._current_ticker: str | None = None
        self._after_id: str | None = None
        self._fila: queue.Queue = queue.Queue()
        self._req_id = 0

        self.frame = tk.Frame(parent)
        self._build_toolbar()
        self._build_container()
        self.reset()

    def _build_toolbar(self: "DocumentTreePanel") -> None:
        """Constrói a barra com os controles de atualizar e abrir."""
        barra = tk.Frame(self.frame)
        barra.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))
        self._refresh_btn = ttk.Button(
            barra, text="Atualizar", command=self._on_refresh
        )
        self._refresh_btn.pack(side=tk.LEFT, padx=2)
        self._open_btn = ttk.Button(
            barra, text="Abrir documento", command=self._on_open_selected,
            state=tk.DISABLED,
        )
        self._open_btn.pack(side=tk.LEFT, padx=2)
        self._ia_btn = ttk.Button(
            barra, text="I.A.", command=self._on_ia
        )
        self._ia_btn.pack(side=tk.LEFT, padx=2)

    def _build_container(self: "DocumentTreePanel") -> None:
        """Constrói a área de conteúdo com a árvore e a pré-visualização."""
        self._container = tk.Frame(self.frame)
        self._container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._content = tk.PanedWindow(
            self._container, orient=tk.HORIZONTAL,
            sashrelief=tk.RAISED, sashwidth=6,
        )
        self._view = DocumentTreeView(self._content)
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
            self._container, text="", fg="gray", justify=tk.CENTER,
        )

    def _build_preview(self: "DocumentTreePanel") -> tk.Frame:
        """Constrói a caixa de texto somente-leitura da pré-visualização."""
        quadro = tk.Frame(self._content)
        self._preview = ReadonlyText(
            quadro, wrap=tk.WORD, padx=8, pady=8,
        )
        rolagem = ttk.Scrollbar(
            quadro, orient=tk.VERTICAL, command=self._preview.yview
        )
        self._preview.configure(yscrollcommand=rolagem.set)
        self._preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rolagem.pack(side=tk.RIGHT, fill=tk.Y)
        return quadro

    def update(
        self: "DocumentTreePanel", ticker: str | None
    ) -> None:
        """Recarrega o catálogo de leitura do ticker e remonta a árvore.

        A exibição é somente-leitura: nenhuma aquisição é acionada aqui. A
        aquisição de novos documentos ocorre apenas pelo botão "Atualizar".
        """
        self._current_ticker = ticker
        self._limpar()
        if not ticker:
            self._show_empty("Selecione um ticker")
            return
        catalogo = self._catalog.catalogo(ticker)
        if catalogo.vazio:
            self._show_empty(f"Sem documentos em cache para {ticker}")
            return
        self._show_content()
        self._popular(catalogo)

    def all_buttons(self: "DocumentTreePanel") -> list[tk.Widget]:
        """Retorna os botões do painel para o bloqueio global da interface."""
        return [self._refresh_btn, self._open_btn, self._ia_btn]

    def texto_atual(self: "DocumentTreePanel") -> str:
        """Retorna o conteúdo atual do campo de pré-visualização."""
        return self._preview.get("1.0", "end-1c")

    def refresh_open_button(self: "DocumentTreePanel") -> None:
        """Reavalia o estado do botão "Abrir documento" conforme a seleção."""
        self._atualizar_botao_abrir()

    def mostrar_carregando(
        self: "DocumentTreePanel", ticker: str | None = None
    ) -> None:
        """Exibe o estado de carregamento enquanto a aquisição ocorre."""
        self._limpar()
        mensagem = (
            f"Carregando documentos de {ticker}…"
            if ticker
            else "Carregando documentos…"
        )
        self._show_empty(mensagem)

    def reset(self: "DocumentTreePanel") -> None:
        """Limpa a árvore e exibe o estado vazio."""
        self._current_ticker = None
        self._limpar()
        self._show_empty("Selecione um ticker")

    def _limpar(self: "DocumentTreePanel") -> None:
        """Esvazia a árvore, os mapas de nós e a caixa de texto."""
        self._req_id += 1
        self._view.limpar()
        self._catalogo_atual = None
        self._preview_cache.clear()
        self._set_preview_text("")
        self._atualizar_botao_abrir()

    def _popular(
        self: "DocumentTreePanel", catalogo: CatalogoTicker
    ) -> None:
        """Insere a hierarquia do catálogo na árvore."""
        self._catalogo_atual = catalogo
        self._view.popular(catalogo)

    def _show_empty(self: "DocumentTreePanel", mensagem: str) -> None:
        """Exibe a mensagem de estado vazio no lugar do conteúdo."""
        self._content.pack_forget()
        self._empty_label.config(text=mensagem)
        self._empty_label.pack(fill=tk.BOTH, expand=True)

    def _show_content(self: "DocumentTreePanel") -> None:
        """Exibe a árvore e a pré-visualização no lugar do estado vazio."""
        self._empty_label.pack_forget()
        self._content.pack(fill=tk.BOTH, expand=True)

    def _on_select(
        self: "DocumentTreePanel", event: tk.Event | None = None
    ) -> None:
        """Exibe a lista do agrupamento ou agenda a pré-visualização do arquivo."""
        self._req_id += 1
        self._atualizar_botao_abrir()
        no = self._no_selecionado()
        if no is None:
            return
        grupo = self._grupos.get(no)
        if grupo is not None:
            self._mostrar_grupo(grupo)
            return
        arquivo = self._itens.get(no)
        if arquivo is not None:
            self._agendar_preview(arquivo)

    def _atualizar_botao_abrir(self: "DocumentTreePanel") -> None:
        """Habilita o botão "Abrir documento" somente com arquivo selecionado."""
        estado = (
            tk.NORMAL
            if self._arquivo_selecionado() is not None
            else tk.DISABLED
        )
        self._open_btn.config(state=estado)

    def _mostrar_grupo(self: "DocumentTreePanel", grupo: Agrupamento) -> None:
        """Renderiza a lista Markdown do agrupamento selecionado."""
        if self._catalogo_atual is None:
            return
        texto = render_grupo(
            self._catalogo_atual,
            grupo,
            self._por_caminho,
            self._summary.mensagem_indisponivel(),
        )
        self._set_preview_text(texto)

    def _agendar_preview(
        self: "DocumentTreePanel", arquivo: DocumentoArquivo
    ) -> None:
        """Agenda a extração com debounce, cancelando a anterior."""
        if self._after_id is not None:
            try:
                self.frame.after_cancel(self._after_id)
            except tk.TclError:
                pass
        self._after_id = self.frame.after(
            self._debounce_ms, lambda: self._iniciar_preview(arquivo)
        )

    def _iniciar_preview(
        self: "DocumentTreePanel", arquivo: DocumentoArquivo
    ) -> None:
        """Exibe o estado de carregamento e inicia extração/resumo em thread."""
        self._after_id = None
        req = self._req_id
        texto = self._preview_cache.get(arquivo.caminho)
        if texto is not None and not self._summary.precisa_resumo(arquivo, texto):
            self._mostrar_documento(
                texto, self._summary.resumo_para_exibir(arquivo, texto)
            )
            return
        precisa = self._summary.precisa_resumo(arquivo, texto)
        self._set_preview_text(GERANDO_RESUMO if precisa else CARREGANDO)
        fila: queue.Queue = queue.Queue()
        self._fila = fila
        threading.Thread(
            target=self._trabalhar,
            args=(arquivo, fila, texto),
            daemon=True,
        ).start()
        self._agendar_poll(arquivo, fila, req)

    def _trabalhar(
        self: "DocumentTreePanel",
        arquivo: DocumentoArquivo,
        fila: queue.Queue,
        texto_conhecido: str | None,
    ) -> None:
        """Extrai o texto e, se preciso, gera o resumo, publicando na fila."""
        texto = (
            texto_conhecido
            if texto_conhecido is not None
            else texto_preview(arquivo.caminho)
        )
        resumo = self._summary.gerar(arquivo, texto)
        fila.put((texto, resumo))

    def _agendar_poll(
        self: "DocumentTreePanel",
        arquivo: DocumentoArquivo,
        fila: queue.Queue,
        req: int,
    ) -> None:
        """Consome a fila na thread do Tk até o resultado estar disponível."""

        def _verificar() -> None:
            try:
                texto, resumo = fila.get_nowait()
            except queue.Empty:
                self.frame.after(20, _verificar)
                return
            if req != self._req_id:
                return
            self._aplicar_preview(arquivo, texto, resumo)

        self.frame.after(0, _verificar)

    def _aplicar_preview(
        self: "DocumentTreePanel",
        arquivo: DocumentoArquivo,
        texto: str,
        resumo: ResumoDocumento | None = None,
    ) -> None:
        """Cacheia o texto e exibe a pré-visualização se o arquivo seguir selecionado."""
        self._preview_cache[arquivo.caminho] = texto
        if self._arquivo_selecionado() is not arquivo:
            return
        long_summary = self._summary.resumo_para_exibir(arquivo, texto)
        if resumo is not None:
            self._atualizar_resumo(self._summary.persistir(arquivo, resumo))
            long_summary = resumo.long_summary
        self._mostrar_documento(texto, long_summary)

    def _atualizar_resumo(
        self: "DocumentTreePanel", atualizado: DocumentoArquivo
    ) -> None:
        """Atualiza o catálogo em memória com os resumos recém-gerados."""
        for no, item in self._itens.items():
            if item.caminho == atualizado.caminho:
                self._itens[no] = atualizado
        self._por_caminho[atualizado.caminho] = atualizado

    def _no_selecionado(self: "DocumentTreePanel") -> str | None:
        """Retorna o iid do nó selecionado, ou ``None``."""
        return self._view.selecionado()

    def _arquivo_selecionado(self: "DocumentTreePanel") -> DocumentoArquivo | None:
        """Retorna o arquivo do nó selecionado, ou ``None`` para pastas."""
        return self._view.arquivo_selecionado()

    def _mostrar_documento(
        self: "DocumentTreePanel", texto: str, long_summary: str | None
    ) -> None:
        """Compõe a pré-visualização do documento com o resumo longo."""
        corpo = texto if texto.strip() else SEM_TEXTO
        if long_summary:
            self._set_preview_text(f"{long_summary}\n\n---\n\n{corpo}")
        else:
            self._set_preview_text(corpo)

    def _set_preview_text(self: "DocumentTreePanel", texto: str) -> None:
        """Substitui o conteúdo da caixa de pré-visualização somente-leitura."""
        self._preview.delete("1.0", tk.END)
        self._preview.insert("1.0", texto)

    def _on_double_click(
        self: "DocumentTreePanel", event: tk.Event | None = None
    ) -> str:
        """Alterna pastas ou abre arquivos no aplicativo padrão."""
        no = self._no_selecionado()
        if no is None:
            return "break"
        arquivo = self._itens.get(no)
        if arquivo is None:
            self._tree.item(no, open=not self._tree.item(no, "open"))
            return "break"
        self._abrir(arquivo)
        return "break"

    def _on_open_selected(self: "DocumentTreePanel") -> None:
        """Abre o arquivo selecionado, se houver."""
        arquivo = self._arquivo_selecionado()
        if arquivo is not None:
            self._abrir(arquivo)

    def _on_ia(self: "DocumentTreePanel") -> None:
        """Aciona o callback de abertura do diálogo de configuração de LLM."""
        if self._ia_callback is not None:
            self._ia_callback()

    def _abrir(self: "DocumentTreePanel", arquivo: DocumentoArquivo) -> None:
        """Abre o arquivo tolerando falha do aplicativo padrão."""
        try:
            self._open_callback(arquivo.caminho)
        except Exception:  # aplicativo padrão indisponível
            logger.warning(
                "Falha ao abrir documento %s", arquivo.caminho, exc_info=True
            )
            if self._status_callback is not None:
                self._status_callback(
                    f"Não foi possível abrir {arquivo.nome}", "⚠"
                )

    def _on_refresh(self: "DocumentTreePanel") -> None:
        """Aciona a aquisição (se houver) e remonta o catálogo do ticker atual."""
        ticker = self._current_ticker
        if self._acquire_callback is not None and ticker:
            self._acquire_callback(ticker)
            return
        self.update(ticker)
