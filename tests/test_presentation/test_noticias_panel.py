"""Testes do painel de notícias, do job de aquisição e dos resumos em lote."""

import logging
import os
import queue
import threading
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
from flowscope.application.document_preview import ExtracaoTexto, StatusExtracao
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.llm import LLMCommunicationError, LLMResposta
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
from flowscope.application.documentos.document_summary import DocumentSummaryService
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Erro, Progresso, Resultado
from flowscope.presentation.gui.background.job import JobHandle, Politica
from flowscope.presentation.gui.background.manager import BackgroundManager
from flowscope.presentation.gui.charts.noticias_panel import NoticiasPanel
from flowscope.presentation.gui.noticias_actions import NoticiasActionsMixin
from flowscope.presentation.gui.noticias_job import executar_noticias
from flowscope.presentation.gui.resumos_job import executar_resumos
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)

_REFERENCIA = date(2026, 9, 25)


class _LLMFake:
    """Porta de LLM que registra chamadas e devolve resumos configurados."""

    def __init__(self, resposta="CURTO: resumo curto\nLONGO: resumo longo"):
        self.resposta = resposta
        self.chamadas: list[list[dict]] = []

    def complete(self, messages, system_prompt=None):
        self.chamadas.append(messages)
        return LLMResposta(texto=self.resposta)


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


def _executar_lote(painel, arquivos, continuar=True, token=None):
    """Executa o trabalho puro do lote e retorna (sem_texto, eventos)."""
    handle = JobHandle(id=1, grupo="resumos", politica=Politica.LATEST_WINS)
    if token is not None:
        handle.token = token
    eventos = []
    ctx = JobContext(handle, eventos.append)
    sem_texto = executar_resumos(ctx, painel, arquivos, continuar)
    return sem_texto, eventos


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
        assert painel._texto_do_arquivo(arquivo).texto == "Corpo do artigo"

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
        painel = NoticiasPanel.__new__(NoticiasPanel)
        painel._baixar_vinculo = lambda _texto, _senha=None: ExtracaoTexto(
            "texto do documento", StatusExtracao.OK
        )
        resultado = painel._texto_do_arquivo(arquivo)
        assert resultado.texto == "texto do documento"
        assert "Titulo" not in resultado.texto

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
        painel = NoticiasPanel.__new__(NoticiasPanel)
        painel._baixar_vinculo = lambda _texto, _senha=None: None
        assert painel._texto_do_arquivo(arquivo).texto == "Corpo"

    def test_regulatoria_nao_baixa_vinculo(self, tmp_path, monkeypatch):
        chamadas: list = []
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
        painel._baixar_vinculo = (
            lambda texto, _senha=None: chamadas.append(texto)
            or ExtracaoTexto("x", StatusExtracao.OK)
        )
        assert painel._texto_do_arquivo(arquivo).texto == "Corpo"
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
        painel._baixar_vinculo = lambda _texto, _senha=None: None
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

        def _baixar(texto, _senha=None):
            chamadas.append(texto)
            if len(chamadas) == 1:
                return None
            return ExtracaoTexto("CONTEUDO DO DOCUMENTO", StatusExtracao.OK)

        painel._baixar_vinculo = _baixar
        primeiro = painel.preparar_texto(arquivo)
        assert "frmExibirArquivoIPEExterno" in primeiro.texto
        segundo = painel.preparar_texto(arquivo)
        assert segundo.texto == "CONTEUDO DO DOCUMENTO"
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
        painel._baixar_vinculo = lambda _texto, _senha=None: None
        sem_texto, eventos = _executar_lote(painel, [arquivo])
        assert sem_texto == 1
        assert llm.chamadas == []
        assert not any(isinstance(e, Resultado) for e in eventos)
        chave = chave_documento(arquivo.caminho, tmp_path)
        assert store.obter(ESCOPO_NOTICIAS, chave) is None

    def test_lote_resume_quando_documento_resolve(self, tmp_path, monkeypatch):
        arquivo = self._arquivo_geral(tmp_path)
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        llm = _LLMFake()
        painel = self._painel_com_llm(tmp_path, store, llm)
        painel._baixar_vinculo = lambda _texto, _senha=None: ExtracaoTexto(
            "CONTEUDO DO DOCUMENTO", StatusExtracao.OK
        )
        sem_texto, eventos = _executar_lote(painel, [arquivo])
        assert sem_texto == 0
        assert llm.chamadas
        assert "CONTEUDO DO DOCUMENTO" in llm.chamadas[0][0]["content"]
        assert any(isinstance(e, Resultado) for e in eventos)


