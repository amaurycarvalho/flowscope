"""Painel de navegação e pré-visualização dos documentos em cache.

Exibe uma árvore hierárquica (ticker → ano → mês → categoria → arquivos) e
uma caixa de texto somente-leitura com a pré-visualização textual do arquivo
selecionado. A extração de texto ocorre em thread de trabalho e a abertura do
arquivo usa o aplicativo padrão do sistema.
"""

import logging
import queue
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk

from flowscope.infrastructure.document_catalog import (
    CatalogoTicker,
    DocumentCatalog,
    DocumentoArquivo,
)
from flowscope.presentation.gui.charts.document_preview import (
    SEM_TEXTO,
    texto_preview,
)
from flowscope.presentation.gui.document_actions import abrir_no_aplicativo

logger = logging.getLogger("flowscope")

#: Texto exibido enquanto a pré-visualização é extraída em segundo plano.
CARREGANDO = "Carregando…"


class DocumentTreePanel:
    """Árvore de documentos em cache com pré-visualização textual."""

    def __init__(
        self: "DocumentTreePanel",
        parent: tk.Widget,
        *,
        catalog: DocumentCatalog | None = None,
        open_callback: Callable[[Path], None] | None = None,
        status_callback: Callable[[str, str], None] | None = None,
        acquire_callback: Callable[[str], None] | None = None,
        ia_callback: Callable[[], None] | None = None,
        debounce_ms: int = 150,
    ) -> None:
        """Constrói a árvore, a caixa de pré-visualização e os controles."""
        self._catalog = catalog or DocumentCatalog()
        self._open_callback = open_callback or abrir_no_aplicativo
        self._status_callback = status_callback
        self._acquire_callback = acquire_callback
        self._ia_callback = ia_callback
        self._debounce_ms = debounce_ms
        self._itens: dict[str, DocumentoArquivo] = {}
        self._preview_cache: dict[Path, str] = {}
        self._current_ticker: str | None = None
        self._after_id: str | None = None
        self._fila: queue.Queue = queue.Queue()

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
        self._content.add(self._build_tree(), stretch="always")
        self._content.add(self._build_preview(), stretch="always")
        self._content.pack(fill=tk.BOTH, expand=True)

        self._empty_label = tk.Label(
            self._container, text="", fg="gray", justify=tk.CENTER,
        )

    def _build_tree(self: "DocumentTreePanel") -> tk.Frame:
        """Constrói a árvore hierárquica com sua barra de rolagem."""
        quadro = tk.Frame(self._content)
        self._tree = ttk.Treeview(quadro, show="tree")
        rolagem = ttk.Scrollbar(
            quadro, orient=tk.VERTICAL, command=self._tree.yview
        )
        self._tree.configure(yscrollcommand=rolagem.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rolagem.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<Return>", self._on_double_click)
        return quadro

    def _build_preview(self: "DocumentTreePanel") -> tk.Frame:
        """Constrói a caixa de texto somente-leitura da pré-visualização."""
        quadro = tk.Frame(self._content)
        self._preview = tk.Text(
            quadro, wrap=tk.WORD, state=tk.DISABLED, padx=8, pady=8,
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
        """Esvazia a árvore, o cache de pré-visualização e a caixa de texto."""
        self._itens.clear()
        self._preview_cache.clear()
        filhos = self._tree.get_children()
        if filhos:
            self._tree.delete(*filhos)
        self._set_preview_text("")
        self._atualizar_botao_abrir()

    def _popular(
        self: "DocumentTreePanel", catalogo: CatalogoTicker
    ) -> None:
        """Insere a hierarquia do catálogo na árvore."""
        raiz = self._tree.insert("", "end", text=catalogo.ticker, open=True)
        for ano in catalogo.anos:
            no_ano = self._tree.insert(raiz, "end", text=str(ano.ano), open=True)
            for mes in ano.meses:
                no_mes = self._tree.insert(
                    no_ano, "end", text=f"{mes.mes:02d}", open=True
                )
                for categoria in mes.categorias:
                    no_cat = self._tree.insert(
                        no_mes, "end", text=categoria.nome, open=True
                    )
                    self._inserir_arquivos(no_cat, categoria.arquivos)

    def _inserir_arquivos(
        self: "DocumentTreePanel",
        pai: str,
        arquivos: tuple[DocumentoArquivo, ...],
    ) -> None:
        """Insere os arquivos de uma categoria sob o nó informado."""
        for arquivo in arquivos:
            no = self._tree.insert(pai, "end", text=arquivo.nome)
            self._itens[no] = arquivo

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
        """Agenda a pré-visualização e ajusta o botão de abertura."""
        arquivo = self._arquivo_selecionado()
        self._atualizar_botao_abrir()
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
        """Exibe o estado de carregamento e inicia a extração em thread."""
        self._after_id = None
        if arquivo.caminho in self._preview_cache:
            self._mostrar_texto(self._preview_cache[arquivo.caminho])
            return
        self._set_preview_text(CARREGANDO)
        fila: queue.Queue = queue.Queue()
        self._fila = fila
        threading.Thread(
            target=self._extrair, args=(arquivo, fila), daemon=True
        ).start()
        self._agendar_poll(arquivo, fila)

    def _extrair(
        self: "DocumentTreePanel",
        arquivo: DocumentoArquivo,
        fila: queue.Queue,
    ) -> None:
        """Extrai o texto em thread de trabalho e o publica na fila."""
        fila.put(texto_preview(arquivo.caminho))

    def _agendar_poll(
        self: "DocumentTreePanel",
        arquivo: DocumentoArquivo,
        fila: queue.Queue,
    ) -> None:
        """Consome a fila na thread do Tk até o texto estar disponível."""

        def _verificar() -> None:
            try:
                texto = fila.get_nowait()
            except queue.Empty:
                self.frame.after(20, _verificar)
                return
            self._aplicar_preview(arquivo, texto)

        self.frame.after(0, _verificar)

    def _aplicar_preview(
        self: "DocumentTreePanel", arquivo: DocumentoArquivo, texto: str
    ) -> None:
        """Cacheia o texto e o exibe se o arquivo continua selecionado."""
        self._preview_cache[arquivo.caminho] = texto
        if self._arquivo_selecionado() is arquivo:
            self._mostrar_texto(texto)

    def _arquivo_selecionado(self: "DocumentTreePanel") -> DocumentoArquivo | None:
        """Retorna o arquivo do nó selecionado, ou ``None`` para pastas."""
        selecao = self._tree.selection()
        if not selecao:
            return None
        return self._itens.get(selecao[0])

    def _mostrar_texto(self: "DocumentTreePanel", texto: str) -> None:
        """Exibe o texto extraído ou a mensagem de ausência de texto."""
        self._set_preview_text(texto if texto.strip() else SEM_TEXTO)

    def _set_preview_text(self: "DocumentTreePanel", texto: str) -> None:
        """Substitui o conteúdo da caixa de pré-visualização somente-leitura."""
        self._preview.config(state=tk.NORMAL)
        self._preview.delete("1.0", tk.END)
        self._preview.insert("1.0", texto)
        self._preview.config(state=tk.DISABLED)

    def _on_double_click(
        self: "DocumentTreePanel", event: tk.Event | None = None
    ) -> str:
        """Alterna pastas ou abre arquivos no aplicativo padrão."""
        selecao = self._tree.selection()
        if not selecao:
            return "break"
        no = selecao[0]
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
