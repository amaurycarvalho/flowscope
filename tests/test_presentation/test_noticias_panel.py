"""Testes do painel de notícias, do job de aquisição e dos resumos em lote."""

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
from flowscope.domain.llm import LLMCommunicationError
from flowscope.domain.structured import CensuraPublica, NoticiaB3
from flowscope.infrastructure.b3.noticias_aquisicao import (
    ESCOPO_NOTICIAS,
    SECAO_CENSURAS,
    SECAO_CONDICOES,
    SECAO_GERAL,
    SECAO_PROGRAMAS,
    NoticiasCache,
    chave_item,
    chave_noticia,
    classificar_tipo,
    data_noticia,
    html_do_item,
    item_de_censura,
)
from flowscope.infrastructure.b3.noticias_catalogo import (
    NoticiaArquivo,
    NoticiasCatalog,
)
from flowscope.infrastructure.b3.noticias_index import (
    NoticiaMeta,
    NoticiasIndexStore,
)
from flowscope.infrastructure.document_summaries import (
    JsonDocumentSummaryStore,
    chave_documento,
)
from flowscope.infrastructure.document_texts import JsonDocumentTextStore
from flowscope.presentation.gui import noticias_actions
from flowscope.presentation.gui.app_actions import ActionsMixin
from flowscope.presentation.gui.app_resumos_actions import ResumosActionsMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.app_tabs import TAB_CONTENT
from flowscope.presentation.gui.charts import noticias_panel as noticias_panel_mod
from flowscope.presentation.gui.charts.document_summary import DocumentSummaryService
from flowscope.presentation.gui.charts.noticias_panel import NoticiasPanel
from flowscope.presentation.gui.noticias_actions import NoticiasActionsMixin
from flowscope.presentation.gui.noticias_job import (
    MENSAGEM_PROGRESSO,
    NoticiasJob,
)
from flowscope.presentation.gui.resumos_job import (
    MENSAGEM_ERRO,
    MENSAGEM_RESULTADO,
    ResumosPendentesJob,
)
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)

_REFERENCIA = date(2026, 9, 25)


@pytest.fixture(autouse=True)
def _sem_llm_por_padrao(monkeypatch):
    """Torna a disponibilidade da LLM determinística nos testes do painel."""
    monkeypatch.setattr(
        "flowscope.presentation.gui.charts.document_summary.llm_configurada",
        lambda: False,
    )


class _LLMFake:
    """Porta de LLM que registra chamadas e devolve resumos configurados."""

    def __init__(self, resposta="CURTO: resumo curto\nLONGO: resumo longo"):
        self.resposta = resposta
        self.chamadas: list[list[dict]] = []

    def complete(self, messages, system_prompt=None):
        self.chamadas.append(messages)
        return self.resposta


def _noticia(
    titulo="PETROBRAS (PETR4) - Suspensão de negociação",
    url="https://x/1",
    data_publicacao="2026-09-20 10:00:00",
) -> NoticiaB3:
    return NoticiaB3(
        titulo=titulo,
        data_publicacao=data_publicacao,
        url=url,
        agencia="18",
    )


def _semear(tmp_path, noticias):
    cache = NoticiasCache(tmp_path)
    indice = NoticiasIndexStore(cache_dir=tmp_path)
    for noticia in noticias:
        data = data_noticia(noticia.data_publicacao, _REFERENCIA)
        chave = chave_noticia(noticia)
        html = f"<html><body><pre>Corpo {noticia.titulo}</pre></body></html>"
        cache.gravar(chave, data, html.encode("utf-8"))
        indice.registrar(
            cache.caminho(chave, data),
            NoticiaMeta(
                secao=SECAO_GERAL,
                titulo=noticia.titulo,
                data_publicacao=noticia.data_publicacao,
                categoria=classificar_tipo(noticia.titulo),
                url=noticia.url,
            ),
        )
    return NoticiasCatalog(cache_dir=tmp_path)


def _pump(root, condicao, timeout=3.0):
    limite = time.time() + timeout
    while time.time() < limite:
        root.update()
        if condicao():
            return True
        time.sleep(0.01)
    return condicao()


def _tipos_do_job(job):
    """Drena a fila de um job e retorna os tipos de mensagem publicados."""
    tipos: list[str] = []
    while True:
        mensagem = job.fila.get_nowait()
        if mensagem is True:
            break
        tipos.append(mensagem[0])
    return tipos


def _no_arquivo(painel, nome):
    for iid, arquivo in painel._itens.items():
        if arquivo.nome == nome:
            return iid
    raise AssertionError(f"notícia {nome} não encontrada na árvore")


def _arquivo_por_nome(painel, nome):
    for arquivo in painel._itens.values():
        if arquivo.nome == nome:
            return arquivo
    raise AssertionError(f"notícia {nome} não encontrada na árvore")


