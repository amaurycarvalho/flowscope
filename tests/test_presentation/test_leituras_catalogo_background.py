"""Testes headless da leitura assíncrona de catálogos e séries.

Exercitam a preparação (worker) da leitura de documentos, notícias e evolução
dos fundamentos, além da submissão ao gerenciador de background, sem ``tk.Tk``.
"""

import threading
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

from flowscope.application.documentos.catalogo import ConsultarCatalogoUseCase
from flowscope.application.noticias.catalogo import ConsultarCatalogoNoticiasUseCase
from flowscope.domain.documents import CatalogoTicker
from flowscope.domain.noticias import CatalogoNoticias
from flowscope.domain.structured import NoticiaB3
from flowscope.infrastructure.b3.noticias_aquisicao import (
    SECAO_GERAL,
    NoticiasCache,
    chave_noticia,
    classificar_tipo,
    data_noticia,
)
from flowscope.infrastructure.b3.noticias_catalogo import NoticiasCatalog
from flowscope.infrastructure.b3.noticias_index import (
    NoticiaMeta,
    NoticiasIndexStore,
)
from flowscope.infrastructure.document_catalog import DocumentCatalog
from flowscope.presentation.gui.app_actions import ActionsMixin
from flowscope.presentation.gui.background.manager import BackgroundManager
from flowscope.presentation.gui.charts.document_tree_panel import DocumentTreePanel
from flowscope.presentation.gui.charts.noticias_panel import NoticiasPanel
from flowscope.presentation.gui.evolucao_job import preparar_series
from flowscope.presentation.gui.noticias_actions import NoticiasActionsMixin

_REFERENCIA = date(2026, 9, 25)


def _touch(caminho: Path, conteudo: bytes = b"x") -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(conteudo)


def _painel_documentos(cache_dir: Path) -> DocumentTreePanel:
    painel = DocumentTreePanel.__new__(DocumentTreePanel)
    painel._catalogo_uc = ConsultarCatalogoUseCase(
        DocumentCatalog(cache_dir=cache_dir)
    )
    return painel


def _painel_noticias(cache_dir: Path) -> NoticiasPanel:
    painel = NoticiasPanel.__new__(NoticiasPanel)
    painel._catalogo_uc = ConsultarCatalogoNoticiasUseCase(
        NoticiasCatalog(cache_dir=cache_dir)
    )
    return painel


def _drenar(background: BackgroundManager, rounds: int = 5) -> None:
    for _ in range(rounds):
        handles = list(background.jobs_ativos)
        if not handles:
            break
        for handle in handles:
            if handle.thread is not None:
                handle.thread.join(2)
        background.drenar()


