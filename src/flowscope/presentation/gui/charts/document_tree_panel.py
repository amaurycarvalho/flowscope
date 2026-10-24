"""Painel de navegação e pré-visualização dos documentos em cache.

Exibe uma árvore hierárquica (ticker → ano → mês → categoria → arquivos). Ao
selecionar um agrupamento, mostra uma lista Markdown dos documentos contidos;
ao selecionar um arquivo, mostra o resumo longo seguido do texto integral. A
extração e a geração de resumo ocorrem em thread de trabalho, com descarte de
resultados obsoletos, e o campo de texto é somente-leitura copiável.
"""

import inspect
import logging
import queue
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import simpledialog

from flowscope.application.document_text_port import DocumentTextStore
from flowscope.application.documentos.catalogo import (
    CatalogoDocumentos,
    ConsultarCatalogoUseCase,
)
from flowscope.application.documentos.document_guidance import (
    EntradaGuidanceArvore,
    GuidanceService,
    conteudo_arvore_guidance,
)
from flowscope.application.documentos.document_summary import DocumentSummaryService
from flowscope.application.documentos.document_summary_port import (
    DocumentSummaryStore,
)
from flowscope.application.llm_config_port import LLMConfigPort
from flowscope.application.renda_fixa import (
    ConsultarTitulosUseCase,
    InferenciasRepository,
)
from flowscope.domain.documents import CatalogoTicker, DocumentoArquivo
from flowscope.domain.llm import LLMPort
from flowscope.domain.renda_fixa import ArvoreTitulos
from flowscope.presentation.gui.charts.document_flow_mixin import (
    CARREGANDO,
    GERANDO_RESUMO,
    MAX_TENTATIVAS_SENHA,
    DocumentFlowMixin,
)
from flowscope.presentation.gui.charts.document_grouping import Agrupamento
from flowscope.presentation.gui.charts.document_panel_build_mixin import (
    DocumentPanelBuildMixin,
)
from flowscope.presentation.gui.charts.document_panel_support import (
    resolver_summary,
    resolver_text_store,
    resolver_use_case,
)
from flowscope.presentation.gui.charts.document_titulos_mixin import (
    DocumentTitulosMixin,
)
from flowscope.presentation.gui.document_actions import abrir_no_aplicativo

logger = logging.getLogger("flowscope")

__all__ = ["CARREGANDO", "GERANDO_RESUMO", "DocumentTreePanel"]


