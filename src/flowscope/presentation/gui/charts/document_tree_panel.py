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
from dataclasses import dataclass, replace
from pathlib import Path
from tkinter import ttk

from flowscope.application.resumo_documento import (
    ResumirDocumentoUseCase,
    ResumoDocumento,
)
from flowscope.domain.llm import LLMError, LLMPort
from flowscope.infrastructure.document_catalog import (
    CatalogoTicker,
    DocumentCatalog,
    DocumentoArquivo,
)
from flowscope.infrastructure.document_summaries import (
    JsonDocumentSummaryStore,
    chave_documento,
)
from flowscope.infrastructure.llm.config import check_llm_deps, load_llm_config
from flowscope.infrastructure.llm.factory import create_llm_provider
from flowscope.presentation.gui.charts.document_preview import (
    SEM_TEXTO,
    texto_preview,
)
from flowscope.presentation.gui.document_actions import abrir_no_aplicativo
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText

logger = logging.getLogger("flowscope")

#: Texto exibido enquanto a pré-visualização é extraída em segundo plano.
CARREGANDO = "Carregando…"

#: Texto exibido enquanto o resumo é gerado em segundo plano.
GERANDO_RESUMO = "Gerando resumo…"

#: Prefixo da mensagem exibida quando não há resumo disponível.
RESUMO_INDISPONIVEL = "Resumo indisponível."

#: Sufixo da mensagem de indisponibilidade com a LLM configurada.
SUFIXO_LLM_CONFIGURADA = " Clique no documento para análise."

#: Sufixo da mensagem de indisponibilidade sem a LLM configurada.
SUFIXO_LLM_AUSENTE = " Configure a LLM via o botão I.A. e teste a comunicação."

#: Profundidade de cada tipo de agrupamento na hierarquia.
_PROFUNDIDADE = {"ticker": 1, "ano": 2, "mes": 3, "categoria": 4}


def mensagem_indisponivel(llm_configurada: bool) -> str:
    """Monta a mensagem de resumo indisponível conforme a LLM esteja pronta."""
    sufixo = SUFIXO_LLM_CONFIGURADA if llm_configurada else SUFIXO_LLM_AUSENTE
    return RESUMO_INDISPONIVEL + sufixo


def _llm_configurada() -> bool:
    """Indica se há provedor diferente de ``none`` e dependências presentes."""
    try:
        config = load_llm_config()
        return config.get("provider", "none") != "none" and check_llm_deps()
    except Exception:  # configuração ilegível não deve quebrar a interface
        return False


@dataclass(frozen=True)
class _Agrupamento:
    """Payload de um nó de agrupamento da árvore."""

    tipo: str
    titulo: str
    ano: int | None = None
    mes: int | None = None
    categoria: str | None = None


def render_grupo(
    catalogo: CatalogoTicker,
    agrupamento: _Agrupamento,
    por_caminho: dict[Path, DocumentoArquivo],
    mensagem: str,
) -> str:
    """Renderiza a lista Markdown do agrupamento com níveis relativos."""
    linhas: list[str] = []
    base = _PROFUNDIDADE[agrupamento.tipo]
    if agrupamento.tipo == "ticker":
        linhas.append(f"# {catalogo.ticker}")
    for ano in catalogo.anos:
        if agrupamento.ano is not None and ano.ano != agrupamento.ano:
            continue
        if base <= 2:
            linhas.append(f"{'#' * (2 - base + 1)} {ano.ano}")
        for mes in ano.meses:
            if agrupamento.mes is not None and mes.mes != agrupamento.mes:
                continue
            if base <= 3:
                linhas.append(f"{'#' * (3 - base + 1)} {mes.mes:02d}")
            for categoria in mes.categorias:
                if agrupamento.categoria is not None and categoria.nome != agrupamento.categoria:
                    continue
                if base <= 4:
                    linhas.append(f"{'#' * (4 - base + 1)} {categoria.nome}")
                _linhas_arquivos(linhas, categoria.arquivos, por_caminho, mensagem)
    return "\n".join(linhas)


