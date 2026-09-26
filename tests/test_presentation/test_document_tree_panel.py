"""Testes do painel de documentos, do preview e da abertura de arquivos."""

import logging
import os
import queue
import time
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import ttk
from unittest.mock import MagicMock

import pytest

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.llm import LLMCommunicationError
from flowscope.infrastructure.document_catalog import DocumentCatalog
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.infrastructure.document_texts import JsonDocumentTextStore
from flowscope.presentation.gui import (
    app_actions,
    app_resumos_actions,
    app_tab_actions,
    document_actions,
)
from flowscope.presentation.gui.app_actions import ActionsMixin
from flowscope.presentation.gui.app_resumos_actions import ResumosActionsMixin
from flowscope.presentation.gui.documentos_job import (
    MENSAGEM_PROGRESSO,
    DocumentosJob,
)
from flowscope.presentation.gui.progress import ProgressReporter
from flowscope.presentation.gui.resumos_job import (
    MENSAGEM_ERRO as RESUMO_ERRO,
    MENSAGEM_RESULTADO as RESUMO_RESULTADO,
    ResumosPendentesJob,
)
from flowscope.presentation.gui.app_tab_actions import TabActionsMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.app_tabs import (
    ENABLED_TABS,
    TAB_CONFIGS,
    TAB_CONTENT,
)
from flowscope.application import document_preview
from flowscope.application.document_preview import (
    SELETOR_CONTEUDO_DETALHE,
    SEM_TEXTO,
    tem_texto,
    texto_de_html,
    texto_de_pdf,
    texto_preview,
)
from flowscope.presentation.gui.charts.document_grouping import (
    mensagem_indisponivel,
)
from flowscope.presentation.gui.charts.document_tree_panel import (
    CARREGANDO,
    DocumentTreePanel,
)
from flowscope.presentation.gui.charts.document_tree_view import DocumentTreeView
from flowscope.presentation.gui.controller import FlowScopeController
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText

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

    def test_texto_de_html_com_seletor_isola_conteudo(self):
        html = (
            "<html><body>"
            "<div id='topo'>Moldura da pagina</div>"
            "<pre id='conteudoDetalhe'>Corpo do artigo</pre>"
            "<footer>Rodape</footer>"
            "</body></html>"
        )
        texto = texto_de_html(html, SELETOR_CONTEUDO_DETALHE)
        assert texto == "Corpo do artigo"
        assert "Moldura" not in texto
        assert "Rodape" not in texto

    def test_texto_de_html_seletor_ausente_usa_pagina(self):
        texto = texto_de_html(
            "<html><body><h1>Titulo</h1></body></html>",
            SELETOR_CONTEUDO_DETALHE,
        )
        assert "Titulo" in texto

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

    def test_tem_texto_vazio(self):
        assert tem_texto("") is False

    def test_tem_texto_apenas_espacos(self):
        assert tem_texto("   \n\t ") is False

    def test_tem_texto_marcador(self):
        assert tem_texto(SEM_TEXTO) is False

    def test_tem_texto_com_conteudo(self):
        assert tem_texto("conteudo do documento") is True


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
                painel._resumir_btn,
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
                painel._resumir_btn,
            ]
            assert painel._ia_btn.cget("text") == "I.A."
            assert painel._resumir_btn.cget("text") == "Resumir pendentes"
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
                "flowscope.presentation.gui.charts.document_flow_mixin.texto_preview",
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


