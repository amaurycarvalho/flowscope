from datetime import date, timedelta
from unittest.mock import MagicMock

from flowscope.domain.chat import DocumentSource
from flowscope.domain.structured import (
    FatoRelevante,
    NoticiaB3,
)
from flowscope.infrastructure.document_sources import (
    MaterialFactsSource,
    NoticiasSource,
)


def _fato(ticker: str = "PETR4") -> FatoRelevante:
    return FatoRelevante(
        code_cvm="9512",
        empresa="PETROLEO BRASILEIRO S.A. PETROBRAS",
        ticker=ticker,
        data_referencia="16/04/2026 14:16",
        data_entrega="28/04/2026 19:19:42",
        categoria="Fatos Relevantes",
        tipo=None,
        especie=None,
        status="Ativo",
        assunto="Tomada de Contas",
        url_documento="https://rad.cvm.gov.br/x",
        url_download="https://rad.cvm.gov.br/y",
    )


def _noticia() -> NoticiaB3:
    return NoticiaB3(
        titulo="PETROBRAS anuncia dividendos",
        data_publicacao="2026-07-28 10:00:00",
        url="https://sistemasweb.b3.com.br/1",
        agencia="18",
    )


class TestMaterialFactsSource:
    def test_implementa_document_source(self):
        fonte = MaterialFactsSource(MagicMock())
        assert isinstance(fonte, DocumentSource)
        assert fonte.categoria == "fatos_relevantes"

    def test_obter_documentos_itera_cinco_categorias(self):
        repositorio = MagicMock()
        repositorio.resolver_code_cvm.return_value = "9512"
        repositorio.listar_fatos_relevantes.return_value = [_fato()]
        fonte = MaterialFactsSource(repositorio)
        documentos = fonte.obter_documentos(ticker="PETR4")
        assert len(documentos) == 5
        assert repositorio.listar_fatos_relevantes.call_count == 5
        assert all(hasattr(documento, "to_text") for documento in documentos)

    def test_ticker_sem_code_cvm_retorna_lista_vazia(self):
        repositorio = MagicMock()
        repositorio.resolver_code_cvm.return_value = None
        fonte = MaterialFactsSource(repositorio)
        assert fonte.obter_documentos(ticker="SEM_CVM") == []
        repositorio.listar_fatos_relevantes.assert_not_called()

    def test_falha_em_uma_categoria_continua_as_demais(self, caplog):
        repositorio = MagicMock()
        repositorio.resolver_code_cvm.return_value = "9512"
        repositorio.listar_fatos_relevantes.side_effect = [
            RuntimeError("API indisponível"),
            [_fato()],
            [_fato()],
            [_fato()],
            [_fato()],
        ]
        fonte = MaterialFactsSource(repositorio)
        with caplog.at_level("WARNING", logger="flowscope.infrastructure.document_sources.material_facts_source"):
            documentos = fonte.obter_documentos(ticker="PETR4")
        assert len(documentos) == 4
        assert repositorio.listar_fatos_relevantes.call_count == 5
        assert any("Falha na categoria" in record.getMessage() for record in caplog.records)


class TestNoticiasSource:
    def test_implementa_document_source(self):
        fonte = NoticiasSource(MagicMock())
        assert isinstance(fonte, DocumentSource)
        assert fonte.categoria == "noticias"

    def test_obter_documentos_sem_requerer_ticker(self):
        repositorio = MagicMock()
        repositorio.listar_noticias.return_value = [_noticia()]
        fonte = NoticiasSource(repositorio)
        documentos = fonte.obter_documentos(ticker="PETR4")
        assert len(documentos) == 1
        assert documentos[0].titulo.startswith("PETROBRAS")
        repositorio.resolver_code_cvm.assert_not_called()

    def test_periodo_padrao_ultimos_30_dias(self):
        repositorio = MagicMock()
        repositorio.listar_noticias.return_value = []
        NoticiasSource(repositorio).obter_documentos()
        chamada = repositorio.listar_noticias.call_args
        hoje = date.today()
        assert chamada.kwargs["data_fim"] == hoje
        assert chamada.kwargs["data_inicio"] == hoje - timedelta(days=30)