class TestReClickNoticias:
    def test_clique_no_mesmo_artigo_reprocessa(self):
        painel = NoticiasPanel.__new__(NoticiasPanel)
        painel._tree = MagicMock()
        painel._tree.identify_row.return_value = "n1"
        arquivo = _arquivo_lote("noticia", Path("/tmp/noticia.html"))
        painel._itens = {"n1": arquivo}
        painel._agendar_preview = MagicMock()
        painel._arquivo_selecionado = lambda: arquivo
        evento = MagicMock()
        evento.y = 3

        painel._on_click(evento)

        painel._agendar_preview.assert_called_once_with(arquivo)

    def test_clique_em_outro_no_nao_reprocessa(self):
        painel = NoticiasPanel.__new__(NoticiasPanel)
        painel._tree = MagicMock()
        painel._tree.identify_row.return_value = "n2"
        painel._itens = {"n2": _arquivo_lote("outra", Path("/tmp/outra.html"))}
        painel._agendar_preview = MagicMock()
        painel._arquivo_selecionado = lambda: _arquivo_lote(
            "noticia", Path("/tmp/noticia.html")
        )
        evento = MagicMock()
        evento.y = 3

        painel._on_click(evento)

        painel._agendar_preview.assert_not_called()


class TestSolicitarSenhaDialogo:
    def test_usa_dialogo_com_entrada_oculta(self, monkeypatch):
        painel = NoticiasPanel.__new__(NoticiasPanel)
        painel.frame = MagicMock()
        capturado: dict = {}

        def _askstring(titulo, prompt, show=None, parent=None):
            capturado["show"] = show
            return "abc"

        monkeypatch.setattr(
            "flowscope.presentation.gui.charts.noticias_panel.simpledialog.askstring",
            _askstring,
        )

        arquivo = _arquivo_lote("noticia", Path("/tmp/noticia.html"))
        assert painel._solicitar_senha(arquivo) == "abc"
        assert capturado["show"] == "*"


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
        llm = _LLMFake()
        root = tk.Tk()
        try:
            painel = NoticiasPanel(
                root,
                catalog=catalogo,
                baixar_vinculo=lambda _texto, _senha=None: ExtracaoTexto(
                    "CONTEUDO DO ARQUIVO VINCULADO", StatusExtracao.OK
                ),
                llm_factory=lambda: llm,
                llm_available=lambda: True,
                debounce_ms=0,
            )
            painel.update(_REFERENCIA)
            _executar_lote(painel, list(painel._itens.values()))
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
            def preparar_texto(self, arquivo, senha=None):
                return ExtracaoTexto("texto", StatusExtracao.OK)

            def persistir_no_lote(self):
                return False

            def gerar_resumo_estrito(self, arquivo, texto):
                if arquivo.nome == "B":
                    raise LLMCommunicationError("falha")
                return ResumoDocumento("curto", "longo")

            def avaliar_guidance(self, arquivo, texto):
                return None

        sem_texto, eventos = _executar_lote(_PainelLote(), arquivos)
        resultados = [e for e in eventos if isinstance(e, Resultado)]
        erros = [e for e in eventos if isinstance(e, Erro)]
        assert len(resultados) == 2
        assert len(erros) == 1


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


class TestExecutarNoticias:
    def test_publica_progresso(self):
        class _Aquisicao:
            def adquirir(self, reference_date, progress=None, cancel_token=None):
                progress(1, 2, "• Notícias (1/2)")

        handle = JobHandle(id=1, grupo="noticias", politica=Politica.LATEST_WINS)
        eventos = []
        ctx = JobContext(handle, eventos.append)
        executar_noticias(ctx, _Aquisicao(), _REFERENCIA)
        assert eventos == [Progresso("• Notícias (1/2)", 1, 2)]

    def test_cancelamento_nao_loga_falha(self, caplog):
        class _AquisicaoCancelada:
            def adquirir(self, reference_date, progress=None, cancel_token=None):
                raise OperacaoCancelada()

        handle = JobHandle(id=1, grupo="noticias", politica=Politica.LATEST_WINS)
        handle.token.request()
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            executar_noticias(
                JobContext(handle, lambda evento: None),
                _AquisicaoCancelada(),
                _REFERENCIA,
            )
        assert "Falha na aquisição" not in caplog.text