class TestCacheTextoPreview:
    def _painel(self, root, tmp_path, monkeypatch, texto_convertido):
        store = JsonDocumentTextStore(cache_dir=tmp_path)
        catalogo = DocumentCatalog(cache_dir=tmp_path, text_store=store)
        _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        chamadas = []
        monkeypatch.setattr(
            "flowscope.presentation.gui.charts.document_flow_mixin.texto_preview",
            lambda caminho: chamadas.append(caminho) or texto_convertido,
        )
        painel = DocumentTreePanel(
            root, catalog=catalogo, text_store=store, debounce_ms=0
        )
        painel.update("ALZR11")
        return painel, store, chamadas

    @needs_display
    def test_miss_converte_e_grava_no_cache(self, tmp_path, monkeypatch):
        root = tk.Tk()
        try:
            painel, store, chamadas = self._painel(
                root, tmp_path, monkeypatch, "extraído"
            )
            no = _no_arquivo(painel, "10.pdf")
            painel._tree.selection_set(no)
            assert _pump(
                root, lambda: "extraído" in painel._preview.get("1.0", "end-1c")
            )
            assert len(chamadas) == 1
            assert store.obter("ALZR11", "bdr/ALZR11/2026/02/10.pdf") == "extraído"
        finally:
            root.destroy()

    @needs_display
    def test_miss_sem_texto_grava_marcador(self, tmp_path, monkeypatch):
        root = tk.Tk()
        try:
            painel, store, _ = self._painel(root, tmp_path, monkeypatch, "")
            no = _no_arquivo(painel, "10.pdf")
            painel._tree.selection_set(no)
            assert _pump(
                root, lambda: painel._preview.get("1.0", "end-1c") == SEM_TEXTO
            )
            assert store.obter("ALZR11", "bdr/ALZR11/2026/02/10.pdf") == SEM_TEXTO
        finally:
            root.destroy()

    @needs_display
    def test_hit_usa_cache_sem_converter(self, tmp_path, monkeypatch):
        root = tk.Tk()
        try:
            store = JsonDocumentTextStore(cache_dir=tmp_path)
            store.salvar("ALZR11", "bdr/ALZR11/2026/02/10.pdf", "do cache")
            catalogo = DocumentCatalog(cache_dir=tmp_path, text_store=store)
            _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
            chamadas = []
            monkeypatch.setattr(
                "flowscope.presentation.gui.charts.document_flow_mixin.texto_preview",
                lambda caminho: chamadas.append(caminho) or "convertido",
            )
            painel = DocumentTreePanel(
                root, catalog=catalogo, text_store=store, debounce_ms=0
            )
            painel.update("ALZR11")
            no = _no_arquivo(painel, "10.pdf")
            painel._tree.selection_set(no)
            esperado = f"{mensagem_indisponivel(False)}\n\n---\n\ndo cache"
            assert _pump(
                root, lambda: painel._preview.get("1.0", "end-1c") == esperado
            )
            assert chamadas == []
        finally:
            root.destroy()

    @needs_display
    def test_marcador_em_cache_nao_reconverte(self, tmp_path, monkeypatch):
        root = tk.Tk()
        try:
            store = JsonDocumentTextStore(cache_dir=tmp_path)
            store.salvar("ALZR11", "bdr/ALZR11/2026/02/10.pdf", SEM_TEXTO)
            catalogo = DocumentCatalog(cache_dir=tmp_path, text_store=store)
            _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
            chamadas = []
            monkeypatch.setattr(
                "flowscope.presentation.gui.charts.document_flow_mixin.texto_preview",
                lambda caminho: chamadas.append(caminho) or "convertido",
            )
            painel = DocumentTreePanel(
                root, catalog=catalogo, text_store=store, debounce_ms=0
            )
            painel.update("ALZR11")
            no = _no_arquivo(painel, "10.pdf")
            painel._tree.selection_set(no)
            assert _pump(
                root, lambda: painel._preview.get("1.0", "end-1c") == SEM_TEXTO
            )
            assert chamadas == []
        finally:
            root.destroy()


class TestAberturaSemTexto:
    @needs_display
    def test_abertura_permanece_funcional_sem_texto(self, tmp_path):
        root = tk.Tk()
        try:
            abertos = []
            store = JsonDocumentTextStore(cache_dir=tmp_path)
            store.salvar("ALZR11", "bdr/ALZR11/2026/02/10.pdf", SEM_TEXTO)
            catalogo = DocumentCatalog(cache_dir=tmp_path, text_store=store)
            _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
            painel = DocumentTreePanel(
                root, catalog=catalogo, text_store=store,
                open_callback=abertos.append, debounce_ms=0,
            )
            painel.update("ALZR11")
            no = _no_arquivo(painel, "10.pdf")
            painel._tree.selection_set(no)
            assert _pump(
                root, lambda: painel._preview.get("1.0", "end-1c") == SEM_TEXTO
            )
            assert str(painel._open_btn.cget("state")) == "normal"

            painel._open_btn.invoke()
            assert abertos == [painel._itens[no].caminho]

            assert painel._on_double_click() == "break"
            assert abertos[-1] == painel._itens[no].caminho
        finally:
            root.destroy()