class TestConstrucao:
    @needs_display
    def test_constroi_widgets(self, tmp_path):
        root = tk.Tk()
        try:
            painel = NoticiasPanel(
                root,
                catalog=NoticiasCatalog(cache_dir=tmp_path),
                debounce_ms=0,
            )
            assert isinstance(painel._preview, ReadonlyText)
            assert len(painel.all_buttons()) == 4
            assert painel.texto_atual() == ""
            assert "Atualizar" in painel._empty_label.cget("text")
        finally:
            root.destroy()


def _aberto(tree, no):
    """Indica se um nó do Treeview está expandido, tolerando tipos do Tk."""
    return tree.item(no, "open") in (1, True, "1", "true", "True")


class TestArvorePreview:
    @needs_display
    def test_arvore_expandida_so_ate_o_primeiro_nivel(self, tmp_path):
        noticia = _noticia()
        catalogo = _semear(tmp_path, [noticia])
        root = tk.Tk()
        try:
            painel = NoticiasPanel(root, catalog=catalogo, debounce_ms=0)
            painel.update(_REFERENCIA)
            raiz = painel._tree.get_children()[0]
            assert _aberto(painel._tree, raiz) is True
            for secao in painel._tree.get_children(raiz):
                assert _aberto(painel._tree, secao) is False
        finally:
            root.destroy()

    @needs_display
    def test_arvore_lista_noticias_em_cache(self, tmp_path):
        noticia = _noticia()
        catalogo = _semear(tmp_path, [noticia])
        root = tk.Tk()
        try:
            painel = NoticiasPanel(root, catalog=catalogo, debounce_ms=0)
            painel.update(_REFERENCIA)
            assert _no_arquivo(painel, noticia.titulo) is not None
        finally:
            root.destroy()

    @needs_display
    def test_selecao_exibe_texto_e_persiste(self, tmp_path):
        noticia = _noticia(titulo="Unica - Suspensão de negociação")
        catalogo = _semear(tmp_path, [noticia])
        text_store = JsonDocumentTextStore(cache_dir=tmp_path)
        root = tk.Tk()
        try:
            painel = NoticiasPanel(
                root, catalog=catalogo, text_store=text_store, debounce_ms=0
            )
            painel.update(_REFERENCIA)
            painel._view.tree.selection_set(_no_arquivo(painel, noticia.titulo))
            painel._on_select()
            assert _pump(root, lambda: "Corpo Unica" in painel.texto_atual())
            chave = catalogo.chave(_arquivo_por_nome(painel, noticia.titulo))
            assert text_store.obter(ESCOPO_NOTICIAS, chave) is not None
        finally:
            root.destroy()

    @needs_display
    def test_estado_vazio_sem_cache(self, tmp_path):
        catalogo = NoticiasCatalog(cache_dir=tmp_path)
        root = tk.Tk()
        try:
            painel = NoticiasPanel(root, catalog=catalogo, debounce_ms=0)
            painel.update(_REFERENCIA)
            assert "Sem notícias" in painel._empty_label.cget("text")
        finally:
            root.destroy()

    @needs_display
    def test_cache_frio_nao_quebra(self, tmp_path):
        cache = NoticiasCache(tmp_path)
        NoticiasIndexStore(cache_dir=tmp_path).registrar(
            cache.caminho("ausente", _REFERENCIA),
            NoticiaMeta(
                secao=SECAO_GERAL,
                titulo="Sem corpo",
                data_publicacao="2026-09-20 10:00:00",
                categoria="18",
                url="https://x/1",
            ),
        )
        catalogo = NoticiasCatalog(cache_dir=tmp_path)
        root = tk.Tk()
        try:
            painel = NoticiasPanel(root, catalog=catalogo, debounce_ms=0)
            painel.update(_REFERENCIA)
            assert "Sem notícias" in painel._empty_label.cget("text")
        finally:
            root.destroy()


def _semear_censura(tmp_path, censura):
    item = item_de_censura(censura)
    cache = NoticiasCache(tmp_path)
    data = data_noticia(item.data_publicacao, _REFERENCIA)
    chave = chave_item(item)
    cache.gravar(chave, data, html_do_item(item))
    NoticiasIndexStore(cache_dir=tmp_path).registrar(
        cache.caminho(chave, data),
        NoticiaMeta(
            secao=item.secao,
            titulo=item.titulo,
            data_publicacao=item.data_publicacao,
            categoria=item.categoria,
            url=item.url,
        ),
    )
    return NoticiasCatalog(cache_dir=tmp_path)


class TestSecoesPainel:
    @needs_display
    def test_arvore_exibe_secao_regulatoria(self, tmp_path):
        censura = CensuraPublica(
            titulo="FII TORDE EI (TORD)",
            ticker="TORD",
            data="25/02/2026",
            conteudo="Corpo da censura.",
        )
        catalogo = _semear_censura(tmp_path, censura)
        root = tk.Tk()
        try:
            painel = NoticiasPanel(root, catalog=catalogo, debounce_ms=0)
            painel.update(_REFERENCIA)
            raiz = painel._tree.get_children()[0]
            assert painel._tree.item(raiz, "text") == "Notícias"
            secoes = [
                painel._tree.item(no, "text")
                for no in painel._tree.get_children(raiz)
            ]
            assert secoes == [SECAO_CENSURAS]
        finally:
            root.destroy()

    @needs_display
    def test_selecao_da_raiz_renderiza_secoes(self, tmp_path):
        censura = CensuraPublica(
            titulo="FII TORDE EI (TORD)",
            ticker="TORD",
            data="25/02/2026",
            conteudo="Corpo da censura.",
        )
        catalogo = _semear_censura(tmp_path, censura)
        root = tk.Tk()
        try:
            painel = NoticiasPanel(root, catalog=catalogo, debounce_ms=0)
            painel.update(_REFERENCIA)
            raiz = painel._tree.get_children()[0]
            painel._tree.selection_set(raiz)
            painel._on_select()
            assert SECAO_CENSURAS in painel.texto_atual()
        finally:
            root.destroy()


