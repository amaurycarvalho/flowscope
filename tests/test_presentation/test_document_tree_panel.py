"""Testes do painel de documentos, do preview e da abertura de arquivos."""

import os
import queue
import time
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import ttk
from unittest.mock import MagicMock

import pytest

from flowscope.infrastructure.document_catalog import DocumentCatalog
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.domain.llm import LLMCommunicationError
from flowscope.presentation.gui import app_actions, document_actions
from flowscope.presentation.gui.app_actions import ActionsMixin
from flowscope.presentation.gui.documentos_job import (
    MENSAGEM_PROGRESSO,
    DocumentosJob,
)
from flowscope.presentation.gui.app_tab_actions import TabActionsMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.app_tabs import (
    ENABLED_TABS,
    TAB_CONFIGS,
    TAB_CONTENT,
)
from flowscope.presentation.gui.charts import document_preview
from flowscope.presentation.gui.charts.document_preview import (
    SEM_TEXTO,
    texto_de_html,
    texto_de_pdf,
    texto_preview,
)
from flowscope.presentation.gui.charts.document_tree_panel import (
    CARREGANDO,
    DocumentTreePanel,
    mensagem_indisponivel,
)
from flowscope.presentation.gui.controller import FlowScopeController
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


@pytest.fixture(autouse=True)
def _sem_llm_por_padrao(monkeypatch):
    """Torna a disponibilidade da LLM determinística nos testes do painel."""
    monkeypatch.setattr(
        "flowscope.presentation.gui.charts.document_tree_panel._llm_configurada",
        lambda: False,
    )


def _touch(caminho: Path, conteudo: bytes = b"x") -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(conteudo)