class TestRolagemDocumentos:
    @needs_display
    def test_barra_da_arvore_mapeada_em_painel_estreito(self):
        root = tk.Tk()
        try:
            view = DocumentTreeView(root)
            view.frame.pack_propagate(False)
            view.frame.configure(width=50, height=100)
            view.frame.pack()
            root.update()
            assert view.rolagem.winfo_ismapped()
            assert view.rolagem.winfo_width() > 0
        finally:
            root.destroy()

    @needs_display
    def test_barra_da_preview_mapeada_em_painel_estreito(self, tmp_path):
        root = tk.Tk()
        try:
            root.geometry("600x300")
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.frame.pack(fill=tk.BOTH, expand=True)
            painel.update("ALZR11")
            root.update()
            painel._content.sash_place(0, 590, 0)
            root.update()
            assert painel._preview.master.winfo_width() < 20
            assert painel._preview_scrollbar.winfo_ismapped()
            assert painel._preview_scrollbar.winfo_width() > 0
        finally:
            root.destroy()

    @needs_display
    def test_barras_mapeadas_no_painel(self, tmp_path):
        root = tk.Tk()
        try:
            root.geometry("600x400")
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.frame.pack(fill=tk.BOTH, expand=True)
            painel.update("ALZR11")
            root.update()
            assert painel._view.rolagem.winfo_ismapped()
            assert painel._view.rolagem.winfo_width() > 0
            assert painel._preview_scrollbar.winfo_ismapped()
            assert painel._preview_scrollbar.winfo_width() > 0
        finally:
            root.destroy()

    @needs_display
    def test_roda_rola_arvore(self, tmp_path):
        root = tk.Tk()
        try:
            root.geometry("600x200")
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.frame.pack(fill=tk.BOTH, expand=True)
            painel.update("ALZR11")
            for indice in range(100):
                painel._tree.insert("", "end", text=f"item {indice}")
            root.update()
            antes = painel._tree.yview()
            painel._tree.event_generate("<Button-5>", x=5, y=5)
            root.update()
            assert painel._tree.yview() != antes
        finally:
            root.destroy()

    @needs_display
    def test_roda_rola_preview(self, tmp_path):
        root = tk.Tk()
        try:
            root.geometry("600x200")
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            painel.frame.pack(fill=tk.BOTH, expand=True)
            painel._set_preview_text("\n".join(f"linha {i}" for i in range(200)))
            root.update()
            antes = painel._preview.yview()
            painel._preview.event_generate("<Button-5>", x=5, y=5)
            root.update()
            assert painel._preview.yview() != antes
        finally:
            root.destroy()


def _arquivo(tmp_path: Path, nome: str = "10.pdf") -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=2,
        categoria="Aviso aos Acionistas",
        nome=nome,
        tipo="pdf",
        caminho=tmp_path / nome,
    )


class TestFachadaDocumentos:
    @needs_display
    def test_documentos_sem_resumo_em_ordem_da_arvore(self, tmp_path):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        store.salvar("ALZR11", "bdr/ALZR11/2026/02/10.pdf", "c", "l")
        catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
        _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        _touch(
            catalogo.base_dir / "informe-mensal" / "ALZR11" / "2026" / "02"
            / "20.html",
            b"<html><body>Conteudo</body></html>",
        )
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=catalogo, summary_store=store, debounce_ms=0
            )
            painel.update("ALZR11")
            pendentes = painel.documentos_sem_resumo()
            assert [arquivo.nome for arquivo in pendentes] == ["20.html"]
        finally:
            root.destroy()

    @needs_display
    def test_preparar_texto_miss_converte_e_grava(self, tmp_path, monkeypatch):
        store = JsonDocumentTextStore(cache_dir=tmp_path)
        catalogo = DocumentCatalog(cache_dir=tmp_path, text_store=store)
        _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        chamadas = []
        monkeypatch.setattr(
            "flowscope.presentation.gui.charts.document_flow_mixin.texto_preview",
            lambda caminho: chamadas.append(caminho) or "extraído",
        )
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=catalogo, text_store=store, debounce_ms=0
            )
            painel.update("ALZR11")
            arquivo = painel._itens[_no_arquivo(painel, "10.pdf")]
            assert painel.preparar_texto(arquivo) == "extraído"
            assert chamadas == [arquivo.caminho]
            assert store.obter(
                "ALZR11", "bdr/ALZR11/2026/02/10.pdf"
            ) == "extraído"
            assert painel._preview_cache[arquivo.caminho] == "extraído"
        finally:
            root.destroy()

    @needs_display
    def test_preparar_texto_hit_nao_converte(self, tmp_path, monkeypatch):
        store = JsonDocumentTextStore(cache_dir=tmp_path)
        store.salvar("ALZR11", "bdr/ALZR11/2026/02/10.pdf", "do cache")
        catalogo = DocumentCatalog(cache_dir=tmp_path, text_store=store)
        _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        chamadas = []
        monkeypatch.setattr(
            "flowscope.presentation.gui.charts.document_flow_mixin.texto_preview",
            lambda caminho: chamadas.append(caminho) or "convertido",
        )
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=catalogo, text_store=store, debounce_ms=0
            )
            painel.update("ALZR11")
            arquivo = painel._itens[_no_arquivo(painel, "10.pdf")]
            assert painel.preparar_texto(arquivo) == "do cache"
            assert chamadas == []
        finally:
            root.destroy()