class TestExtracaoNoticias:
    def test_texto_do_arquivo_isola_corpo_do_artigo(self, tmp_path):
        caminho = tmp_path / "noticia.html"
        caminho.write_text(
            "<html><body><div>Moldura da pagina</div>"
            "<pre id='conteudoDetalhe'>Corpo do artigo</pre>"
            "<footer>Rodape</footer></body></html>",
            encoding="utf-8",
        )
        arquivo = NoticiaArquivo(
            ticker=ESCOPO_NOTICIAS,
            ano=2026,
            mes=9,
            categoria="18",
            nome="noticia",
            tipo="html",
            caminho=caminho,
            url="https://x/1",
        )
        painel = NoticiasPanel.__new__(NoticiasPanel)
        assert painel._texto_do_arquivo(arquivo) == "Corpo do artigo"

    def test_geral_usa_documento_vinculado(self, tmp_path, monkeypatch):
        caminho = tmp_path / "noticia.html"
        caminho.write_text(
            "<html><body><pre id='conteudoDetalhe'>"
            "Titulo\nhttps://www.rad.cvm.gov.br/ENETWEB/frmExibirArquivoIPEExterno.aspx?ID=1&flnk"
            "</pre></body></html>",
            encoding="utf-8",
        )
        arquivo = NoticiaArquivo(
            ticker=ESCOPO_NOTICIAS,
            ano=2026,
            mes=9,
            categoria="18",
            nome="noticia",
            tipo="html",
            caminho=caminho,
            secao=SECAO_GERAL,
            url="https://x/1",
        )
        monkeypatch.setattr(
            noticias_panel_mod,
            "baixar_conteudo_vinculado",
            lambda _texto: "texto do documento",
        )
        painel = NoticiasPanel.__new__(NoticiasPanel)
        resultado = painel._texto_do_arquivo(arquivo)
        assert resultado == "texto do documento"
        assert "Titulo" not in resultado

    def test_geral_sem_vinculo_mantem_corpo(self, tmp_path, monkeypatch):
        caminho = tmp_path / "noticia.html"
        caminho.write_text(
            "<html><body><pre id='conteudoDetalhe'>Corpo</pre></body></html>",
            encoding="utf-8",
        )
        arquivo = NoticiaArquivo(
            ticker=ESCOPO_NOTICIAS,
            ano=2026,
            mes=9,
            categoria="18",
            nome="noticia",
            tipo="html",
            caminho=caminho,
            secao=SECAO_GERAL,
            url="https://x/1",
        )
        monkeypatch.setattr(
            noticias_panel_mod,
            "baixar_conteudo_vinculado",
            lambda _texto: None,
        )
        painel = NoticiasPanel.__new__(NoticiasPanel)
        assert painel._texto_do_arquivo(arquivo) == "Corpo"

    def test_regulatoria_nao_baixa_vinculo(self, tmp_path, monkeypatch):
        chamadas: list = []
        monkeypatch.setattr(
            noticias_panel_mod,
            "baixar_conteudo_vinculado",
            lambda texto: chamadas.append(texto) or "x",
        )
        caminho = tmp_path / "n.html"
        caminho.write_text(
            "<html><body><pre id='conteudoDetalhe'>Corpo</pre></body></html>",
            encoding="utf-8",
        )
        arquivo = NoticiaArquivo(
            ticker=ESCOPO_NOTICIAS,
            ano=2026,
            mes=2,
            categoria="TORD",
            nome="n",
            tipo="html",
            caminho=caminho,
            secao=SECAO_CENSURAS,
            url=None,
        )
        painel = NoticiasPanel.__new__(NoticiasPanel)
        assert painel._texto_do_arquivo(arquivo) == "Corpo"
        assert chamadas == []


