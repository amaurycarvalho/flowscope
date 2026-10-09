"""Painel de navegação e pré-visualização dos documentos em cache.

Exibe uma árvore hierárquica (ticker → ano → mês → categoria → arquivos). Ao
selecionar um agrupamento, mostra uma lista Markdown dos documentos contidos;
ao selecionar um arquivo, mostra o resumo longo seguido do texto integral. A
extração e a geração de resumo ocorrem em thread de trabalho, com descarte de
resultados obsoletos, e o campo de texto é somente-leitura copiável.
"""

import logging
import queue
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import simpledialog, ttk

from flowscope.application.document_text_port import DocumentTextStore
from flowscope.application.documentos.catalogo import (
    CatalogoDocumentos,
    ConsultarCatalogoUseCase,
)
from flowscope.application.documentos.document_guidance import GuidanceService
from flowscope.application.documentos.document_summary import DocumentSummaryService
from flowscope.application.documentos.document_summary_port import (
    DocumentSummaryStore,
)
from flowscope.application.llm_config_port import LLMConfigPort
from flowscope.domain.documents import CatalogoTicker, DocumentoArquivo
from flowscope.domain.llm import LLMPort
from flowscope.presentation.gui.charts.document_flow_mixin import (
    CARREGANDO,
    GERANDO_RESUMO,
    MAX_TENTATIVAS_SENHA,
    DocumentFlowMixin,
)
from flowscope.presentation.gui.charts.document_grouping import Agrupamento
from flowscope.presentation.gui.charts.document_tree_view import DocumentTreeView
from flowscope.presentation.gui.document_actions import abrir_no_aplicativo
from flowscope.presentation.gui.llm.model_selector import SeletorModelo
from flowscope.presentation.gui.widgets.mousewheel import vincular_roda
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText
from flowscope.presentation.gui.widgets.tooltip import ToolTip

logger = logging.getLogger("flowscope")

__all__ = ["CARREGANDO", "GERANDO_RESUMO", "DocumentTreePanel"]