class TestAplicarResumo:
    @needs_display
    def test_grava_e_atualiza_catalogo(self, tmp_path):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
        _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=catalogo, summary_store=store, debounce_ms=0
            )
            painel.update("ALZR11")
            no = _no_arquivo(painel, "10.pdf")
            arquivo = painel._itens[no]
            painel.aplicar_resumo(arquivo, ResumoDocumento("curto", "longo"))
            assert painel._itens[no].long_summary == "longo"
            assert painel._por_caminho[arquivo.caminho].long_summary == "longo"
            salvo = store.obter("ALZR11", "bdr/ALZR11/2026/02/10.pdf")
            assert salvo.long_summary == "longo"
        finally:
            root.destroy()

    @needs_display
    def test_atualiza_estado_do_botao(self, tmp_path):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
        _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=catalogo, summary_store=store,
                llm_available=lambda: True, debounce_ms=0,
            )
            painel.update("ALZR11")
            assert str(painel._resumir_btn.cget("state")) == "normal"
            arquivo = painel._itens[_no_arquivo(painel, "10.pdf")]
            painel.aplicar_resumo(arquivo, ResumoDocumento("c", "l"))
            assert str(painel._resumir_btn.cget("state")) == "disabled"
        finally:
            root.destroy()

    @needs_display
    def test_recompoe_preview_quando_selecionado(self, tmp_path):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
        _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=catalogo, summary_store=store, debounce_ms=0
            )
            painel.update("ALZR11")
            no = _no_arquivo(painel, "10.pdf")
            arquivo = painel._itens[no]
            painel._tree.selection_set(no)
            painel._preview_cache[arquivo.caminho] = "texto integral"
            painel.aplicar_resumo(arquivo, ResumoDocumento("curto", "longo"))
            assert painel._preview.get("1.0", "end-1c") == (
                "longo\n\n---\n\ntexto integral"
            )
        finally:
            root.destroy()


class TestPersistenciaNoWorkerDoPainel:
    @needs_display
    def test_painel_de_documentos_persiste_no_lote(self, tmp_path):
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path), debounce_ms=0
            )
            assert painel.persistir_no_lote() is True
        finally:
            root.destroy()

    @needs_display
    def test_gerar_e_persistir_grava_sem_tocar_no_catalogo(self, tmp_path):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
        _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        llm = _LLMFake(resposta="Resumo gerado")
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=catalogo, summary_store=store,
                llm_available=lambda: True, llm_factory=lambda: llm,
                debounce_ms=0,
            )
            painel.update("ALZR11")
            no = _no_arquivo(painel, "10.pdf")
            arquivo = painel._itens[no]
            resumo = painel.gerar_e_persistir(arquivo, "texto")
            assert resumo is not None
            salvo = store.obter("ALZR11", "bdr/ALZR11/2026/02/10.pdf")
            assert salvo.long_summary == resumo.long_summary
            assert painel._itens[no].long_summary is None
        finally:
            root.destroy()

    @needs_display
    def test_refletir_resumo_nao_grava_no_store(self, tmp_path):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
        _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        root = tk.Tk()
        try:
            painel = DocumentTreePanel(
                root, catalog=catalogo, summary_store=store, debounce_ms=0
            )
            painel.update("ALZR11")
            no = _no_arquivo(painel, "10.pdf")
            arquivo = painel._itens[no]
            painel.refletir_resumo(arquivo, ResumoDocumento("curto", "longo"))
            assert painel._itens[no].long_summary == "longo"
            assert store.obter("ALZR11", "bdr/ALZR11/2026/02/10.pdf") is None
        finally:
            root.destroy()


class TestBotaoResumir:
    @needs_display
    def test_acionamento_chama_callback(self, tmp_path):
        root = tk.Tk()
        try:
            chamadas = []
            painel = DocumentTreePanel(
                root, catalog=_catalogo(tmp_path),
                resumir_callback=lambda: chamadas.append(True), debounce_ms=0,
            )
            painel._resumir_btn.config(state=tk.NORMAL)
            painel._resumir_btn.invoke()
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
            painel._on_resumir()
        finally:
            root.destroy()


class TestRefreshResumirButton:
    def _painel(self, root, tmp_path, disponivel=True, com_resumo=False):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        if com_resumo:
            store.salvar("ALZR11", "bdr/ALZR11/2026/02/10.pdf", "c", "l")
        catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
        _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        painel = DocumentTreePanel(
            root, catalog=catalogo, summary_store=store,
            llm_available=lambda: disponivel, debounce_ms=0,
        )
        painel.update("ALZR11")
        return painel

    @needs_display
    def test_habilitado_com_llm_e_pendentes(self, tmp_path):
        root = tk.Tk()
        try:
            painel = self._painel(root, tmp_path, disponivel=True)
            assert str(painel._resumir_btn.cget("state")) == "normal"
        finally:
            root.destroy()

    @needs_display
    def test_desabilitado_sem_llm(self, tmp_path):
        root = tk.Tk()
        try:
            painel = self._painel(root, tmp_path, disponivel=False)
            assert str(painel._resumir_btn.cget("state")) == "disabled"
        finally:
            root.destroy()

    @needs_display
    def test_desabilitado_sem_pendentes(self, tmp_path):
        root = tk.Tk()
        try:
            painel = self._painel(root, tmp_path, com_resumo=True)
            assert str(painel._resumir_btn.cget("state")) == "disabled"
        finally:
            root.destroy()

    @needs_display
    def test_callback_de_lote_padrao_none(self, tmp_path):
        root = tk.Tk()
        try:
            painel = self._painel(root, tmp_path, disponivel=True)
            assert painel._resumir_ativo_callback is None
            assert str(painel._resumir_btn.cget("state")) == "normal"
        finally:
            root.destroy()

    @needs_display
    def test_desabilitado_com_lote_ativo(self, tmp_path):
        root = tk.Tk()
        try:
            store = JsonDocumentSummaryStore(cache_dir=tmp_path)
            catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
            _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
            painel = DocumentTreePanel(
                root, catalog=catalogo, summary_store=store,
                llm_available=lambda: True,
                resumir_ativo_callback=lambda: True, debounce_ms=0,
            )
            painel.update("ALZR11")
            assert str(painel._resumir_btn.cget("state")) == "disabled"
        finally:
            root.destroy()