class TestAutoRecuperacao:
    @staticmethod
    def _painel_cache(tmp_path):
        painel = NoticiasPanel.__new__(NoticiasPanel)
        painel._preview_cache = {}
        painel._text_store = JsonDocumentTextStore(cache_dir=tmp_path)
        painel._summary = DocumentSummaryService(
            JsonDocumentSummaryStore(cache_dir=tmp_path), tmp_path
        )
        return painel

    @staticmethod
    def _arquivo_geral(tmp_path):
        caminho = tmp_path / "noticia.html"
        caminho.write_text(
            "<html><body><pre id='conteudoDetalhe'>Titulo\n"
            "https://www.rad.cvm.gov.br/ENETWEB/frmExibirArquivoIPEExterno.aspx"
            "?ID=1&flnk</pre></body></html>",
            encoding="utf-8",
        )
        return NoticiaArquivo(
            ticker=ESCOPO_NOTICIAS,
            ano=2026,
            mes=9,
            categoria="18",
            nome="noticia",
            tipo="html",
            caminho=caminho,
            secao=SECAO_GERAL,
            url="https://x/1",
        )

    def _semear_texto(self, painel, tmp_path, arquivo, texto):
        painel._text_store.salvar(
            arquivo.ticker, chave_documento(arquivo.caminho, tmp_path), texto
        )

    def test_cache_de_apontador_e_invalidado(self, tmp_path):
        painel = self._painel_cache(tmp_path)
        arquivo = self._arquivo_geral(tmp_path)
        apontador = (
            "Titulo\nhttps://www.rad.cvm.gov.br/ENETWEB/"
            "frmExibirArquivoIPEExterno.aspx?ID=1&flnk"
        )
        self._semear_texto(painel, tmp_path, arquivo, apontador)
        assert painel._texto_cacheado(arquivo) is None

    def test_cache_de_documento_resolvido_e_reutilizado(self, tmp_path):
        painel = self._painel_cache(tmp_path)
        arquivo = self._arquivo_geral(tmp_path)
        self._semear_texto(painel, tmp_path, arquivo, "CONTEUDO DO DOCUMENTO")
        assert painel._texto_cacheado(arquivo) == "CONTEUDO DO DOCUMENTO"

    def test_documento_resolvido_que_cita_url_e_reutilizado(self, tmp_path):
        painel = self._painel_cache(tmp_path)
        arquivo = self._arquivo_geral(tmp_path)
        resolvido = (
            "Ofício cita https://www.rad.cvm.gov.br/ENET/"
            "frmExibirArquivoIPEExterno.aspx?ID=9&flnk"
        )
        self._semear_texto(painel, tmp_path, arquivo, resolvido)
        assert painel._texto_cacheado(arquivo) == resolvido

    def test_preparar_texto_reprocessa_apontador_falho(self, tmp_path, monkeypatch):
        painel = self._painel_cache(tmp_path)
        arquivo = self._arquivo_geral(tmp_path)
        chamadas: list[str] = []

        def _baixar(texto):
            chamadas.append(texto)
            return None if len(chamadas) == 1 else "CONTEUDO DO DOCUMENTO"

        monkeypatch.setattr(
            noticias_panel_mod, "baixar_conteudo_vinculado", _baixar
        )
        primeiro = painel.preparar_texto(arquivo)
        assert "frmExibirArquivoIPEExterno" in primeiro
        segundo = painel.preparar_texto(arquivo)
        assert segundo == "CONTEUDO DO DOCUMENTO"
        assert len(chamadas) == 2

    def _painel_com_llm(self, tmp_path, store, llm):
        painel = self._painel_cache(tmp_path)
        painel._summary = DocumentSummaryService(
            store, tmp_path, llm_factory=lambda: llm, llm_available=lambda: True
        )
        return painel

    def test_lote_pula_apontador_e_mantem_pendente(self, tmp_path, monkeypatch):
        arquivo = self._arquivo_geral(tmp_path)
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        llm = _LLMFake()
        painel = self._painel_com_llm(tmp_path, store, llm)
        monkeypatch.setattr(
            noticias_panel_mod, "baixar_conteudo_vinculado", lambda _texto: None
        )
        job = ResumosPendentesJob(painel, [arquivo], continuar_em_erro=True)
        job.iniciar().join()
        assert job.sem_texto == 1
        assert llm.chamadas == []
        assert MENSAGEM_RESULTADO not in _tipos_do_job(job)
        chave = chave_documento(arquivo.caminho, tmp_path)
        assert store.obter(ESCOPO_NOTICIAS, chave) is None

    def test_lote_resume_quando_documento_resolve(self, tmp_path, monkeypatch):
        arquivo = self._arquivo_geral(tmp_path)
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        llm = _LLMFake()
        painel = self._painel_com_llm(tmp_path, store, llm)
        monkeypatch.setattr(
            noticias_panel_mod,
            "baixar_conteudo_vinculado",
            lambda _texto: "CONTEUDO DO DOCUMENTO",
        )
        job = ResumosPendentesJob(painel, [arquivo], continuar_em_erro=True)
        job.iniciar().join()
        assert job.sem_texto == 0
        assert llm.chamadas
        assert "CONTEUDO DO DOCUMENTO" in llm.chamadas[0][0]["content"]
        assert MENSAGEM_RESULTADO in _tipos_do_job(job)