def _catalogo(tmp_path: Path) -> DocumentCatalog:
    _touch(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
    _touch(
        tmp_path
        / "documentos-relevantes"
        / "ALZR11"
        / "2026"
        / "02"
        / "assembleia"
        / "20.pdf"
    )
    return DocumentCatalog(cache_dir=tmp_path)


def _catalogo_com_html(tmp_path: Path) -> DocumentCatalog:
    _touch(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
    _touch(
        tmp_path / "informe-mensal" / "ALZR11" / "2026" / "02" / "20.html",
        b"<html><body>Conteudo do informe</body></html>",
    )
    return DocumentCatalog(cache_dir=tmp_path)


def _pump(root: tk.Tk, condicao, timeout: float = 2.0) -> bool:
    limite = time.time() + timeout
    while time.time() < limite:
        root.update()
        if condicao():
            return True
        time.sleep(0.01)
    return condicao()


def _no_arquivo(painel: DocumentTreePanel, nome: str) -> str:
    for iid, arquivo in painel._itens.items():
        if arquivo.nome == nome:
            return iid
    raise AssertionError(f"arquivo {nome} não encontrado na árvore")


def _no_grupo(painel: DocumentTreePanel, tipo: str, titulo: str | None = None) -> str:
    for iid, grupo in painel._grupos.items():
        if grupo.tipo == tipo and (titulo is None or grupo.titulo == titulo):
            return iid
    raise AssertionError(f"agrupamento {tipo}/{titulo} não encontrado")


class _LLMFake:
    """Porta de LLM que registra chamadas e pode bloquear até ser liberada."""

    def __init__(self, resposta: str = "", liberar=None) -> None:
        self.resposta = resposta
        self.liberar = liberar
        self.chamadas: list[list[dict]] = []

    def complete(self, messages: list[dict], system_prompt=None) -> str:
        self.chamadas.append(messages)
        if self.liberar is not None:
            self.liberar.wait(2.0)
        return self.resposta


class TestPreview:
    def test_texto_de_html(self):
        assert "Título" in texto_de_html("<html><body><h1>Título</h1></body></html>")

    def test_texto_de_html_vazio(self):
        assert texto_de_html("") == ""

    def test_texto_de_pdf_invalido_retorna_vazio(self):
        assert texto_de_pdf(b"nao e pdf") == ""

    def test_texto_preview_html(self):
        assert texto_preview(Path("doc.html")) == ""

    def test_texto_preview_despacha_pdf(self, tmp_path, monkeypatch):
        caminho = tmp_path / "doc.pdf"
        caminho.write_bytes(b"%PDF-1.4")
        monkeypatch.setattr(
            document_preview, "texto_de_pdf", lambda _dados: "texto do pdf"
        )
        assert texto_preview(caminho) == "texto do pdf"

    def test_texto_preview_extensao_desconhecida(self, tmp_path):
        caminho = tmp_path / "doc.txt"
        caminho.write_text("x", encoding="utf-8")
        assert texto_preview(caminho) == ""


class TestAbertura:
    def test_linux_usa_xdg_open(self, monkeypatch):
        chamadas = []
        monkeypatch.setattr(document_actions.platform, "system", lambda: "Linux")
        monkeypatch.setattr(
            document_actions.subprocess, "run",
            lambda args, check: chamadas.append((args, check)),
        )
        document_actions.abrir_no_aplicativo(Path("/tmp/doc.pdf"))
        assert chamadas == [(["xdg-open", "/tmp/doc.pdf"], False)]

    def test_macos_usa_open(self, monkeypatch):
        chamadas = []
        monkeypatch.setattr(document_actions.platform, "system", lambda: "Darwin")
        monkeypatch.setattr(
            document_actions.subprocess, "run",
            lambda args, check: chamadas.append((args, check)),
        )
        document_actions.abrir_no_aplicativo(Path("/tmp/doc.html"))
        assert chamadas == [(["open", "/tmp/doc.html"], False)]

    def test_windows_usa_startfile(self, monkeypatch):
        chamadas = []
        monkeypatch.setattr(document_actions.platform, "system", lambda: "Windows")
        monkeypatch.setattr(
            document_actions.os, "startfile",
            lambda caminho: chamadas.append(caminho),
            raising=False,
        )
        document_actions.abrir_no_aplicativo(Path("C:/doc.pdf"))
        assert chamadas == ["C:/doc.pdf"]


class TestMontagemArvore:
    @needs_display
    def test_arvore_hierarquica(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            raiz = painel._tree.get_children()
            assert len(raiz) == 1
            assert painel._tree.item(raiz[0], "text") == "ALZR11"
            anos = painel._tree.get_children(raiz[0])
            assert [painel._tree.item(no, "text") for no in anos] == ["2026"]
            meses = painel._tree.get_children(anos[0])
            assert [painel._tree.item(no, "text") for no in meses] == ["02"]
            categorias = painel._tree.get_children(meses[0])
            assert [painel._tree.item(no, "text") for no in categorias] == [
                "Assembleia",
                "Aviso aos Acionistas",
            ]
            arquivos = painel._tree.get_children(categorias[1])
            assert [painel._tree.item(no, "text") for no in arquivos] == ["10.pdf"]
        finally:
            root.destroy()

    @needs_display
    def test_selecao_de_arquivo_dispara_preview_cacheada(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            arquivo = painel._itens[_no_arquivo(painel, "10.pdf")]
            painel._preview_cache[arquivo.caminho] = "conteúdo cacheado"
            painel._iniciar_preview(arquivo)
            esperado = (
                f"{mensagem_indisponivel(False)}\n\n---\n\nconteúdo cacheado"
            )
            assert painel._preview.get("1.0", "end-1c") == esperado
        finally:
            root.destroy()

    @needs_display
    def test_preview_sem_texto_exibe_mensagem(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            no = _no_arquivo(painel, "10.pdf")
            arquivo = painel._itens[no]
            painel._tree.selection_set(no)
            painel._aplicar_preview(arquivo, "   ")
            assert painel._preview.get("1.0", "end-1c") == SEM_TEXTO
        finally:
            root.destroy()


class TestAberturaNaArvore:
    @needs_display
    def test_duplo_clique_em_arquivo_abre(self, tmp_path):
        root = tk.Tk()
        try:
            abertos = []
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path),
                open_callback=abertos.append, debounce_ms=0,
            )
            painel.update("ALZR11")
            no = _no_arquivo(painel, "10.pdf")
            painel._tree.selection_set(no)
            assert painel._on_double_click() == "break"
            assert abertos == [painel._itens[no].caminho]
        finally:
            root.destroy()

    @needs_display
    def test_duplo_clique_em_pasta_expande_sem_abrir(self, tmp_path):
        root = tk.Tk()
        try:
            abertos = []
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path),
                open_callback=abertos.append, debounce_ms=0,
            )
            painel.update("ALZR11")
            no_ano = painel._tree.get_children(
                painel._tree.get_children()[0]
            )[0]
            antes = painel._tree.item(no_ano, "open")
            painel._tree.selection_set(no_ano)
            painel._on_double_click()
            assert painel._tree.item(no_ano, "open") != antes
            assert abertos == []
        finally:
            root.destroy()

    @needs_display
    def test_falha_ao_abrir_notifica_status(self, tmp_path):
        root = tk.Tk()
        try:
            mensagens = []

            def _falha(_caminho):
                raise OSError("sem aplicativo")

            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), open_callback=_falha,
                status_callback=lambda msg, icone: mensagens.append((msg, icone)),
                debounce_ms=0,
            )
            painel.update("ALZR11")
            painel._tree.selection_set(_no_arquivo(painel, "10.pdf"))
            painel._on_open_selected()
            assert mensagens and mensagens[0][1] == "⚠"
        finally:
            root.destroy()