class TestBotaoResumirDuranteLote:
    def _painel(self, root, tmp_path, ativo=lambda: True):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
        _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "20.pdf")
        painel = DocumentTreePanel(
            root, catalog=catalogo, summary_store=store,
            llm_available=lambda: True,
            resumir_ativo_callback=ativo, debounce_ms=0,
        )
        painel.update("ALZR11")
        return painel

    @needs_display
    def test_aplicar_resumo_com_pendente_nao_reabilita(self, tmp_path):
        root = tk.Tk()
        try:
            painel = self._painel(root, tmp_path)
            arquivo = painel._itens[_no_arquivo(painel, "10.pdf")]
            painel.aplicar_resumo(arquivo, ResumoDocumento("c", "l"))
            assert painel.documentos_sem_resumo()
            assert str(painel._resumir_btn.cget("state")) == "disabled"
        finally:
            root.destroy()

    @needs_display
    def test_update_mantem_desabilitado_com_pendentes(self, tmp_path):
        root = tk.Tk()
        try:
            painel = self._painel(root, tmp_path)
            painel.update("ALZR11")
            assert painel.documentos_sem_resumo()
            assert str(painel._resumir_btn.cget("state")) == "disabled"
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
            assert host._documents_panel._text_store is not None
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

    @needs_display
    def test_resumir_callback_injetado_no_painel(self):
        root = tk.Tk()
        try:
            class _HostResumo(_Host):
                def __init__(self):
                    self.chamadas = []

                def _resumir_documentos_pendentes(self):
                    self.chamadas.append(True)

            host = _HostResumo()
            host._main_notebook = ttk.Notebook(root)
            host._copy_chart = lambda _figure: None
            host._build_ticker_tabs()
            host._documents_panel._resumir_btn.config(state=tk.NORMAL)
            host._documents_panel._resumir_btn.invoke()
            assert host.chamadas == [True]
        finally:
            root.destroy()

    @needs_display
    def test_resumir_ativo_callback_injetado_no_painel(self):
        root = tk.Tk()
        try:
            class _HostAtivo(_Host):
                def _resumos_em_andamento(self):
                    return True

            host = _HostAtivo()
            host._main_notebook = ttk.Notebook(root)
            host._copy_chart = lambda _figure: None
            host._build_ticker_tabs()
            assert host._documents_panel._resumir_ativo_callback is not None
            assert host._documents_panel._resumir_ativo_callback() is True
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
            app_tab_actions,
            "LLMConfigDialog",
            lambda parent, **kwargs: chamadas.append((parent, kwargs)),
        )
        host = TabActionsMixin()
        host._abrir_config_llm()
        assert len(chamadas) == 1
        parent, kwargs = chamadas[0]
        assert parent is host
        assert callable(kwargs["on_saved"])

    def test_injeta_refresh_do_painel(self, monkeypatch):
        chamadas = []
        monkeypatch.setattr(
            app_tab_actions,
            "LLMConfigDialog",
            lambda parent, **kwargs: chamadas.append(kwargs),
        )
        host = TabActionsMixin()
        painel = MagicMock()
        host._documents_panel = painel
        host._abrir_config_llm()
        chamadas[0]["on_saved"]()
        painel.refresh_resumir_button.assert_called_once_with()


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
    def __init__(self, aquisicao, ticker, reference_date, cancel_token=None):
        self._aquisicao = aquisicao
        self._ticker = ticker
        self._reference_date = reference_date
        self.cancel_token = cancel_token
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

    def test_falha_ao_iniciar_job_libera_cursor(self, monkeypatch):
        class _JobFalhaInicio:
            def __init__(self, *args, **kwargs):
                self.fila = queue.Queue()

            def iniciar(self):
                raise RuntimeError("thread boom")

        host = _HostDocumentos()
        monkeypatch.setattr(app_actions, "DocumentosJob", _JobFalhaInicio)
        host._adquirir_documentos("EXXO34")

        host._presenter.on_operation_finished.assert_called_once()
        assert host._documentos_job is None