class TestAbertura:
    @needs_display
    def test_abre_url_no_callback(self, tmp_path):
        noticia = _noticia(titulo="Abrir - Suspensão de negociação")
        catalogo = _semear(tmp_path, [noticia])
        abertas: list[str] = []
        root = tk.Tk()
        try:
            painel = NoticiasPanel(
                root,
                catalog=catalogo,
                open_callback=abertas.append,
                debounce_ms=0,
            )
            painel.update(_REFERENCIA)
            painel._view.tree.selection_set(_no_arquivo(painel, noticia.titulo))
            painel._on_select()
            painel._open_btn.invoke()
            assert abertas == [noticia.url]
        finally:
            root.destroy()

    def test_abrir_sem_url_informa_status(self, tmp_path):
        status: list[tuple] = []
        painel = NoticiasPanel.__new__(NoticiasPanel)
        painel._status_callback = lambda msg, icon="": status.append((msg, icon))
        painel._open_callback = lambda url: None
        arquivo = NoticiaArquivo(
            ticker=ESCOPO_NOTICIAS,
            ano=2026,
            mes=9,
            categoria="18",
            nome="Sem URL",
            tipo="html",
            caminho=tmp_path / "x.html",
            url=None,
        )
        painel._abrir(arquivo)
        assert status and "sem URL" in status[0][0]

    @needs_display
    def test_botao_abrir_desabilitado_sem_selecao(self, tmp_path):
        catalogo = _semear(tmp_path, [_noticia()])
        root = tk.Tk()
        try:
            painel = NoticiasPanel(root, catalog=catalogo, debounce_ms=0)
            painel.update(_REFERENCIA)
            assert str(painel._open_btn.cget("state")) == "disabled"
        finally:
            root.destroy()


class TestCallbacks:
    @needs_display
    def test_acquire_ia_e_resumir(self, tmp_path):
        catalogo = _semear(tmp_path, [_noticia()])
        root = tk.Tk()
        try:
            chamadas: list[str] = []
            painel = NoticiasPanel(
                root,
                catalog=catalogo,
                acquire_callback=lambda: chamadas.append("atualizar"),
                ia_callback=lambda: chamadas.append("ia"),
                resumir_callback=lambda: chamadas.append("resumir"),
                llm_available=lambda: True,
                debounce_ms=0,
            )
            painel.update(_REFERENCIA)
            painel._refresh_btn.invoke()
            painel._ia_btn.invoke()
            painel._resumir_btn.config(state=tk.NORMAL)
            painel._resumir_btn.invoke()
            assert chamadas == ["atualizar", "ia", "resumir"]
        finally:
            root.destroy()

    @needs_display
    def test_resumir_ativo_desabilita_botao(self, tmp_path):
        catalogo = _semear(tmp_path, [_noticia()])
        root = tk.Tk()
        try:
            painel = NoticiasPanel(
                root,
                catalog=catalogo,
                llm_available=lambda: True,
                resumir_ativo_callback=lambda: True,
                debounce_ms=0,
            )
            painel.update(_REFERENCIA)
            assert str(painel._resumir_btn.cget("state")) == "disabled"
        finally:
            root.destroy()