class DocumentTreePanel(DocumentFlowMixin):
    """Árvore de documentos em cache com pré-visualização e resumo sob demanda."""

    def __init__(
        self: "DocumentTreePanel",
        parent: tk.Widget,
        *,
        catalogo_use_case: ConsultarCatalogoUseCase | None = None,
        catalog: CatalogoDocumentos | None = None,
        summary_service: DocumentSummaryService | None = None,
        summary_store: DocumentSummaryStore | None = None,
        text_store: DocumentTextStore | None = None,
        guidance_service: GuidanceService | None = None,
        llm_factory: Callable[[], LLMPort] | None = None,
        llm_available: Callable[[], bool] | None = None,
        open_callback: Callable[[Path], None] | None = None,
        status_callback: Callable[[str, str], None] | None = None,
        acquire_callback: Callable[[str], None] | None = None,
        config_callback: Callable[[], None] | None = None,
        config_port: LLMConfigPort | None = None,
        model_changed_callback: Callable[[], None] | None = None,
        resumir_callback: Callable[[], None] | None = None,
        resumir_ativo_callback: Callable[[], bool] | None = None,
        debounce_ms: int = 150,
        senha_max_tentativas: int = MAX_TENTATIVAS_SENHA,
    ) -> None:
        """Constrói a árvore, a caixa de pré-visualização e os controles.

        O caso de uso do catálogo e as portas de resumo/texto chegam por
        injeção; o painel não constrói adaptadores de infraestrutura.
        """
        self._catalogo_uc = self._resolver_use_case(catalogo_use_case, catalog)
        self._summary = self._resolver_summary(
            summary_service, summary_store, catalog, llm_factory, llm_available
        )
        self._text_store = self._resolver_text_store(text_store, catalog)
        self._guidance = guidance_service
        self._open_callback = open_callback or abrir_no_aplicativo
        self._status_callback = status_callback
        self._acquire_callback = acquire_callback
        self._config_callback = config_callback
        self._config_port = config_port
        self._model_changed_callback = model_changed_callback
        self._resumir_callback = resumir_callback
        self._resumir_ativo_callback = resumir_ativo_callback
        self._debounce_ms = debounce_ms
        self._senha_interativa = True
        self._senha_max_tentativas = senha_max_tentativas
        self._itens: dict[str, DocumentoArquivo] = {}
        self._grupos: dict[str, Agrupamento] = {}
        self._por_caminho: dict[Path, DocumentoArquivo] = {}
        self._guidance_pendentes: frozenset[Path] = frozenset()
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

    @staticmethod
    def _resolver_use_case(
        catalogo_use_case: ConsultarCatalogoUseCase | None,
        catalog: CatalogoDocumentos | None,
    ) -> ConsultarCatalogoUseCase:
        """Resolve o caso de uso do catálogo, construindo-o do repositório."""
        if catalogo_use_case is not None:
            return catalogo_use_case
        if catalog is None:
            raise ValueError(
                "DocumentTreePanel exige 'catalogo_use_case' ou 'catalog'."
            )
        return ConsultarCatalogoUseCase(catalog)

    @staticmethod
    def _resolver_summary(
        summary_service: DocumentSummaryService | None,
        summary_store: DocumentSummaryStore | None,
        catalog: CatalogoDocumentos | None,
        llm_factory: Callable[[], LLMPort] | None,
        llm_available: Callable[[], bool] | None,
    ) -> DocumentSummaryService:
        """Resolve o serviço de resumo, injetado ou montado do repositório."""
        if summary_service is not None:
            return summary_service
        store = summary_store
        base = None
        if catalog is not None:
            store = store or catalog.summary_store
            base = catalog.base_dir
        if store is None or base is None:
            raise ValueError(
                "DocumentTreePanel exige 'summary_service' ou "
                "'summary_store' com a raiz de cache."
            )
        return DocumentSummaryService(store, base, llm_factory, llm_available)

    @staticmethod
    def _resolver_text_store(
        text_store: DocumentTextStore | None,
        catalog: CatalogoDocumentos | None,
    ) -> DocumentTextStore:
        """Resolve o store de texto, injetado ou obtido do repositório."""
        if text_store is not None:
            return text_store
        if catalog is None:
            raise ValueError(
                "DocumentTreePanel exige 'text_store' ou 'catalog'."
            )
        return catalog.text_store

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
        self._model_selector = SeletorModelo(
            barra,
            config_port=self._config_port,
            on_config=self._on_configurar,
            on_changed=self._on_model_changed,
        )
        self._model_selector.pack(side=tk.LEFT, padx=2)
        self._resumir_btn = ttk.Button(
            barra, text="Resumir pendentes", command=self._on_resumir,
            state=tk.DISABLED,
        )
        self._resumir_btn.pack(side=tk.LEFT, padx=2)

        ToolTip(self._refresh_btn, "Atualizar a lista de documentos em cache")
        ToolTip(self._open_btn, "Abrir o documento selecionado no aplicativo padrão")
        ToolTip(self._resumir_btn, "Resumir os documentos pendentes com a I.A.")

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
        self._tree.bind("<Button-1>", self._on_click)
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
        self._preview_scrollbar = ttk.Scrollbar(
            quadro, orient=tk.VERTICAL, command=self._preview.yview
        )
        self._preview.configure(yscrollcommand=self._preview_scrollbar.set)
        self._preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vincular_roda(self._preview, self._preview)
        return quadro

    def carregar_catalogo(
        self: "DocumentTreePanel", ticker: str | None
    ) -> CatalogoTicker | None:
        """Lê o catálogo do ticker no cache local.

        Não toca em widgets: é seguro executar na thread de trabalho do job de
        leitura. Retorna ``None`` quando não há ticker apresentado.
        """
        if not ticker:
            return None
        return self._catalogo_uc.executar(ticker)

    def aplicar_catalogo(
        self: "DocumentTreePanel",
        ticker: str | None,
        catalogo: CatalogoTicker | None,
        pendentes_guidance: frozenset[Path] | None = None,
    ) -> None:
        """Aplica o catálogo lido, remontando a árvore na thread do Tk."""
        self._current_ticker = ticker
        self._limpar()
        self._guidance_pendentes = frozenset(pendentes_guidance or ())
        if not ticker:
            self._show_empty("Selecione um ticker")
        elif catalogo is None or catalogo.vazio:
            self._show_empty(f"Sem documentos em cache para {ticker}")
        else:
            self._show_content()
            self._popular(catalogo)
        self.refresh_resumir_button()

    def update(
        self: "DocumentTreePanel", ticker: str | None
    ) -> None:
        """Recarrega o catálogo de leitura do ticker e remonta a árvore.

        A exibição é somente-leitura: nenhuma aquisição é acionada aqui. A
        aquisição de novos documentos ocorre apenas pelo botão "Atualizar".
        """
        catalogo = self.carregar_catalogo(ticker)
        pendentes = self.carregar_pendentes_guidance(ticker, catalogo)
        self.aplicar_catalogo(ticker, catalogo, pendentes)

    def all_buttons(self: "DocumentTreePanel") -> list[tk.Widget]:
        """Retorna os controles do painel para o bloqueio global da interface."""
        return [
            self._refresh_btn,
            self._open_btn,
            *self._model_selector.all_buttons(),
            self._resumir_btn,
        ]

    def texto_atual(self: "DocumentTreePanel") -> str:
        """Retorna o conteúdo atual do campo de pré-visualização."""
        return self._preview.get("1.0", "end-1c")

    def refresh_open_button(self: "DocumentTreePanel") -> None:
        """Reavalia o estado do botão "Abrir documento" conforme a seleção."""
        self._atualizar_botao_abrir()

    def persistir_no_lote(self: "DocumentTreePanel") -> bool:
        """Grava cada resumo na thread de trabalho, à prova de interrupção."""
        return True

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
        self._guidance_pendentes = frozenset()
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

    def _on_click(self: "DocumentTreePanel", event: tk.Event) -> None:
        """Refaz a pré-visualização ao clicar no arquivo já selecionado.

        O ``<<TreeviewSelect>>`` não dispara quando o mesmo nó é clicado de
        novo; isso garante a retentativa automática de extrações não definitivas
        (parcial, falha ou protegida) sem controle dedicado.
        """
        no = self._tree.identify_row(event.y)
        if not no:
            return
        arquivo = self._itens.get(no)
        if arquivo is None:
            return
        selecionado = self._arquivo_selecionado()
        if selecionado is not None and selecionado.caminho == arquivo.caminho:
            self._agendar_preview(arquivo)

    def abrir_habilitado(self: "DocumentTreePanel") -> bool:
        """Indica se o botão "Abrir documento" deve estar habilitado.

        Decisão pura, sem tocar em widgets: verificável sem ``DISPLAY``.
        """
        return self._arquivo_selecionado() is not None

    def _atualizar_botao_abrir(self: "DocumentTreePanel") -> None:
        """Habilita o botão "Abrir documento" somente com arquivo selecionado."""
        self._open_btn.config(
            state=tk.NORMAL if self.abrir_habilitado() else tk.DISABLED
        )

    def _no_selecionado(self: "DocumentTreePanel") -> str | None:
        """Retorna o iid do nó selecionado, ou ``None``."""
        return self._view.selecionado()

    def _arquivo_selecionado(self: "DocumentTreePanel") -> DocumentoArquivo | None:
        """Retorna o arquivo do nó selecionado, ou ``None`` para pastas."""
        return self._view.arquivo_selecionado()

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

    def _on_configurar(self: "DocumentTreePanel") -> None:
        """Aciona o callback de abertura do diálogo de configuração de LLM."""
        if self._config_callback is not None:
            self._config_callback()

    def _on_model_changed(
        self: "DocumentTreePanel", provider: str | None = None
    ) -> None:
        """Reavalia os resumos e notifica o host após trocar o modelo ativo."""
        self.refresh_resumir_button()
        if self._model_changed_callback is not None:
            self._model_changed_callback()

    def _solicitar_senha(self: "DocumentTreePanel", arquivo: DocumentoArquivo) -> str | None:
        """Solicita a senha de um PDF protegido."""
        return simpledialog.askstring(
            "Documento protegido",
            f"Senha do PDF {arquivo.nome}:",
            show="*",
            parent=self.frame,
        )

    def _on_resumir(self: "DocumentTreePanel") -> None:
        """Aciona o callback de resumo em lote dos documentos pendentes."""
        if self._resumir_callback is not None:
            self._resumir_callback()

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