class TestPollDocumentosResiliente:
    def test_erro_ao_tratar_progresso_ainda_encerra_job(self):
        host = _HostDocumentos()
        host._presenter.on_progress.side_effect = RuntimeError("progress boom")
        job = MagicMock()
        job.fila = queue.Queue()
        job.fila.put((MENSAGEM_PROGRESSO, 1, 2, "• Documentos"))
        job.fila.put(True)
        host._documentos_job = job

        host._poll_documentos_job(job, "EXXO34")

        host._presenter.on_operation_finished.assert_called_once()
        assert host._documentos_job is None
        host._documents_panel.update.assert_called_once_with("EXXO34")

    def test_thread_morta_encerra_job_e_libera_cursor(self, caplog):
        host = _HostDocumentos()
        job = MagicMock()
        job.fila.get_nowait.side_effect = queue.Empty
        job.thread.is_alive.return_value = False
        job.fila.empty.return_value = True
        host._documentos_job = job
        host._documentos_ultima_atividade = time.monotonic()

        with caplog.at_level(logging.WARNING, logger="flowscope"):
            host._poll_documentos_job(job, "EXXO34")

        host._presenter.on_operation_finished.assert_called_once()
        assert host._documentos_job is None
        assert "sem progresso" in caplog.text

    def test_inatividade_encerra_job_e_libera_cursor(self, caplog):
        host = _HostDocumentos()
        job = MagicMock()
        job.fila.get_nowait.side_effect = queue.Empty
        job.thread.is_alive.return_value = True
        host._documentos_job = job
        host._documentos_ultima_atividade = time.monotonic() - 1000.0

        with caplog.at_level(logging.WARNING, logger="flowscope"):
            host._poll_documentos_job(job, "EXXO34")

        host._presenter.on_operation_finished.assert_called_once()
        assert host._documentos_job is None
        assert "sem progresso" in caplog.text


class TestCancelamentoDocumentos:
    def test_cancelamento_finaliza_e_suprime_sucesso(self, monkeypatch):
        host = _HostDocumentos()
        flashes: list[tuple] = []
        host._flash_status = lambda *args, **kwargs: flashes.append(args)
        monkeypatch.setattr(app_actions, "DocumentosJob", _JobFake)
        host._presenter.cancel_token.is_set = True

        host._adquirir_documentos("EXXO34")

        host._presenter.job_cancelavel_iniciado.assert_called_once()
        host._presenter.job_cancelavel_finalizado.assert_called_once()
        host._presenter.on_operation_finished.assert_called_once()
        assert flashes == []
        assert host._documentos_job is None

    def test_cancelamento_finaliza_sem_aguardar_terminal(self, monkeypatch):
        class _JobPendente:
            def __init__(self, *args, **kwargs):
                self.fila = queue.Queue()
                self.cancel_token = kwargs.get("cancel_token")

            def iniciar(self):
                return None

        host = _HostDocumentos()
        monkeypatch.setattr(app_actions, "DocumentosJob", _JobPendente)
        host._presenter.cancel_token.is_set = True

        host._adquirir_documentos("EXXO34")

        host._presenter.on_operation_finished.assert_called_once()
        assert host._documentos_job is None


class TestDocumentosJob:
    def test_publica_termino_apos_falha(self):
        class _AquisicaoFalha:
            def adquirir(self, ticker, reference_date, progress=None,
                         cancel_token=None):
                raise RuntimeError("offline")

        job = DocumentosJob(_AquisicaoFalha(), "PETR3", date(2026, 7, 29))
        job.iniciar().join()
        assert job.fila.get_nowait() is True

    def test_publica_progresso_antes_do_termino(self):
        class _AquisicaoProgresso:
            def adquirir(self, ticker, reference_date, progress=None,
                         cancel_token=None):
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

    def test_token_e_repassado_a_aquisicao(self):
        capturado = {}

        class _AquisicaoToken:
            def adquirir(self, ticker, reference_date, progress=None,
                         cancel_token=None):
                capturado["token"] = cancel_token

        token = CancellationToken()
        job = DocumentosJob(
            _AquisicaoToken(), "PETR3", date(2026, 7, 29), cancel_token=token
        )
        job.iniciar().join()
        assert capturado["token"] is token

    def test_cancelamento_nao_loga_falha(self, caplog):
        class _AquisicaoCancelada:
            def adquirir(self, ticker, reference_date, progress=None,
                         cancel_token=None):
                raise OperacaoCancelada()

        token = CancellationToken()
        token.request()
        job = DocumentosJob(
            _AquisicaoCancelada(), "PETR3", date(2026, 7, 29),
            cancel_token=token,
        )
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            job.iniciar().join()

        assert job.fila.get_nowait() is True
        assert "Falha na aquisição" not in caplog.text