class TestResumos:
    @needs_display
    def test_gerar_resumo_persiste(self, tmp_path):
        noticia = _noticia(titulo="Resumivel - Suspensão de negociação")
        catalogo = _semear(tmp_path, [noticia])
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        llm = _LLMFake()
        root = tk.Tk()
        try:
            painel = NoticiasPanel(
                root,
                catalog=catalogo,
                summary_store=store,
                llm_factory=lambda: llm,
                llm_available=lambda: True,
                debounce_ms=0,
            )
            painel.update(_REFERENCIA)
            painel._view.tree.selection_set(_no_arquivo(painel, noticia.titulo))
            painel._on_select()
            assert _pump(root, lambda: "resumo longo" in painel.texto_atual())
            chave = catalogo.chave(_arquivo_por_nome(painel, noticia.titulo))
            assert store.obter(ESCOPO_NOTICIAS, chave).long_summary == "resumo longo"
        finally:
            root.destroy()

    @needs_display
    def test_resumir_pendentes_usa_documento_vinculado(self, tmp_path, monkeypatch):
        cache = NoticiasCache(tmp_path)
        indice = NoticiasIndexStore(cache_dir=tmp_path)
        noticia = _noticia(titulo="Vinculo - Suspensão de negociação")
        data = data_noticia(noticia.data_publicacao, _REFERENCIA)
        chave = chave_noticia(noticia)
        html = (
            "<html><body><pre id='conteudoDetalhe'>Titulo\n"
            "https://www.rad.cvm.gov.br/ENETWEB/frmExibirArquivoIPEExterno.aspx"
            "?ID=1&flnk</pre></body></html>"
        )
        cache.gravar(chave, data, html.encode("utf-8"))
        indice.registrar(
            cache.caminho(chave, data),
            NoticiaMeta(
                secao=SECAO_GERAL,
                titulo=noticia.titulo,
                data_publicacao=noticia.data_publicacao,
                categoria=classificar_tipo(noticia.titulo),
                url=noticia.url,
            ),
        )
        catalogo = NoticiasCatalog(cache_dir=tmp_path)
        monkeypatch.setattr(
            noticias_panel_mod,
            "baixar_conteudo_vinculado",
            lambda _texto: "CONTEUDO DO ARQUIVO VINCULADO",
        )
        llm = _LLMFake()
        root = tk.Tk()
        try:
            painel = NoticiasPanel(
                root,
                catalog=catalogo,
                llm_factory=lambda: llm,
                llm_available=lambda: True,
                debounce_ms=0,
            )
            painel.update(_REFERENCIA)
            job = ResumosPendentesJob(
                painel, list(painel._itens.values()), continuar_em_erro=True
            )
            job.iniciar().join()
            prompt = llm.chamadas[0][0]["content"]
            assert "CONTEUDO DO ARQUIVO VINCULADO" in prompt
            assert "frmExibirArquivoIPEExterno" not in prompt
        finally:
            root.destroy()

    @needs_display
    def test_sem_llm_orienta_configuracao(self, tmp_path):
        noticia = _noticia(titulo="SemLLM - Suspensão de negociação")
        catalogo = _semear(tmp_path, [noticia])
        root = tk.Tk()
        try:
            painel = NoticiasPanel(
                root,
                catalog=catalogo,
                llm_available=lambda: False,
                debounce_ms=0,
            )
            painel.update(_REFERENCIA)
            painel._view.tree.selection_set(_no_arquivo(painel, noticia.titulo))
            painel._on_select()
            assert _pump(root, lambda: "Configure a LLM" in painel.texto_atual())
        finally:
            root.destroy()

    def test_falha_da_llm_no_lote_continua(self):
        arquivos = [
            _arquivo_lote("A", Path("/tmp/a.html")),
            _arquivo_lote("B", Path("/tmp/b.html")),
            _arquivo_lote("C", Path("/tmp/c.html")),
        ]

        class _PainelLote:
            def preparar_texto(self, arquivo):
                return "texto"

            def gerar_resumo_estrito(self, arquivo, texto):
                if arquivo.nome == "B":
                    raise LLMCommunicationError("falha")
                return ResumoDocumento("curto", "longo")

            def avaliar_guidance(self, arquivo, texto):
                return None

        job = ResumosPendentesJob(
            _PainelLote(), arquivos, continuar_em_erro=True
        )
        job.iniciar().join()

        tipos: list[str] = []
        while True:
            mensagem = job.fila.get_nowait()
            if mensagem is True:
                break
            tipos.append(mensagem[0])
        assert tipos.count(MENSAGEM_RESULTADO) == 2
        assert tipos.count(MENSAGEM_ERRO) == 1


def _arquivo_lote(nome, caminho):
    return NoticiaArquivo(
        ticker=ESCOPO_NOTICIAS,
        ano=2026,
        mes=9,
        categoria="18",
        nome=nome,
        tipo="html",
        caminho=caminho,
        url="https://x/1",
    )


class TestNoticiasJob:
    def test_publica_progresso_e_termino(self):
        class _Aquisicao:
            def adquirir(self, reference_date, progress=None, cancel_token=None):
                progress(1, 2, "• Notícias (1/2)")

        job = NoticiasJob(_Aquisicao(), _REFERENCIA)
        job.iniciar().join()
        assert job.fila.get_nowait() == (
            MENSAGEM_PROGRESSO,
            1,
            2,
            "• Notícias (1/2)",
        )
        assert job.fila.get_nowait() is True

    def test_cancelamento_nao_loga_falha(self, caplog):
        class _AquisicaoCancelada:
            def adquirir(self, reference_date, progress=None, cancel_token=None):
                raise OperacaoCancelada()

        token = CancellationToken()
        token.request()
        job = NoticiasJob(_AquisicaoCancelada(), _REFERENCIA, cancel_token=token)
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            job.iniciar().join()
        assert job.fila.get_nowait() is True
        assert "Falha na aquisição" not in caplog.text


class _NoticiasJobFake:
    def __init__(self, aquisicao, reference_date, cancel_token=None):
        self._aquisicao = aquisicao
        self._reference_date = reference_date
        self.cancel_token = cancel_token
        self.fila = queue.Queue()

    def iniciar(self):
        try:
            self._aquisicao.adquirir(self._reference_date)
        except Exception:
            pass
        finally:
            self.fila.put(True)


class _HostNoticias(ActionsMixin, NoticiasActionsMixin):
    def __init__(self, painel):
        self._noticias_panel = painel
        self._aquisicao_noticias = MagicMock()
        self._presenter = MagicMock()
        self._noticias_job = None
        self._data = _REFERENCIA
        self.status: list[tuple] = []

    def _data_referencia(self):
        return self._data

    def after(self, ms, callback):
        callback()
        return "id"

    def _set_status(self, msg, icon=""):
        self.status.append((msg, icon))

    def _flash_status(self, msg, icon="✓", clear_ms=2500):
        self.status.append((msg, icon))