def _linhas_arquivos(
    linhas: list[str],
    arquivos: tuple[DocumentoArquivo, ...],
    por_caminho: dict[Path, DocumentoArquivo],
    mensagem: str,
) -> None:
    """Acrescenta um item de lista por documento, com o resumo curto."""
    for arquivo in arquivos:
        atual = por_caminho.get(arquivo.caminho, arquivo)
        texto = atual.short_summary or mensagem
        linhas.append(f"- {arquivo.nome} — {texto}")


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
        self._summary_store = (
            summary_store
            or getattr(self._catalog, "summary_store", None)
            or JsonDocumentSummaryStore()
        )
        self._llm_factory = llm_factory
        self._llm_available = llm_available
        self._open_callback = open_callback or abrir_no_aplicativo
        self._status_callback = status_callback
        self._acquire_callback = acquire_callback
        self._ia_callback = ia_callback
        self._debounce_ms = debounce_ms
        self._itens: dict[str, DocumentoArquivo] = {}
        self._grupos: dict[str, _Agrupamento] = {}
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
        self._itens.clear()
        self._grupos.clear()
        self._por_caminho.clear()
        self._catalogo_atual = None
        self._preview_cache.clear()
        filhos = self._tree.get_children()
        if filhos:
            self._tree.delete(*filhos)
        self._set_preview_text("")
        self._atualizar_botao_abrir()

    def _popular(
        self: "DocumentTreePanel", catalogo: CatalogoTicker
    ) -> None:
        """Insere a hierarquia do catálogo na árvore e mapeia os agrupamentos."""
        self._catalogo_atual = catalogo
        raiz = self._tree.insert("", "end", text=catalogo.ticker, open=True)
        self._grupos[raiz] = _Agrupamento("ticker", catalogo.ticker)
        for ano in catalogo.anos:
            no_ano = self._tree.insert(raiz, "end", text=str(ano.ano), open=True)
            self._grupos[no_ano] = _Agrupamento("ano", str(ano.ano), ano=ano.ano)
            for mes in ano.meses:
                no_mes = self._tree.insert(
                    no_ano, "end", text=f"{mes.mes:02d}", open=True
                )
                self._grupos[no_mes] = _Agrupamento(
                    "mes", f"{mes.mes:02d}", ano=ano.ano, mes=mes.mes
                )
                for categoria in mes.categorias:
                    no_cat = self._tree.insert(
                        no_mes, "end", text=categoria.nome, open=True
                    )
                    self._grupos[no_cat] = _Agrupamento(
                        "categoria",
                        categoria.nome,
                        ano=ano.ano,
                        mes=mes.mes,
                        categoria=categoria.nome,
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
            self._por_caminho[arquivo.caminho] = arquivo

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

    def _mostrar_grupo(self: "DocumentTreePanel", grupo: _Agrupamento) -> None:
        """Renderiza a lista Markdown do agrupamento selecionado."""
        if self._catalogo_atual is None:
            return
        texto = render_grupo(
            self._catalogo_atual,
            grupo,
            self._por_caminho,
            self._mensagem_indisponivel(),
        )
        self._set_preview_text(texto)

    def _mensagem_indisponivel(self: "DocumentTreePanel") -> str:
        """Retorna a mensagem de indisponibilidade conforme a LLM configurada."""
        return mensagem_indisponivel(self._disponivel())

    def _disponivel(self: "DocumentTreePanel") -> bool:
        """Indica se a geração de resumos está habilitada."""
        if self._llm_available is not None:
            return self._llm_available()
        if self._llm_factory is not None:
            return True
        return _llm_configurada()

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
        if texto is not None and not self._precisa_resumo(arquivo, texto):
            self._mostrar_documento(texto, self._resumo_para_exibir(arquivo, texto))
            return
        self._set_preview_text(GERANDO_RESUMO if self._precisa_resumo(arquivo, texto) else CARREGANDO)
        fila: queue.Queue = queue.Queue()
        self._fila = fila
        threading.Thread(
            target=self._trabalhar,
            args=(arquivo, fila, texto),
            daemon=True,
        ).start()
        self._agendar_poll(arquivo, fila, req)

    def _precisa_resumo(
        self: "DocumentTreePanel", arquivo: DocumentoArquivo, texto: str | None
    ) -> bool:
        """Indica se o documento ainda precisa de geração de resumo."""
        return (
            arquivo.long_summary is None
            and self._disponivel()
            and bool((texto or "").strip())
        )

    def _resumo_para_exibir(
        self: "DocumentTreePanel", arquivo: DocumentoArquivo, texto: str
    ) -> str | None:
        """Resolve o resumo a exibir quando não há geração pendente."""
        if arquivo.long_summary is not None:
            return arquivo.long_summary
        if texto.strip():
            return self._mensagem_indisponivel()
        return None

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
        resumo = self._gerar_resumo(arquivo, texto)
        fila.put((texto, resumo))

    def _gerar_resumo(
        self: "DocumentTreePanel", arquivo: DocumentoArquivo, texto: str
    ) -> ResumoDocumento | None:
        """Gera o resumo do documento, tolerando falhas da LLM."""
        if arquivo.long_summary is not None or not self._disponivel():
            return None
        if not texto.strip():
            return None
        try:
            return ResumirDocumentoUseCase(self._criar_llm()).resumir(texto)
        except LLMError as exc:
            logger.warning("Falha ao resumir documento %s: %s", arquivo.caminho, exc)
            return None
        except Exception as exc:  # falha inesperada não deve derrubar a thread
            logger.warning("Erro inesperado ao resumir %s: %s", arquivo.caminho, exc)
            return None

    def _criar_llm(self: "DocumentTreePanel") -> LLMPort:
        """Cria a porta de completion a partir da factory injetada ou da config."""
        if self._llm_factory is not None:
            return self._llm_factory()
        return create_llm_provider(load_llm_config())

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
        long_summary = self._resumo_para_exibir(arquivo, texto)
        if resumo is not None:
            self._persistir_resumo(arquivo, resumo)
            long_summary = resumo.long_summary
        self._mostrar_documento(texto, long_summary)

    def _persistir_resumo(
        self: "DocumentTreePanel", arquivo: DocumentoArquivo, resumo: ResumoDocumento
    ) -> None:
        """Grava o resumo no store e atualiza o catálogo em memória."""
        self._summary_store.salvar(
            arquivo.ticker,
            self._chave(arquivo),
            resumo.short_summary,
            resumo.long_summary,
        )
        atualizado = replace(
            arquivo,
            short_summary=resumo.short_summary,
            long_summary=resumo.long_summary,
        )
        for no, item in self._itens.items():
            if item.caminho == arquivo.caminho:
                self._itens[no] = atualizado
        self._por_caminho[arquivo.caminho] = atualizado

    def _chave(self: "DocumentTreePanel", arquivo: DocumentoArquivo) -> str:
        """Deriva a chave do documento relativa à raiz de cache."""
        try:
            return chave_documento(arquivo.caminho, self._catalog.base_dir)
        except (TypeError, ValueError):
            return arquivo.nome

    def _no_selecionado(self: "DocumentTreePanel") -> str | None:
        """Retorna o iid do nó selecionado, ou ``None``."""
        selecao = self._tree.selection()
        if not selecao:
            return None
        return selecao[0]

    def _arquivo_selecionado(self: "DocumentTreePanel") -> DocumentoArquivo | None:
        """Retorna o arquivo do nó selecionado, ou ``None`` para pastas."""
        no = self._no_selecionado()
        if no is None:
            return None
        return self._itens.get(no)

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