class _PainelResumosFake:
    def __init__(self, pendentes, textos, falha_em=None):
        self._pendentes = list(pendentes)
        self._textos = textos
        self._falha_em = falha_em
        self.aplicados: list[str] = []
        self.refreshes = 0

    def documentos_sem_resumo(self):
        return list(self._pendentes)

    def preparar_texto(self, arquivo):
        return self._textos.get(arquivo.nome, "")

    def persistir_no_lote(self):
        return False

    def gerar_resumo_estrito(self, arquivo, texto):
        if self._falha_em == arquivo.nome:
            raise LLMCommunicationError("timeout")
        return ResumoDocumento("curto", "longo")

    def avaliar_guidance(self, arquivo, texto):
        return None

    def aplicar_resumo(self, arquivo, resumo):
        self.aplicados.append(arquivo.nome)

    def refresh_resumir_button(self):
        self.refreshes += 1


class _HostResumos(ActionsMixin, ResumosActionsMixin):
    def __init__(self, painel):
        self._documents_panel = painel
        self._presenter = MagicMock()
        self._ticker_selecionado = "ALZR11"
        self.agendados = []
        self.status = []

    def after(self, ms, callback):
        self.agendados.append((ms, callback))
        callback()
        return "id"

    def _set_status(self, msg, icon=""):
        self.status.append((msg, icon))

    def _flash_status(self, msg, icon="✓", clear_ms=2500):
        self.status.append((msg, icon))


def _preparar_poll(host):
    host._resumos_reporter = ProgressReporter(
        on_update=host._presenter.on_progress
    )
    host._resumos_fase = None
    host._resumos_resumidos = 0
    host._resumos_interrompido = False


class TestResumosEmAndamento:
    def test_falso_sem_job(self):
        host = _HostResumos(MagicMock())
        assert host._resumos_em_andamento() is False

    def test_verdadeiro_com_job(self):
        host = _HostResumos(MagicMock())
        host._resumos_job = object()
        assert host._resumos_em_andamento() is True