class TestNoticiasActions:
    def test_atualiza_painel_com_data_de_referencia(self):
        painel = MagicMock()
        host = _HostNoticias(painel)
        host._update_noticias()
        painel.update.assert_called_once_with(_REFERENCIA)

    def test_adquirir_executa_e_remonta(self, monkeypatch):
        painel = MagicMock()
        host = _HostNoticias(painel)
        monkeypatch.setattr(noticias_actions, "NoticiasJob", _NoticiasJobFake)
        host._adquirir_noticias()
        host._aquisicao_noticias.adquirir.assert_called_once_with(_REFERENCIA)
        painel.mostrar_carregando.assert_called_once()
        painel.update.assert_called_once_with(_REFERENCIA)
        assert host._noticias_job is None

    def test_sem_aquisicao_apenas_atualiza(self):
        painel = MagicMock()
        host = _HostNoticias(painel)
        host._aquisicao_noticias = None
        host._adquirir_noticias()
        painel.update.assert_called_once_with(_REFERENCIA)

    def test_falha_ao_iniciar_libera_cursor(self, monkeypatch):
        class _JobFalhaInicio:
            def __init__(self, *args, **kwargs):
                self.fila = queue.Queue()

            def iniciar(self):
                raise RuntimeError("thread boom")

        painel = MagicMock()
        host = _HostNoticias(painel)
        monkeypatch.setattr(noticias_actions, "NoticiasJob", _JobFalhaInicio)
        host._adquirir_noticias()
        host._presenter.on_operation_finished.assert_called_once()
        assert host._noticias_job is None

    def test_cancelamento_reagenda_remontagem_apos_worker(self):
        painel = MagicMock()
        host = _HostNoticias(painel)

        class _Thread:
            def __init__(self):
                self.chamadas = 0

            def is_alive(self):
                self.chamadas += 1
                return self.chamadas == 1

        class _Job:
            def __init__(self):
                self.fila = queue.Queue()
                self.thread = _Thread()

        host._cancelamento_solicitado = lambda: True
        job = _Job()
        host._noticias_job = job
        host._finalizar_noticias_job(job)

        assert host._noticias_job is None
        assert painel.update.call_count == 2
        host._presenter.job_cancelavel_finalizado.assert_called_once()
        host._presenter.on_operation_finished.assert_called_once()

    def test_cancelamento_nao_sobrescreve_novo_job(self):
        painel = MagicMock()
        host = _HostNoticias(painel)
        pendentes: list = []
        host.after = lambda ms, cb: pendentes.append(cb)

        class _Thread:
            def __init__(self):
                self.chamadas = 0

            def is_alive(self):
                self.chamadas += 1
                return self.chamadas == 1

        class _Job:
            def __init__(self):
                self.fila = queue.Queue()
                self.thread = _Thread()

        host._cancelamento_solicitado = lambda: True
        job = _Job()
        host._noticias_job = job
        host._finalizar_noticias_job(job)
        assert painel.update.call_count == 1
        assert pendentes

        host._noticias_job = object()  # um novo "Atualizar" começou
        pendentes.pop(0)()
        assert painel.update.call_count == 1


class _HostAbas(TabsLayoutMixin):
    def __init__(self):
        self._prefs = {}
        self._copy_chart = lambda *args, **kwargs: None

    def _data_referencia(self):
        return _REFERENCIA

    def _on_fundamental_widths_changed(self, widths):
        return None

    def _on_quadrant_summary(self, summary):
        return None


class TestWiringSubAba:
    @needs_display
    def test_registra_noticias_na_analise_geral(self):
        root = tk.Tk()
        try:
            host = _HostAbas()
            host._general_notebook = ttk.Notebook(root)
            host._build_general_tabs()
            abas = [
                host._general_notebook.tab(i, "text")
                for i in range(host._general_notebook.index("end"))
            ]
            assert "Notícias" in abas
            assert hasattr(host, "_noticias_panel")
        finally:
            root.destroy()

    def test_tab_content_documentado(self):
        assert ("Análise Geral", "Notícias") in TAB_CONTENT


def _arq_noticia(
    secao,
    nome,
    data="",
    *,
    ano=2026,
    mes=9,
    categoria="cat",
    resumo=None,
):
    return NoticiaArquivo(
        ticker=ESCOPO_NOTICIAS,
        ano=ano,
        mes=mes,
        categoria=categoria,
        nome=nome,
        tipo="html",
        caminho=Path(f"/tmp/{nome}"),
        long_summary=resumo,
        url="https://x/1",
        data_publicacao=data,
        secao=secao,
    )


