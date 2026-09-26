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
from flowscope.application.documentos.document_summary import DocumentSummaryService
from flowscope.application.documentos.document_summary_port import (
    DocumentSummaryStore,
)
from flowscope.application.noticias.catalogo import (
    ConsultarCatalogoNoticiasUseCase,
    NoticiasCatalogo,
)
from flowscope.application.noticias.lote import pendentes_ordenados
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.llm import LLMPort
from flowscope.domain.noticias import (
    SECAO_GERAL,
    CatalogoNoticias,
    apontador_pendente,
)
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
    tem_texto,
    texto_preview,
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
        catalogo_use_case: ConsultarCatalogoNoticiasUseCase | None = None,
        catalog: NoticiasCatalogo | None = None,
        summary_service: DocumentSummaryService | None = None,
        summary_store: DocumentSummaryStore | None = None,
        text_store: DocumentTextStore | None = None,
        baixar_vinculo: Callable[[str], str | None] | None = None,
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
        """Constrói a árvore, a caixa de pré-visualização e os controles.

        O caso de uso do catálogo e as portas chegam por injeção; o painel não
        constrói adaptadores de infraestrutura.
        """
        self._catalogo_uc = self._resolver_use_case(catalogo_use_case, catalog)
        self._summary = self._resolver_summary(
            summary_service, summary_store, catalog, llm_factory, llm_available
        )
        self._text_store = self._resolver_text_store(text_store, catalog)
        self._baixar_vinculo = baixar_vinculo or (lambda _texto: None)
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
        self._catalogo_noticias = None
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

    @staticmethod
    def _resolver_use_case(
        catalogo_use_case: ConsultarCatalogoNoticiasUseCase | None,
        catalog: NoticiasCatalogo | None,
    ) -> ConsultarCatalogoNoticiasUseCase:
        """Resolve o caso de uso do catálogo, construindo-o do repositório."""
        if catalogo_use_case is not None:
            return catalogo_use_case
        if catalog is None:
            raise ValueError(
                "NoticiasPanel exige 'catalogo_use_case' ou 'catalog'."
            )
        return ConsultarCatalogoNoticiasUseCase(catalog)

    @staticmethod
    def _resolver_summary(
        summary_service: DocumentSummaryService | None,
        summary_store: DocumentSummaryStore | None,
        catalog: NoticiasCatalogo | None,
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
                "NoticiasPanel exige 'summary_service' ou "
                "'summary_store' com a raiz de cache."
            )
        return DocumentSummaryService(store, base, llm_factory, llm_available)

    @staticmethod
    def _resolver_text_store(
        text_store: DocumentTextStore | None,
        catalog: NoticiasCatalogo | None,
    ) -> DocumentTextStore:
        """Resolve o store de texto, injetado ou obtido do repositório."""
        if text_store is not None:
            return text_store
        if catalog is None:
            raise ValueError("NoticiasPanel exige 'text_store' ou 'catalog'.")
        return catalog.text_store

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
        catalogo = self._catalogo_uc.secoes()
        if catalogo.vazio:
            self._show_empty("Sem notícias em cache")
        else:
            self._show_content()
            self._popular(catalogo)
        self.refresh_resumir_button()

    def _texto_cacheado(
        self: "NoticiasPanel", arquivo: DocumentoArquivo
    ) -> str | None:
        """Retorna o texto cacheado, invalidando apontadores não resolvidos.

        Um download anterior que falhou deixa no cache o próprio apontador do
        Plantão B3. Para não confiar nele para sempre, o texto é descartado
        quando é um apontador pendente — forçando nova tentativa de resolução.
        Documentos já resolvidos seguem reutilizados.
        """
        texto = super()._texto_cacheado(arquivo)
        if texto is None:
            return texto
        if self._apontador_pendente(arquivo, texto):
            return None
        return texto

    def _apontador_pendente(
        self: "NoticiasPanel", arquivo: DocumentoArquivo, texto: str
    ) -> bool:
        """Indica se o texto é o apontador da "Geral" ainda não resolvido.

        É apontador pendente quando contém uma URL suportada (CVM RAD ou FNET)
        e é idêntico ao corpo atual do ``#conteudoDetalhe``. A comparação evita
        tratar como pendente um documento já resolvido que cite uma URL.
        """
        if getattr(arquivo, "secao", "") != SECAO_GERAL:
            return False
        corpo = texto_preview(arquivo.caminho, SELETOR_CONTEUDO_DETALHE)
        return apontador_pendente(texto, corpo)

    def texto_utilizavel(
        self: "NoticiasPanel", arquivo: DocumentoArquivo, texto: str
    ) -> bool:
        """Indica se o texto serve para resumir (não é apontador pendente).

        O lote usa este gancho para pular notícias cujo documento vinculado não
        foi baixado: elas permanecem pendentes e são tentadas de novo, em vez de
        gerar um resumo a partir do apontador.
        """
        return tem_texto(texto) and not self._apontador_pendente(arquivo, texto)

    def persistir_no_lote(self: "NoticiasPanel") -> bool:
        """Grava cada resumo na thread de trabalho, à prova de interrupção."""
        return True

    def pendentes_ordenados(self: "NoticiasPanel") -> list[DocumentoArquivo]:
        """Retorna as notícias sem resumo por grupo e da mais recente à mais antiga.

        A ordem é determinista e vive na aplicação; a apresentação apenas
        delega os itens em memória.
        """
        return pendentes_ordenados(list(self._itens.values()))

    def _texto_do_arquivo(self: "NoticiasPanel", arquivo: DocumentoArquivo) -> str:
        """Extrai o corpo do artigo, resolvendo o documento vinculado da "Geral".

        O corpo do Plantão B3 é extraído de ``#conteudoDetalhe``. Quando ele é
        apenas um apontador para um documento (notícias "Geral" com URL embutida
        no visualizador da CVM RAD ou do FNET), o texto do documento vinculado
        substitui o apontador; sem URL suportada ou em falha, mantém-se o corpo.
        Roda na thread de trabalho.
        """
        texto = texto_preview(arquivo.caminho, SELETOR_CONTEUDO_DETALHE)
        if getattr(arquivo, "secao", "") != SECAO_GERAL:
            return texto
        return self._baixar_vinculo(texto) or texto

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