class TestCarregarCatalogo:
    def test_retorna_hierarquia_ordenada(self, tmp_path):
        _touch(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        _touch(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "30.pdf")
        _touch(
            tmp_path / "documentos-relevantes" / "ALZR11" / "2025"
            / "12" / "assembleia" / "1.pdf"
        )

        painel = _painel_documentos(tmp_path)
        catalogo = painel.carregar_catalogo("ALZR11")

        assert isinstance(catalogo, CatalogoTicker)
        assert [ano.ano for ano in catalogo.anos] == [2026, 2025]
        categorias = catalogo.anos[0].meses[0].categorias
        nomes = [categoria.nome for categoria in categorias]
        assert nomes == ["Aviso aos Acionistas"]
        arquivos = [arquivo.nome for arquivo in categorias[0].arquivos]
        assert arquivos == ["30.pdf", "10.pdf"]

    def test_sem_ticker_retorna_none(self, tmp_path):
        painel = _painel_documentos(tmp_path)
        assert painel.carregar_catalogo(None) is None
        assert painel.carregar_catalogo("") is None

    def test_ticker_sem_documentos_retorna_vazio(self, tmp_path):
        painel = _painel_documentos(tmp_path)
        catalogo = painel.carregar_catalogo("SEMDOC")
        assert catalogo is not None
        assert catalogo.vazio is True


class TestCarregarSecoes:
    def _semear(self, tmp_path: Path) -> NoticiasCatalog:
        cache = NoticiasCache(tmp_path)
        indice = NoticiasIndexStore(cache_dir=tmp_path)
        noticia = NoticiaB3(
            titulo="PETROBRAS (PETR4) - Suspensão",
            data_publicacao="2026-09-20 10:00:00",
            url="https://x/1",
            agencia="18",
        )
        data = data_noticia(noticia.data_publicacao, _REFERENCIA)
        chave = chave_noticia(noticia)
        cache.gravar(
            chave, data, b"<html><body><pre>Corpo</pre></body></html>"
        )
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

    def test_retorna_secoes_com_itens(self, tmp_path):
        self._semear(tmp_path)
        painel = _painel_noticias(tmp_path)

        catalogo = painel.carregar_secoes()

        assert isinstance(catalogo, CatalogoNoticias)
        assert catalogo.vazio is False

    def test_filtra_entradas_sem_html(self, tmp_path):
        catalog = self._semear(tmp_path)
        # Remove o corpo em cache: o índice permanece, mas o item é filtrado.
        for caminho in catalog.base_dir.rglob("*.html"):
            caminho.unlink()

        painel = _painel_noticias(tmp_path)
        catalogo = painel.carregar_secoes()

        assert catalogo.vazio is True


class TestPrepararSeries:
    def test_sem_ticker_ou_store_retorna_vazio(self):
        assert preparar_series(None, "ALZR11") == ()
        assert preparar_series(MagicMock(), None) == ()

    def test_store_sem_datas_retorna_vazio(self):
        store = MagicMock()
        store.datas.return_value = []
        assert preparar_series(store, "ALZR11") == ()
        store.historico.assert_not_called()

    def test_le_historico_e_monta_series(self):
        store = MagicMock()
        store.datas.return_value = [date(2026, 1, 1), date(2026, 3, 1)]
        store.historico.return_value = ["obs"]
        with patch(
            "flowscope.presentation.gui.evolucao_job.montar_series",
            return_value=["s1", "s2"],
        ) as montar:
            series = preparar_series(store, "ALZR11")

        store.historico.assert_called_once_with(
            "ALZR11", date(2026, 1, 1), date(2026, 3, 1)
        )
        montar.assert_called_once_with(["obs"])
        assert series == ("s1", "s2")


class TestLeituraDocumentosBackground:
    def _host(self, background):
        host = ActionsMixin()
        host._documents_panel = MagicMock()
        host._background = background
        host._ticker_selecionado = "ALZR11"
        return host

    def test_submete_leitura_e_aplica_por_evento(self):
        background = BackgroundManager()
        host = self._host(background)

        host._update_documents()

        assert background.tem_ativo("documentos-leitura") is True
        host._documents_panel.mostrar_carregando.assert_called_once_with("ALZR11")
        _drenar(background)
        host._documents_panel.aplicar_catalogo.assert_called_once_with(
            "ALZR11", host._documents_panel.carregar_catalogo.return_value
        )

    def test_troca_de_ticker_descarta_leitura_obsoleta(self):
        background = BackgroundManager()
        host = self._host(background)
        liberar = threading.Event()

        def _carregar(ticker):
            if ticker == "ALZR11":
                liberar.wait(2)
            return f"cat-{ticker}"

        host._documents_panel.carregar_catalogo.side_effect = _carregar

        host._update_documents()
        host._ticker_selecionado = "PETR4"
        host._update_documents()
        liberar.set()
        _drenar(background)

        host._documents_panel.aplicar_catalogo.assert_called_once_with(
            "PETR4", "cat-PETR4"
        )

    def test_sem_ticker_aplica_estado_vazio(self):
        host = ActionsMixin()
        host._documents_panel = MagicMock()
        host._background = BackgroundManager()
        host._ticker_selecionado = None

        host._update_documents()

        host._documents_panel.aplicar_catalogo.assert_called_once_with(None, None)


class TestAquisicaoDocumentosComDedup:
    def _host(self, background, aquisicao, dedup):
        host = ActionsMixin()
        host._documents_panel = MagicMock()
        host._background = background
        host._ticker_selecionado = "ALZR11"
        host._aquisicao_documentos = aquisicao
        host._deduplicar_documentos = dedup
        host._presenter = MagicMock()
        host._flash_status = MagicMock()
        host._data_referencia = lambda: _REFERENCIA
        return host

    def test_dedup_roda_apos_aquisicao(self):
        background = BackgroundManager()
        aquisicao = MagicMock()
        dedup = MagicMock()
        host = self._host(background, aquisicao, dedup)

        host._adquirir_documentos("ALZR11")
        _drenar(background)

        aquisicao.adquirir.assert_called_once()
        dedup.assert_called_once()
        assert dedup.call_args.args[0] == "ALZR11"

    def test_sem_dedup_ainda_adquire(self):
        background = BackgroundManager()
        aquisicao = MagicMock()
        host = self._host(background, aquisicao, None)

        host._adquirir_documentos("ALZR11")
        _drenar(background)

        aquisicao.adquirir.assert_called_once()


class TestLeituraNoticiasBackground:
    def _host(self, background):
        host = NoticiasActionsMixin()
        host._noticias_panel = MagicMock()
        host._background = background
        host._data_referencia = lambda: _REFERENCIA
        return host

    def test_submete_leitura_e_aplica_por_evento(self):
        background = BackgroundManager()
        host = self._host(background)

        host._update_noticias()

        assert background.tem_ativo("noticias-leitura") is True
        host._noticias_panel.mostrar_carregando.assert_called_once()
        _drenar(background)
        host._noticias_panel.aplicar_secoes.assert_called_once_with(
            host._noticias_panel.carregar_secoes.return_value
        )
        host._noticias_panel.definir_referencia.assert_called_once_with(
            _REFERENCIA
        )

    def test_nova_leitura_prevalece_sobre_anterior(self):
        background = BackgroundManager()
        host = self._host(background)
        liberar = threading.Event()
        iniciou = threading.Event()
        contagem = {"n": 0}

        def _carregar():
            contagem["n"] += 1
            if contagem["n"] == 1:
                iniciou.set()
                liberar.wait(2)
                return "antigo"
            return "novo"

        host._noticias_panel.carregar_secoes.side_effect = _carregar

        host._update_noticias()
        assert iniciou.wait(2)
        host._update_noticias()
        liberar.set()
        _drenar(background)

        host._noticias_panel.aplicar_secoes.assert_called_once_with("novo")


class TestLeituraEvolucaoBackground:
    def _host(self, background):
        host = ActionsMixin()
        host._fundamental_evolution_panel = MagicMock()
        host._fundamental_history_store = MagicMock()
        host._background = background
        host._ticker_selecionado = "ALZR11"
        return host

    def test_submete_leitura_e_aplica_por_evento(self):
        background = BackgroundManager()
        host = self._host(background)
        host._fundamental_history_store.datas.return_value = []

        host._update_fundamental_evolution()

        assert background.tem_ativo("evolucao") is True
        host._fundamental_evolution_panel.mostrar_carregando.assert_called_once_with(
            "ALZR11"
        )
        _drenar(background)
        host._fundamental_evolution_panel.update.assert_called_once_with(
            (), ticker="ALZR11"
        )

    def test_resultado_de_ticker_anterior_nao_e_aplicado(self):
        background = BackgroundManager()
        host = self._host(background)
        liberar = threading.Event()
        host._fundamental_history_store.datas.side_effect = lambda ticker: (
            liberar.wait(2) if ticker == "ALZR11" else None,
            [],
        )[1]

        host._update_fundamental_evolution()
        host._ticker_selecionado = "PETR4"
        host._update_fundamental_evolution()
        liberar.set()
        _drenar(background)

        assert host._fundamental_evolution_panel.update.call_count == 1
        assert host._fundamental_evolution_panel.update.call_args.kwargs[
            "ticker"
        ] == "PETR4"