class DocumentTreePanel(
    DocumentFlowMixin, DocumentTitulosMixin, DocumentPanelBuildMixin
):
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
        titulos_use_case: ConsultarTitulosUseCase | None = None,
        inferencias: InferenciasRepository | None = None,
        inferencia_pendente_callback: Callable[[str], bool] | None = None,
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
        self._catalogo_uc = resolver_use_case(catalogo_use_case, catalog)
        self._summary = resolver_summary(
            summary_service, summary_store, catalog, llm_factory, llm_available
        )
        self._text_store = resolver_text_store(text_store, catalog)
        self._guidance = guidance_service
        self._titulos_uc = titulos_use_case
        self._inferencias = inferencias
        self._inferencia_pendente_callback = inferencia_pendente_callback
        self._inferencia_pendente = False
        self._titulos_itens: dict[str, object] = {}
        self._titulos_arvore: ArvoreTitulos | None = None
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
        self._guidances: list[EntradaGuidanceArvore] = []
        self._guidance_pendentes: frozenset[Path] = frozenset()
        self._tickers_expandidos: set[str] = set()
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

    def carregar_catalogo(
        self: "DocumentTreePanel", ticker: str | None
    ) -> CatalogoTicker | None:
        """Lê o catálogo do ticker no cache local, sem tocar em widgets."""
        if not ticker:
            return None
        return self._catalogo_uc.executar(ticker)

    def aplicar_catalogo(
        self: "DocumentTreePanel",
        ticker: str | None,
        catalogo: CatalogoTicker | None,
        pendentes_guidance: frozenset[Path] | None = None,
        guidances: list[EntradaGuidanceArvore] | None = None,
        sem_texto: frozenset[Path] = frozenset(),
        titulos: ArvoreTitulos | None = None,
    ) -> None:
        """Aplica o catálogo lido, remontando a árvore na thread do Tk."""
        primeira = ticker not in self._tickers_expandidos
        abertos = None if primeira else self._view.estado_expansao()
        selecionado = self._caminho_selecionado()
        chave = getattr(self._view, "chave_selecionada", lambda: None)()
        self._current_ticker = ticker
        self._titulos_arvore = titulos
        self._limpar_nos()
        self._guidance_pendentes = frozenset(pendentes_guidance or ())
        self._guidances = list(guidances or ())
        self._sem_texto = frozenset(sem_texto)
        if ticker:
            self._tickers_expandidos.add(ticker)
        restaurado = self._montar_ou_vazio(
            ticker, catalogo, titulos, abertos, selecionado, chave
        )
        if not restaurado:
            self._limpar_preview()
        self.refresh_resumir_button()

    def _montar_ou_vazio(
        self: "DocumentTreePanel",
        ticker: str | None,
        catalogo: CatalogoTicker | None,
        titulos: ArvoreTitulos | None,
        abertos: set[tuple] | None,
        selecionado: Path | None,
        chave: str | None,
    ) -> bool:
        """Monta a árvore ou exibe o estado vazio aplicável."""
        if not ticker:
            self._show_empty("Selecione um ticker")
            return False
        if catalogo is None or catalogo.vazio:
            if titulos is None or titulos.vazio:
                self._show_empty(f"Sem documentos em cache para {ticker}")
                return False
            catalogo = CatalogoTicker(ticker)
        return self._reconstruir(
            catalogo, abertos, selecionado, chave
        )

    def _reconstruir(
        self: "DocumentTreePanel",
        catalogo: CatalogoTicker,
        abertos: set[tuple] | None,
        selecionado: Path | None,
        chave: str | None,
    ) -> bool:
        """Remonta a árvore e reaplica expansão e seleção preservadas."""
        self._show_content()
        self._popular(catalogo)
        if abertos is not None:
            self._view.restaurar_expansao(abertos)
        return self._restaurar_selecao(selecionado, chave)

    def update(
        self: "DocumentTreePanel", ticker: str | None
    ) -> None:
        """Recarrega o catálogo de leitura do ticker e remonta a árvore."""
        catalogo = self.carregar_catalogo(ticker)
        pendentes, guidances = self.carregar_guidance(ticker, catalogo)
        sem_texto = self.carregar_ausencia_catalogo(catalogo)
        titulos = self.carregar_titulos(ticker)
        self.definir_inferencia_pendente(
            self.carregar_inferencia_pendente(ticker)
        )
        self.aplicar_catalogo(
            ticker, catalogo, pendentes, guidances, sem_texto, titulos
        )

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
        self._limpar_nos()
        self._limpar_preview()

    def _limpar_nos(self: "DocumentTreePanel") -> None:
        """Esvazia a árvore e os mapas de nós, sem tocar na pré-visualização."""
        self._req_id += 1
        self._view.limpar()
        self._catalogo_atual = None
        self._titulos_itens = {}
        self._guidances = []
        self._guidance_pendentes = frozenset()

    def _limpar_preview(self: "DocumentTreePanel") -> None:
        """Limpa a pré-visualização, o memo de texto e o botão de abrir."""
        self._preview_cache.clear()
        self._set_preview_text("")
        self._atualizar_botao_abrir()

    def _popular(
        self: "DocumentTreePanel", catalogo: CatalogoTicker
    ) -> None:
        """Insere a hierarquia do catálogo na árvore."""
        self._catalogo_atual = catalogo
        self._titulos_itens = getattr(self._view, "titulos", {})
        if "titulos" in inspect.signature(self._view.popular).parameters:
            self._view.popular(
                catalogo, self._guidances, titulos=self._titulos_arvore
            )
        else:
            self._view.popular(catalogo, self._guidances)

    def _caminho_selecionado(self: "DocumentTreePanel") -> Path | None:
        """Retorna o caminho do arquivo selecionado, ou ``None``."""
        arquivo = self._arquivo_selecionado()
        return arquivo.caminho if arquivo is not None else None

    def _restaurar_selecao(
        self: "DocumentTreePanel",
        caminho: Path | None,
        chave: str | None = None,
    ) -> bool:
        """Reseleciona o arquivo ou título e recompõe a pré-visualização."""
        if caminho is None or not self._view.focar_caminho(caminho):
            if chave is None or not self._view.focar_chave(chave):
                return False
            self._on_select()
            return True
        arquivo = self._arquivo_selecionado()
        if arquivo is not None:
            self._agendar_preview(arquivo)
        return True

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
        entrada = self._guidances_folhas.get(no)
        if entrada is not None:
            self._mostrar_guidance(entrada)
            return
        arquivo = self._itens.get(no)
        if arquivo is not None:
            self._agendar_preview(arquivo)

    def _mostrar_guidance(
        self: "DocumentTreePanel", entrada: EntradaGuidanceArvore
    ) -> None:
        """Exibe o texto do guidance e o rótulo curado do RG associado."""
        self._set_preview_text(
            conteudo_arvore_guidance(entrada, self._por_caminho)
        )

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
        """Salta da folha de guidance ao RG ou abre arquivos/pastas."""
        no = self._no_selecionado()
        if no is None:
            return "break"
        entrada = self._guidances_folhas.get(no)
        if entrada is not None:
            self._saltar_para_rg(entrada)
            return "break"
        arquivo = self._itens.get(no)
        if arquivo is None:
            self._tree.item(no, open=not self._tree.item(no, "open"))
            return "break"
        self._abrir(arquivo)
        return "break"

    def _saltar_para_rg(
        self: "DocumentTreePanel", entrada: EntradaGuidanceArvore
    ) -> None:
        """Foca a folha do RG associado, expandindo os ancestrais.

        Sem o documento no catálogo apresentado, não salta nem falha.
        """
        if entrada.caminho_pdf:
            self._view.focar_caminho(Path(entrada.caminho_pdf))

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
        """Reavalia os resumos e notifica o host após trocar o modelo ativo.

        Trocar o modelo ativo reconfigura a IA: o registro de falhas de guidance
        é limpo para que os RGs voltem a ser acionáveis com o novo provedor.
        """
        self.reabilitar_guidance()
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