class TestOrquestrarResumos:
    def test_reentrancia_ignora_segundo_acionamento(self):
        painel = MagicMock()
        host = _HostResumos(painel)
        host._resumos_job = object()
        host._resumir_documentos_pendentes()
        painel.documentos_sem_resumo.assert_not_called()
        host._presenter.enter.assert_not_called()

    def test_sem_pendentes_reavalia_botao(self):
        painel = MagicMock()
        painel.documentos_sem_resumo.return_value = []
        host = _HostResumos(painel)
        host._resumir_documentos_pendentes()
        painel.refresh_resumir_button.assert_called_once()
        host._presenter.enter.assert_not_called()

    def test_atraso_minimo_ao_termino_da_fase(self):
        host = _HostResumos(MagicMock())
        host._resumos_fase_completa = True
        host._resumos_fase_inicio = time.monotonic()
        assert host._atraso_poll_resumos("processou") > 0

        host._resumos_fase_inicio = time.monotonic() - 10
        assert host._atraso_poll_resumos("processou") == 0
        assert host._atraso_poll_resumos("vazio") == 50

    def test_sem_atraso_durante_avanco_da_fase(self):
        host = _HostResumos(MagicMock())
        host._resumos_fase_inicio = time.monotonic()
        host._resumos_fase_completa = False
        assert host._atraso_poll_resumos("processou") == 0

    def test_balanceia_enter_exit(self, tmp_path, monkeypatch):
        arquivos = [_arquivo(tmp_path, "10.pdf")]
        painel = _PainelResumosFake(arquivos, {"10.pdf": "texto"})
        host = _HostResumos(painel)

        class _JobFake:
            def __init__(self, _painel, _arquivos, cancel_token=None):
                self.fila = queue.Queue()
                self.fila.put(True)
                self.total = len(_arquivos)
                self.sem_texto = 0
                self.thread = None

            def iniciar(self):
                return None

        monkeypatch.setattr(app_resumos_actions, "ResumosPendentesJob", _JobFake)
        host._resumir_documentos_pendentes()
        host._presenter.enter.assert_called_once()
        host._presenter.exit.assert_called_once()
        assert painel.refreshes == 1

    def test_cancelamento_suprime_desfecho(self, tmp_path):
        arquivos = [_arquivo(tmp_path, "10.pdf"), _arquivo(tmp_path, "20.pdf")]
        painel = _PainelResumosFake(
            arquivos, {"10.pdf": "texto", "20.pdf": "texto"}
        )
        host = _HostResumos(painel)
        _preparar_poll(host)
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        host._resumos_job = job
        host._presenter.cancel_token.is_set = True

        host._poll_resumos_job(job, "ALZR11")

        assert host._resumos_interrompido is True
        host._presenter.job_cancelavel_finalizado.assert_called_once()
        host._presenter.exit.assert_called_once()
        assert not any(
            msg.startswith("Resumos gerados") for msg, _icon in host.status
        )

    def test_progresso_resultado_e_desfecho(self, tmp_path):
        arquivos = [_arquivo(tmp_path, "10.pdf"), _arquivo(tmp_path, "20.pdf")]
        painel = _PainelResumosFake(arquivos, {"10.pdf": "texto", "20.pdf": ""})
        host = _HostResumos(painel)
        _preparar_poll(host)
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        host._resumos_job = job

        host._poll_resumos_job(job, "ALZR11")

        assert painel.aplicados == ["10.pdf"]
        host._presenter.on_progress.assert_called()
        assert any(
            "/" in chamada.args[2]
            for chamada in host._presenter.on_progress.call_args_list
        )
        assert any(
            "Resumos gerados: 1 de 2 (1 sem texto)." in msg
            for msg, _icon in host.status
        )

    def test_interrupcao_publica_status_e_libera(self, tmp_path):
        arquivos = [_arquivo(tmp_path, "10.pdf"), _arquivo(tmp_path, "20.pdf")]
        painel = _PainelResumosFake(
            arquivos, {"10.pdf": "texto", "20.pdf": "texto"},
            falha_em="20.pdf",
        )
        host = _HostResumos(painel)
        _preparar_poll(host)
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        host._resumos_job = job

        host._poll_resumos_job(job, "ALZR11")

        assert painel.aplicados == ["10.pdf"]
        assert any(
            msg.startswith("20.pdf: ") and "conectar ao serviço de I.A." in msg
            for msg, _icon in host.status
        )
        assert all("timeout" not in msg for msg, _icon in host.status)
        host._presenter.exit.assert_called_once()

    def test_descarta_resultado_ao_trocar_ticker(self, tmp_path):
        arquivos = [_arquivo(tmp_path, "10.pdf")]
        painel = _PainelResumosFake(arquivos, {"10.pdf": "texto"})
        host = _HostResumos(painel)
        _preparar_poll(host)
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        host._resumos_job = job
        host._ticker_selecionado = "OUTRO"

        host._poll_resumos_job(job, "ALZR11")

        assert painel.aplicados == []

    @needs_display
    def test_lote_ativo_mantem_botao_desabilitado_e_reabilita(self, tmp_path):
        root = tk.Tk()
        try:
            host = _HostResumos(MagicMock())
            host._resumos_job = object()
            store = JsonDocumentSummaryStore(cache_dir=tmp_path)
            catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
            _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
            painel = DocumentTreePanel(
                root, catalog=catalogo, summary_store=store,
                llm_available=lambda: True,
                resumir_ativo_callback=host._resumos_em_andamento,
                debounce_ms=0,
            )
            painel.update("ALZR11")
            assert str(painel._resumir_btn.cget("state")) == "disabled"

            host._resumos_job = None
            painel.refresh_resumir_button()
            assert str(painel._resumir_btn.cget("state")) == "normal"
        finally:
            root.destroy()

    @needs_display
    def test_lote_termina_sem_pendentes_permanece_desabilitado(self, tmp_path):
        root = tk.Tk()
        try:
            host = _HostResumos(MagicMock())
            host._resumos_job = object()
            store = JsonDocumentSummaryStore(cache_dir=tmp_path)
            store.salvar("ALZR11", "bdr/ALZR11/2026/02/10.pdf", "c", "l")
            catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
            _touch(catalogo.base_dir / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
            painel = DocumentTreePanel(
                root, catalog=catalogo, summary_store=store,
                llm_available=lambda: True,
                resumir_ativo_callback=host._resumos_em_andamento,
                debounce_ms=0,
            )
            painel.update("ALZR11")
            assert str(painel._resumir_btn.cget("state")) == "disabled"

            host._resumos_job = None
            painel.refresh_resumir_button()
            assert str(painel._resumir_btn.cget("state")) == "disabled"
        finally:
            root.destroy()


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
    def test_sem_texto_nao_chama_llm_nem_persiste(self, tmp_path):
        root = tk.Tk()
        try:
            llm = _LLMFake("CURTO: curto\nLONGO: longo")
            store = JsonDocumentSummaryStore(cache_dir=tmp_path)
            text_store = JsonDocumentTextStore(cache_dir=tmp_path)
            catalogo = DocumentCatalog(
                cache_dir=tmp_path, summary_store=store, text_store=text_store
            )
            _touch(
                catalogo.base_dir / "informe-mensal" / "ALZR11" / "2026"
                / "02" / "20.html",
                b"<html><body></body></html>",
            )
            painel = DocumentTreePanel(
                root, catalog=catalogo, summary_store=store,
                text_store=text_store, llm_available=lambda: True,
                llm_factory=lambda: llm, debounce_ms=0,
            )
            painel.update("ALZR11")
            no = _no_arquivo(painel, "20.html")
            painel._tree.selection_set(no)
            assert _pump(
                root, lambda: painel._preview.get("1.0", "end-1c") == SEM_TEXTO
            )
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