class TestOrdemDoLote:
    @needs_display
    def test_ordena_por_grupo_e_data_decrescente(self, tmp_path):
        root = tk.Tk()
        try:
            painel = NoticiasPanel(
                root,
                catalog=NoticiasCatalog(cache_dir=tmp_path),
                debounce_ms=0,
            )
            painel._itens = {
                "1": _arq_noticia(SECAO_GERAL, "g_old", "2026-01-05"),
                "2": _arq_noticia(SECAO_CENSURAS, "c_old", "2026-02-01"),
                "3": _arq_noticia(SECAO_GERAL, "g_new", "2026-09-20 10:00:00"),
                "4": _arq_noticia(SECAO_CENSURAS, "c_new", "2026-08-01"),
                "5": _arq_noticia(SECAO_PROGRAMAS, "p", "2026-05-05"),
                "6": _arq_noticia(SECAO_CONDICOES, "co", "2026-03-03"),
                "7": _arq_noticia(SECAO_GERAL, "g_resumido", resumo="x"),
            }
            nomes = [a.nome for a in painel.pendentes_ordenados()]
            assert nomes == ["c_new", "c_old", "co", "p", "g_new", "g_old"]
        finally:
            root.destroy()

    @needs_display
    def test_data_ausente_ou_empatada_tem_ordem_estavel(self, tmp_path):
        root = tk.Tk()
        try:
            painel = NoticiasPanel(
                root,
                catalog=NoticiasCatalog(cache_dir=tmp_path),
                debounce_ms=0,
            )
            painel._itens = {
                "1": _arq_noticia(
                    SECAO_GERAL, "sem_data", "", ano=2025, mes=3, categoria="B"
                ),
                "2": _arq_noticia(SECAO_GERAL, "iso_data", "2026-09-20"),
                "3": _arq_noticia(
                    SECAO_GERAL, "iso_data_hora", "2026-09-20 10:00:00"
                ),
                "4": _arq_noticia(
                    SECAO_GERAL, "empate_a", "2026-09-20", categoria="A"
                ),
                "5": _arq_noticia(
                    SECAO_GERAL, "invalida", "not-a-date", ano=2024, mes=1
                ),
            }
            primeira = [a.nome for a in painel.pendentes_ordenados()]
            segunda = [a.nome for a in painel.pendentes_ordenados()]
            assert primeira == segunda
            assert primeira == [
                "empate_a",
                "iso_data",
                "iso_data_hora",
                "sem_data",
                "invalida",
            ]
        finally:
            root.destroy()


class _LLMQueCancela(_LLMFake):
    """LLM fake que solicita cancelamento logo após a primeira resposta."""

    def __init__(self, token):
        super().__init__()
        self._token = token

    def complete(self, messages, system_prompt=None):
        resposta = super().complete(messages, system_prompt)
        self._token.request()
        return resposta


class TestPersistenciaImediataNoticias:
    @needs_display
    def test_lote_grava_no_worker(self, tmp_path):
        noticias = [
            _noticia(
                titulo="PETROBRAS (PETR4) - Suspensão de negociação",
                url="https://x/1",
                data_publicacao="2026-09-20 10:00:00",
            ),
            _noticia(
                titulo="VALE (VALE3) - Retomada de negociação",
                url="https://x/2",
                data_publicacao="2026-09-10 10:00:00",
            ),
        ]
        catalogo = _semear(tmp_path, noticias)
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        llm = _LLMFake()
        root = tk.Tk()
        try:
            painel = NoticiasPanel(
                root,
                catalog=catalogo,
                summary_store=store,
                llm_factory=lambda: llm,
                llm_available=lambda: True,
                debounce_ms=0,
            )
            painel.update(_REFERENCIA)
            assert painel.persistir_no_lote() is True

            job = ResumosPendentesJob(
                painel, painel.pendentes_ordenados(), continuar_em_erro=True
            )
            job.iniciar().join()

            assert len(store.resumos(ESCOPO_NOTICIAS)) == 2
        finally:
            root.destroy()

    @needs_display
    def test_cancelamento_preserva_resumos_ja_gerados(self, tmp_path):
        noticias = [
            _noticia(
                titulo="A - Suspensão de negociação",
                url="https://x/1",
                data_publicacao="2026-09-20 10:00:00",
            ),
            _noticia(
                titulo="B - Retomada de negociação",
                url="https://x/2",
                data_publicacao="2026-09-10 10:00:00",
            ),
        ]
        catalogo = _semear(tmp_path, noticias)
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        token = CancellationToken()
        root = tk.Tk()
        try:
            painel = NoticiasPanel(
                root,
                catalog=catalogo,
                summary_store=store,
                llm_factory=lambda: _LLMQueCancela(token),
                llm_available=lambda: True,
                debounce_ms=0,
            )
            painel.update(_REFERENCIA)
            job = ResumosPendentesJob(
                painel,
                painel.pendentes_ordenados(),
                cancel_token=token,
                continuar_em_erro=True,
            )
            job.iniciar().join()

            assert len(store.resumos(ESCOPO_NOTICIAS)) == 1
        finally:
            root.destroy()


class _HostResumosNoticias(ResumosActionsMixin):
    def __init__(self, painel):
        self._noticias_panel = painel
        self._resumos_job = None
        self.capturado = None

    def _iniciar_lote_resumos(self, painel, pendentes, guarda, continuar=False):
        self.capturado = (painel, pendentes, guarda, continuar)


class TestResumirNoticiasPendentes:
    def test_usa_lista_ordenada_do_painel(self):
        painel = MagicMock()
        ordenados = [object(), object()]
        painel.pendentes_ordenados.return_value = ordenados
        host = _HostResumosNoticias(painel)

        host._resumir_noticias_pendentes()

        painel.pendentes_ordenados.assert_called_once()
        assert host.capturado[0] is painel
        assert host.capturado[1] == ordenados
        assert host.capturado[3] is True