class _HostNoticias(ActionsMixin, NoticiasActionsMixin):
    def __init__(self, painel):
        self._noticias_panel = painel
        self._aquisicao_noticias = MagicMock()
        self._presenter = MagicMock()
        self._background = BackgroundManager()
        self._data = _REFERENCIA
        self.status: list[tuple] = []
        self.pendentes: list = []

    def _data_referencia(self):
        return self._data

    def after(self, ms, callback):
        self.pendentes.append((ms, callback))
        return "id"

    def _rodar_pendentes(self):
        pendentes, self.pendentes = self.pendentes, []
        for _, callback in pendentes:
            callback()

    def _set_status(self, msg, icon=""):
        self.status.append((msg, icon))

    def _flash_status(self, msg, icon="✓", clear_ms=2500):
        self.status.append((msg, icon))


def _drenar(host, rounds: int = 10) -> None:
    """Aguarda as threads, drena eventos e roda os callbacks ``after(0)``."""
    for _ in range(rounds):
        for handle in list(host._background.jobs_ativos):
            if handle.thread is not None:
                handle.thread.join(2)
        host._background.drenar()
        host._rodar_pendentes()
        if not host._background.jobs_ativos and not host.pendentes:
            break


class TestNoticiasActions:
    def test_atualiza_painel_com_data_de_referencia(self):
        painel = MagicMock()
        host = _HostNoticias(painel)
        host._update_noticias()
        _drenar(host)
        painel.definir_referencia.assert_called_once_with(_REFERENCIA)
        painel.mostrar_carregando.assert_called_once()
        painel.aplicar_secoes.assert_called_once()

    def test_update_noticias_nao_bloqueia_com_leitura_lenta(self):
        painel = MagicMock()
        liberar = threading.Event()
        painel.carregar_secoes.side_effect = lambda: (
            liberar.wait(2), "catalogo"
        )[1]
        host = _HostNoticias(painel)
        host._update_noticias()
        assert host._background.tem_ativo(noticias_actions.GRUPO_LEITURA) is True
        liberar.set()
        _drenar(host)
        painel.aplicar_secoes.assert_called_once_with("catalogo")

    def test_adquirir_executa_e_remonta(self):
        painel = MagicMock()
        host = _HostNoticias(painel)
        host._adquirir_noticias()
        _drenar(host)
        assert host._aquisicao_noticias.adquirir.call_args.args == (_REFERENCIA,)
        painel.mostrar_carregando.assert_called()
        painel.aplicar_secoes.assert_called_once()

    def test_sem_aquisicao_apenas_le_cache(self):
        painel = MagicMock()
        host = _HostNoticias(painel)
        host._aquisicao_noticias = None
        host._adquirir_noticias()
        _drenar(host)
        painel.aplicar_secoes.assert_called_once()

    def test_cancelamento_agenda_remontagem_sem_polling(self):
        painel = MagicMock()
        host = _HostNoticias(painel)

        host._finalizar_noticias(cancelado=True)

        assert len(host.pendentes) == 1
        assert host.pendentes[0][0] == 0
        _drenar(host)

        assert painel.carregar_secoes.call_count == 1
        painel.aplicar_secoes.assert_called_once()

    def test_remontagem_nao_sobrescreve_carga_nova(self):
        painel = MagicMock()
        host = _HostNoticias(painel)
        liberar = threading.Event()

        host._background.submit(
            lambda ctx: liberar.wait(2),
            grupo=noticias_actions.GRUPO,
            politica=noticias_actions.POLITICA,
        )
        assert host._background.tem_ativo(noticias_actions.GRUPO) is True

        host._finalizar_noticias(cancelado=True)
        host._rodar_pendentes()

        assert painel.carregar_secoes.call_count == 0

        liberar.set()
        _drenar(host)



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