class TestEstadoVazioERefresh:
    @needs_display
    def test_ticker_sem_documentos_exibe_mensagem(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("SEMDOC")
            assert painel._content.winfo_manager() == ""
            assert painel._empty_label.winfo_manager() == "pack"
            assert "SEMDOC" in painel._empty_label.cget("text")
        finally:
            root.destroy()

    @needs_display
    def test_com_documentos_mostra_conteudo(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            assert painel._content.winfo_manager() == "pack"
            assert painel._empty_label.winfo_manager() == ""
        finally:
            root.destroy()

    @needs_display
    def test_reset_volta_ao_estado_vazio(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            painel.reset()
            assert painel._empty_label.winfo_manager() == "pack"
            assert painel._tree.get_children() == ()
        finally:
            root.destroy()

    @needs_display
    def test_refresh_revarre_catalogo(self, tmp_path):
        root = tk.Tk()
        try:
            catalogo = MagicMock()
            from flowscope.infrastructure.document_catalog import CatalogoTicker

            catalogo.catalogo.return_value = CatalogoTicker("ALZR11", ())
            painel = DocumentTreePanel(root, catalog=catalogo, debounce_ms=0)
            painel.update("ALZR11")
            painel._on_refresh()
            assert catalogo.catalogo.call_count == 2
        finally:
            root.destroy()


class TestAcquireCallback:
    @needs_display
    def test_update_nao_aciona_callback(self, tmp_path):
        root = tk.Tk()
        try:
            chamadas = []
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path),
                acquire_callback=chamadas.append, debounce_ms=0,
            )
            painel.update("ALZR11")
            assert chamadas == []
            assert painel._tree.get_children() != ()
        finally:
            root.destroy()

    @needs_display
    def test_refresh_aciona_callback(self, tmp_path):
        root = tk.Tk()
        try:
            chamadas = []
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path),
                acquire_callback=chamadas.append, debounce_ms=0,
            )
            painel.update("ALZR11")
            painel._on_refresh()
            assert chamadas == ["ALZR11"]
        finally:
            root.destroy()

    @needs_display
    def test_mostrar_carregando(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            painel.mostrar_carregando("ALZR11")
            assert "Carregando" in painel._empty_label.cget("text")
            assert painel._empty_label.winfo_manager() == "pack"
        finally:
            root.destroy()


class TestBotaoAbrir:
    @needs_display
    def test_botao_rotulo_e_desabilitado_sem_selecao(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            assert painel._open_btn.cget("text") == "Abrir documento"
            assert str(painel._open_btn.cget("state")) == "disabled"
        finally:
            root.destroy()

    @needs_display
    def test_botao_habilita_com_arquivo_selecionado(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            painel._tree.selection_set(_no_arquivo(painel, "10.pdf"))
            root.update()
            assert str(painel._open_btn.cget("state")) == "normal"
        finally:
            root.destroy()

    @needs_display
    def test_botao_desabilita_com_pasta_selecionada(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            pasta = painel._tree.get_children()[0]
            painel._tree.selection_set(pasta)
            root.update()
            assert str(painel._open_btn.cget("state")) == "disabled"
        finally:
            root.destroy()

    @needs_display
    def test_reset_desabilita_botao(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            painel._tree.selection_set(_no_arquivo(painel, "10.pdf"))
            root.update()
            painel.reset()
            assert str(painel._open_btn.cget("state")) == "disabled"
        finally:
            root.destroy()

    @needs_display
    def test_all_buttons_e_refresh_open_button(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            assert painel.all_buttons() == [
                painel._refresh_btn,
                painel._open_btn,
                painel._ia_btn,
            ]
            painel.update("ALZR11")
            painel._open_btn.config(state=tk.NORMAL)
            painel.refresh_open_button()
            assert str(painel._open_btn.cget("state")) == "disabled"

            painel._tree.selection_set(_no_arquivo(painel, "10.pdf"))
            painel.refresh_open_button()
            assert str(painel._open_btn.cget("state")) == "normal"
        finally:
            root.destroy()


class TestBotaoIA:
    @needs_display
    def test_botao_aparece_apos_abrir_documento(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            filhos = list(painel._refresh_btn.master.winfo_children())
            assert filhos == [
                painel._refresh_btn,
                painel._open_btn,
                painel._ia_btn,
            ]
            assert painel._ia_btn.cget("text") == "I.A."
        finally:
            root.destroy()

    @needs_display
    def test_botao_habilitado_sem_documentos(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("SEMDOC")
            assert str(painel._ia_btn.cget("state")) == "normal"
        finally:
            root.destroy()

    @needs_display
    def test_acionamento_chama_callback(self, tmp_path):
        root = tk.Tk()
        try:
            chamadas = []
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path),
                ia_callback=lambda: chamadas.append(True), debounce_ms=0,
            )
            painel._ia_btn.invoke()
            assert chamadas == [True]
        finally:
            root.destroy()

    @needs_display
    def test_sem_callback_nao_falha(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel._on_ia()
        finally:
            root.destroy()


class TestPreviewEmThread:
    @needs_display
    def test_carregando_e_aplicacao(self, tmp_path, monkeypatch):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            no = _no_arquivo(painel, "10.pdf")
            arquivo = painel._itens[no]
            monkeypatch.setattr(
                "flowscope.presentation.gui.charts.document_tree_panel.texto_preview",
                lambda _caminho: "extraído",
            )
            painel._tree.selection_set(no)
            esperado = f"{mensagem_indisponivel(False)}\n\n---\n\nextraído"
            for _ in range(200):
                root.update()
                if painel._preview.get("1.0", "end-1c") == esperado:
                    break
                time.sleep(0.01)
            assert painel._preview.get("1.0", "end-1c") == esperado
        finally:
            root.destroy()


class _Host(TabActionsMixin, TabsLayoutMixin):
    """Combina os mixins usados na construção e navegação das abas."""


class TestWiringSubAba:
    def test_documentos_registrada(self):
        nomes = [config[0] for config in TAB_CONFIGS]
        assert "Documentos" in nomes
        assert "Documentos" in ENABLED_TABS

    def test_conteudo_explicativo_existe(self):
        chave = ("Análise do Ticker", "Documentos")
        assert chave in TAB_CONTENT
        titulo, corpo = TAB_CONTENT[chave]
        assert "Documentos" in titulo
        assert isinstance(corpo, list) and corpo

    @needs_display
    def test_sub_aba_aparece_na_analise_do_ticker(self):
        root = tk.Tk()
        try:
            host = _Host()
            host._main_notebook = ttk.Notebook(root)
            host._copy_chart = lambda _figure: None
            host._build_ticker_tabs()
            abas = [
                host._ticker_notebook.tab(indice, "text")
                for indice in range(host._ticker_notebook.index("end"))
            ]
            assert "Documentos" in abas
            assert hasattr(host, "_documents_panel")
        finally:
            root.destroy()

    @needs_display
    def test_ia_callback_injetado_no_painel(self):
        root = tk.Tk()
        try:
            class _HostIA(_Host):
                def __init__(self):
                    self.chamadas = []

                def _abrir_config_llm(self):
                    self.chamadas.append(True)

            host = _HostIA()
            host._main_notebook = ttk.Notebook(root)
            host._copy_chart = lambda _figure: None
            host._build_ticker_tabs()
            host._documents_panel._ia_btn.invoke()
            assert host.chamadas == [True]
        finally:
            root.destroy()


class TestSyncCopyButton:
    @needs_display
    def test_habilita_em_documentos(self):
        root = tk.Tk()
        try:
            host = TabActionsMixin()
            host._copy_data_btn = tk.Button(root, state=tk.DISABLED)
            host._current_data = {}
            host._button_states = {}
            host._sync_copy_button_for_tab("Análise do Ticker", "Documentos")
            assert str(host._copy_data_btn.cget("state")) == "normal"
        finally:
            root.destroy()

    @needs_display
    def test_desabilita_fora_de_documentos_sem_dados(self):
        root = tk.Tk()
        try:
            host = TabActionsMixin()
            host._copy_data_btn = tk.Button(root, state=tk.NORMAL)
            host._current_data = {}
            host._button_states = {}
            host._sync_copy_button_for_tab("Análise Geral", "Fundamentos")
            assert str(host._copy_data_btn.cget("state")) == "disabled"
        finally:
            root.destroy()

    @needs_display
    def test_mantem_habilitado_com_dados(self):
        root = tk.Tk()
        try:
            host = TabActionsMixin()
            host._copy_data_btn = tk.Button(root, state=tk.DISABLED)
            host._current_data = {"PETR4": {}}
            host._button_states = {}
            host._sync_copy_button_for_tab("Análise Geral", "Fundamentos")
            assert str(host._copy_data_btn.cget("state")) == "normal"
        finally:
            root.destroy()

    @needs_display
    def test_nao_sobrescreve_bloqueio_global(self):
        root = tk.Tk()
        try:
            host = TabActionsMixin()
            host._copy_data_btn = tk.Button(root, state=tk.DISABLED)
            host._current_data = {}
            host._button_states = {host._copy_data_btn: tk.DISABLED}
            host._sync_copy_button_for_tab("Análise do Ticker", "Documentos")
            assert str(host._copy_data_btn.cget("state")) == "disabled"
        finally:
            root.destroy()

    def test_sem_botao_nao_falha(self):
        host = TabActionsMixin()
        host._button_states = {}
        host._sync_copy_button_for_tab("Análise do Ticker", "Documentos")


class TestAbrirConfigLLM:
    def test_abre_dialogo(self, monkeypatch):
        chamadas = []
        monkeypatch.setattr(
            app_actions,
            "LLMConfigDialog",
            lambda parent: chamadas.append(parent),
        )
        host = ActionsMixin()
        host._abrir_config_llm()
        assert chamadas == [host]


class TestDeveAtualizar:
    def test_documentos_atualiza_sem_dados_b3(self):
        host = TabActionsMixin()
        host._current_data = {}
        host._documents_panel = object()
        assert host._deve_atualizar(host._documents_panel) is True

    def test_outros_paineis_nao_atualizam_sem_dados(self):
        host = TabActionsMixin()
        host._current_data = {}
        host._documents_panel = object()
        assert host._deve_atualizar(object()) is False


class TestUpdateDocuments:
    def test_update_documents_chama_painel(self):
        host = ActionsMixin()
        host._documents_panel = MagicMock()
        host._ticker_list = MagicMock()
        host._ticker_list.get_tickers.return_value = ["ALZR11"]
        host._ticker_selecionado = "ALZR11"
        host._update_documents()
        host._documents_panel.update.assert_called_once_with("ALZR11")

    def test_update_documents_usa_ticker_selecionado(self):
        host = ActionsMixin()
        host._documents_panel = MagicMock()
        host._ticker_list = MagicMock()
        host._ticker_list.get_tickers.return_value = ["PETR3"]
        host._ticker_selecionado = "EXXO34"
        host._update_documents()
        host._documents_panel.update.assert_called_once_with("EXXO34")

    def test_ticker_apresentado_usa_selecao_dos_fundamentos(self):
        host = ActionsMixin()
        host._ticker_list = MagicMock()
        host._ticker_list.get_tickers.return_value = ["PETR3"]
        host._ticker_selecionado = "EXXO34"
        assert host._ticker_apresentado() == "EXXO34"
        host._ticker_selecionado = None
        assert host._ticker_apresentado() is None

    def test_documentos_e_evolucao_recebem_mesmo_ticker(self):
        host = ActionsMixin()
        host._documents_panel = MagicMock()
        host._fundamental_evolution_panel = MagicMock()
        host._ticker_list = MagicMock()
        host._ticker_list.get_tickers.return_value = ["PETR3"]
        host._ticker_selecionado = "EXXO34"
        host._fundamental_history_store = None

        host._update_documents()
        host._update_fundamental_evolution()

        host._documents_panel.update.assert_called_once_with("EXXO34")
        host._fundamental_evolution_panel.update.assert_called_once_with(
            (), ticker="EXXO34"
        )

    def test_do_update_despacha_para_documentos(self):
        host = ActionsMixin()
        host._ticker_list = MagicMock()
        host._ticker_list.get_tickers.return_value = []
        host._current_data = {}
        host._ticker_charts = set()
        host._documents_panel = MagicMock()
        host._do_update(host._documents_panel)
        host._documents_panel.update.assert_called_once()

    def test_sem_painel_nao_falha(self):
        host = ActionsMixin()
        host._update_documents()


class TestControllerTickerEdit:
    def test_troca_de_ticker_atualiza_documentos_sem_dados(self):
        gui = MagicMock()
        gui._resolve_current_chart.return_value = object()
        gui._deve_atualizar.return_value = True
        presenter = MagicMock()
        presenter._gui = gui
        presenter.get_current_tickers.return_value = ["ALZR11"]
        controller = FlowScopeController(
            guard=MagicMock(),
            load_portfolio=MagicMock(),
            analyze=MagicMock(),
            presenter=presenter,
            logger=MagicMock(),
        )
        controller.on_ticker_edit()
        gui._do_update.assert_called_once()


class _JobFake:
    def __init__(self, aquisicao, ticker, reference_date):
        self._aquisicao = aquisicao
        self._ticker = ticker
        self._reference_date = reference_date
        self.fila = queue.Queue()

    def iniciar(self):
        try:
            self._aquisicao.adquirir(self._ticker, self._reference_date)
        except Exception:
            pass
        finally:
            self.fila.put(True)


class _HostDocumentos(ActionsMixin):
    def __init__(self):
        self._documents_panel = MagicMock()
        self._aquisicao_documentos = MagicMock()
        self._presenter = MagicMock()
        self._documentos_job = None
        self._date_entry = MagicMock()
        self._date_entry.get_date.return_value = date(2026, 7, 29)
        self.agendados = []

    def after(self, ms, callback):
        self.agendados.append((ms, callback))
        return "id"

    def _flash_status(self, *args, **kwargs):
        pass


class TestAdquirirDocumentos:
    def test_executa_e_remonta_arvore(self, monkeypatch):
        host = _HostDocumentos()
        monkeypatch.setattr(app_actions, "DocumentosJob", _JobFake)
        host._adquirir_documentos("EXXO34")
        host._aquisicao_documentos.adquirir.assert_called_once_with(
            "EXXO34", date(2026, 7, 29)
        )
        host._documents_panel.mostrar_carregando.assert_called_once_with("EXXO34")
        host._documents_panel.update.assert_called_once_with("EXXO34")

    def test_falha_de_aquisicao_ainda_remonta(self, monkeypatch):
        host = _HostDocumentos()
        host._aquisicao_documentos.adquirir.side_effect = RuntimeError("offline")
        monkeypatch.setattr(app_actions, "DocumentosJob", _JobFake)
        host._adquirir_documentos("PETR3")
        host._documents_panel.update.assert_called_once_with("PETR3")

    def test_sem_aquisicao_apenas_varre(self):
        host = _HostDocumentos()
        host._aquisicao_documentos = None
        host._adquirir_documentos("PETR3")
        host._documents_panel.update.assert_called_once_with("PETR3")

    def test_ticker_vazio_apenas_varre(self):
        host = _HostDocumentos()
        host._adquirir_documentos("")
        host._documents_panel.update.assert_called_once_with("")

    def test_sem_painel_nao_falha(self):
        host = _HostDocumentos()
        host._documents_panel = None
        host._adquirir_documentos("PETR3")

    def test_bloqueia_e_restaura_controles(self, monkeypatch):
        host = _HostDocumentos()
        monkeypatch.setattr(app_actions, "DocumentosJob", _JobFake)
        host._adquirir_documentos("EXXO34")

        host._presenter.on_operation_started.assert_called_once()
        host._presenter.on_operation_finished.assert_called_once()

    def test_reentrancia_ignora_segundo_acionamento(self, monkeypatch):
        class _JobPendente:
            def __init__(self, *args, **kwargs):
                self.fila = queue.Queue()

            def iniciar(self):
                return None

        host = _HostDocumentos()
        monkeypatch.setattr(app_actions, "DocumentosJob", _JobPendente)
        host._adquirir_documentos("EXXO34")
        host._aquisicao_documentos.adquirir.reset_mock()
        host._presenter.on_operation_started.reset_mock()

        host._adquirir_documentos("EXXO34")

        host._aquisicao_documentos.adquirir.assert_not_called()
        host._presenter.on_operation_started.assert_not_called()


class TestDocumentosJob:
    def test_publica_termino_apos_falha(self):
        class _AquisicaoFalha:
            def adquirir(self, ticker, reference_date, progress=None):
                raise RuntimeError("offline")

        job = DocumentosJob(_AquisicaoFalha(), "PETR3", date(2026, 7, 29))
        job.iniciar().join()
        assert job.fila.get_nowait() is True

    def test_publica_progresso_antes_do_termino(self):
        class _AquisicaoProgresso:
            def adquirir(self, ticker, reference_date, progress=None):
                progress(1, 2, "• Documentos de PETR3 (1/2)")
                progress(2, 2, "• Documentos de PETR3 (2/2)")

        job = DocumentosJob(_AquisicaoProgresso(), "PETR3", date(2026, 7, 29))
        job.iniciar().join()

        mensagens = []
        while not job.fila.empty():
            mensagens.append(job.fila.get_nowait())
        assert mensagens[0] == (
            MENSAGEM_PROGRESSO, 1, 2, "• Documentos de PETR3 (1/2)"
        )
        assert mensagens[1] == (
            MENSAGEM_PROGRESSO, 2, 2, "• Documentos de PETR3 (2/2)"
        )
        assert mensagens[-1] is True


class TestWidgetSomenteLeitura:
    @needs_display
    def test_preview_usa_readonly_text(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            assert isinstance(painel._preview, ReadonlyText)
        finally:
            root.destroy()

    @needs_display
    def test_texto_atual_reflete_a_preview(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel._set_preview_text("conteudo atual")
            assert painel.texto_atual() == "conteudo atual"
        finally:
            root.destroy()


class TestAgrupamento:
    @needs_display
    def test_nos_de_agrupamento_tem_payload(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            tipos = {grupo.tipo for grupo in painel._grupos.values()}
            assert tipos == {"ticker", "ano", "mes", "categoria"}
            assert _no_arquivo(painel, "10.pdf") not in painel._grupos
        finally:
            root.destroy()

    @needs_display
    def test_lista_do_ticker_com_niveis_relativos(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            painel._tree.selection_set(_no_grupo(painel, "ticker"))
            root.update()
            texto = painel._preview.get("1.0", "end-1c")
            assert texto.startswith("# ALZR11\n## 2026\n### 02\n")
            assert "#### Assembleia" in texto
            assert "#### Aviso aos Acionistas" in texto
            assert "- 10.pdf —" in texto
            assert "- 20.pdf —" in texto
        finally:
            root.destroy()

    @needs_display
    def test_lista_da_categoria(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            painel._tree.selection_set(
                _no_grupo(painel, "categoria", "Aviso aos Acionistas")
            )
            root.update()
            texto = painel._preview.get("1.0", "end-1c")
            assert texto.startswith("# Aviso aos Acionistas\n")
            assert "- 10.pdf —" in texto
            assert "20.pdf" not in texto
        finally:
            root.destroy()

    @needs_display
    def test_item_exibe_short_summary_armazenado(self, tmp_path):
        root = tk.Tk()
        try:
            _touch(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
            store = JsonDocumentSummaryStore(cache_dir=tmp_path)
            store.salvar(
                "ALZR11", "bdr/ALZR11/2026/02/10.pdf", "resumo curto", "longo"
            )
            catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
            painel = DocumentTreePanel(
                root, catalog=catalogo, summary_store=store, debounce_ms=0
            )
            painel.update("ALZR11")
            painel._tree.selection_set(_no_grupo(painel, "ticker"))
            root.update()
            assert "- 10.pdf — resumo curto" in painel._preview.get(
                "1.0", "end-1c"
            )
        finally:
            root.destroy()


class TestMensagemIndisponibilidade:
    def test_dois_sufixos(self):
        assert mensagem_indisponivel(True) == (
            "Resumo indisponível. Clique no documento para análise."
        )
        assert mensagem_indisponivel(False) == (
            "Resumo indisponível. Configure a LLM via o botão I.A. e teste "
            "a comunicação."
        )

    @needs_display
    def test_lista_usa_sufixo_da_llm_configurada(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path),
                llm_available=lambda: True, llm_factory=lambda: object(),
                debounce_ms=0,
            )
            painel.update("ALZR11")
            painel._tree.selection_set(_no_grupo(painel, "ticker"))
            root.update()
            assert mensagem_indisponivel(True) in painel._preview.get(
                "1.0", "end-1c"
            )
        finally:
            root.destroy()

    @needs_display
    def test_lista_usa_sufixo_sem_llm(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            painel._tree.selection_set(_no_grupo(painel, "ticker"))
            root.update()
            assert mensagem_indisponivel(False) in painel._preview.get(
                "1.0", "end-1c"
            )
        finally:
            root.destroy()


class TestGeracaoDeResumo:
    def _painel(self, root, tmp_path, llm, disponivel=True):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
        _touch(
            catalogo.base_dir / "informe-mensal" / "ALZR11" / "2026" / "02"
            / "20.html",
            b"<html><body>Conteudo do informe</body></html>",
        )
        painel = DocumentTreePanel(
            root, catalog=catalogo, summary_store=store,
            llm_available=lambda: disponivel, llm_factory=lambda: llm,
            debounce_ms=0,
        )
        painel.update("ALZR11")
        return painel, store

    @needs_display
    def test_preview_composta_com_resumo_longo(self, tmp_path):
        root = tk.Tk()
        try:
            store = JsonDocumentSummaryStore(cache_dir=tmp_path)
            store.salvar(
                "ALZR11", "informe-mensal/ALZR11/2026/02/20.html",
                "curto", "resumo longo",
            )
            catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
            _touch(
                catalogo.base_dir / "informe-mensal" / "ALZR11" / "2026"
                / "02" / "20.html",
                b"<html><body>Conteudo do informe</body></html>",
            )
            painel = DocumentTreePanel(
                root, catalog=catalogo, summary_store=store, debounce_ms=0
            )
            painel.update("ALZR11")
            no = _no_arquivo(painel, "20.html")
            painel._tree.selection_set(no)
            assert _pump(
                root,
                lambda: painel._preview.get("1.0", "end-1c")
                == "resumo longo\n\n---\n\nConteudo do informe",
            )
        finally:
            root.destroy()

    @needs_display
    def test_gera_resumo_persiste_e_atualiza_catalogo(self, tmp_path):
        root = tk.Tk()
        try:
            llm = _LLMFake("CURTO: curto\nLONGO: longo")
            painel, store = self._painel(root, tmp_path, llm)
            no = _no_arquivo(painel, "20.html")
            painel._tree.selection_set(no)
            assert _pump(root, lambda: "longo" in painel._preview.get("1.0", "end-1c"))
            texto = painel._preview.get("1.0", "end-1c")
            assert texto == "longo\n\n---\n\nConteudo do informe"
            assert painel._itens[no].short_summary == "curto"
            assert painel._itens[no].long_summary == "longo"
            assert len(llm.chamadas) == 1
            chave = "informe-mensal/ALZR11/2026/02/20.html"
            assert store.obter("ALZR11", chave).long_summary == "longo"
            painel._tree.selection_set(_no_grupo(painel, "ticker"))
            root.update()
            assert "- 20.html — curto" in painel._preview.get("1.0", "end-1c")
        finally:
            root.destroy()

    @needs_display
    def test_sem_llm_exibe_mensagem_sem_chamar(self, tmp_path):
        root = tk.Tk()
        try:
            llm = _LLMFake("CURTO: curto\nLONGO: longo")
            painel, store = self._painel(root, tmp_path, llm, disponivel=False)
            no = _no_arquivo(painel, "20.html")
            painel._tree.selection_set(no)
            esperado = (
                f"{mensagem_indisponivel(False)}\n\n---\n\nConteudo do informe"
            )
            assert _pump(root, lambda: painel._preview.get("1.0", "end-1c") == esperado)
            assert llm.chamadas == []
            assert store.resumos("ALZR11") == {}
        finally:
            root.destroy()

    @needs_display
    def test_falha_tipada_exibe_mensagem(self, tmp_path):
        root = tk.Tk()
        try:
            class _Falha:
                def complete(self, messages, system_prompt=None):
                    raise LLMCommunicationError("timeout")

            painel, _ = self._painel(root, tmp_path, _Falha())
            no = _no_arquivo(painel, "20.html")
            painel._tree.selection_set(no)
            assert _pump(
                root,
                lambda: mensagem_indisponivel(True)
                in painel._preview.get("1.0", "end-1c"),
            )
        finally:
            root.destroy()

    @needs_display
    def test_resultado_obsoleto_descartado(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.update("ALZR11")
            arquivo = painel._itens[_no_arquivo(painel, "10.pdf")]
            painel._set_preview_text("ATUAL")
            fila: queue.Queue = queue.Queue()
            req_antigo = painel._req_id
            painel._req_id += 1
            painel._agendar_poll(arquivo, fila, req_antigo)
            fila.put(("texto antigo", None))
            for _ in range(50):
                root.update()
                time.sleep(0.005)
            assert painel._preview.get("1.0", "end-1c") == "ATUAL"
        finally:
            root.destroy()
