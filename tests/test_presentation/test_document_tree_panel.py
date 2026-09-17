"""Testes do painel de documentos, do preview e da abertura de arquivos."""

import os
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from unittest.mock import MagicMock

import pytest

from flowscope.infrastructure.document_catalog import DocumentCatalog
from flowscope.presentation.gui import document_actions
from flowscope.presentation.gui.app_actions import ActionsMixin
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
)
from flowscope.presentation.gui.controller import FlowScopeController

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
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


def _no_arquivo(painel: DocumentTreePanel, nome: str) -> str:
    for iid, arquivo in painel._itens.items():
        if arquivo.nome == nome:
            return iid
    raise AssertionError(f"arquivo {nome} não encontrado na árvore")


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
            painel._aplicar_preview(arquivo, "conteúdo cacheado")
            painel._iniciar_preview(arquivo)
            assert painel._preview.get("1.0", "end-1c") == "conteúdo cacheado"
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
            painel._iniciar_preview(arquivo)
            assert painel._preview.get("1.0", "end-1c") in (CARREGANDO, "extraído")
            for _ in range(100):
                root.update()
                if painel._preview.get("1.0", "end-1c") == "extraído":
                    break
                time.sleep(0.01)
            assert painel._preview.get("1.0", "end-1c") == "extraído"
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
        host._update_documents()
        host._documents_panel.update.assert_called_once_with("ALZR11")

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
