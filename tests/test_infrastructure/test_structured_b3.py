import base64
import json
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
import responses

from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.b3.structured_extractor import extrair_documento_provento
from flowscope.infrastructure.b3.structured_parser import (
    converter_data_br_para_iso,
    extrair_isento_ir,
    extrair_por_rotulo,
    extrair_tabelas,
    identificar_tipo_provento,
    limpar_valor_monetario,
)
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.b3.structured_repository import FundosRepository
from tests.fixtures.structured_documents import (
    AMORTIZACAO_HTML,
    FLAT_HTML,
    SEM_DADOS_HTML,
    TABLE_HTML,
)

_BASE = B3FundosClient._BASE_URL


def _token(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"))
    return base64.b64encode(raw.encode()).decode()


class TestBuildToken:
    def test_token_get_list_class_fund(self):
        client = B3FundosClient(cache=CacheManager(cache_dir="/tmp/irrelevante"))
        token = client._build_token(
            {"language": "pt-br", "idCEM": "ALZR", "typeFund": "FII"}
        )
        assert (
            token
            == "eyJsYW5ndWFnZSI6InB0LWJyIiwiaWRDRU0iOiJBTFpSIiwidHlwZUZ1bmQiOiJGSUkifQ=="
        )

    def test_token_compacto_sem_espacos(self):
        client = B3FundosClient(cache=CacheManager(cache_dir="/tmp/irrelevante"))
        token = client._build_token(
            {"language": "pt-br", "idCEM": "ALZR", "typeFund": "FII"}
        )
        decodificado = base64.b64decode(token).decode()
        assert " " not in decodificado


class TestExtrairPorRotulo:
    def test_valor_no_proximo_sibling(self):
        from flowscope.infrastructure.b3.structured_parser import parse_html

        html = "<strong>Nome:</strong><span>ALIANZA TRUST</span>"
        soup = parse_html(html)
        assert extrair_por_rotulo(soup, "Nome:") == "ALIANZA TRUST"

    def test_rotulo_nao_encontrado(self):
        from flowscope.infrastructure.b3.structured_parser import parse_html

        soup = parse_html("<p>Outro conteúdo</p>")
        assert extrair_por_rotulo(soup, "Nome:") is None

    def test_valor_no_mesmo_elemento_apos_dois_pontos(self):
        from flowscope.infrastructure.b3.structured_parser import parse_html

        soup = parse_html("<td>Telefone Contato: (11) 3383-3102</td>")
        assert extrair_por_rotulo(soup, "Telefone Contato:") == "(11) 3383-3102"


class TestExtrairTabelas:
    def test_tabela_com_thead(self):
        from flowscope.infrastructure.b3.structured_parser import parse_html

        html = """
        <table><thead><tr><th>Código ISIN</th><th>Valor</th></tr></thead>
        <tbody><tr><td>BRALZRCTF006</td><td>R$ 0,08355</td></tr></tbody></table>
        """
        soup = parse_html(html)
        tabelas = extrair_tabelas(soup)
        assert tabelas[0]["dados"] == [
            {"Código ISIN": "BRALZRCTF006", "Valor": "R$ 0,08355"}
        ]

    def test_tabela_sem_thead_primeira_linha_como_cabecalho(self):
        from flowscope.infrastructure.b3.structured_parser import parse_html

        html = """
        <table><tbody>
        <tr><td>Código</td><td>Valor</td></tr>
        <tr><td>BRALZRCTF006</td><td>R$ 0,08355</td></tr>
        </tbody></table>
        """
        soup = parse_html(html)
        tabelas = extrair_tabelas(soup)
        assert tabelas[0]["dados"] == [
            {"Código": "BRALZRCTF006", "Valor": "R$ 0,08355"}
        ]

    def test_contexto_da_tabela_vem_do_heading(self):
        from flowscope.infrastructure.b3.structured_parser import parse_html

        html = "<h3>Detalhes do Provento</h3><table><tr><td>a</td><td>b</td></tr></table>"
        soup = parse_html(html)
        tabelas = extrair_tabelas(soup)
        assert tabelas[0]["contexto"] == "Detalhes do Provento"


class TestLimpeza:
    def test_limpar_valor_monetario(self):
        assert limpar_valor_monetario("R$ 1.234,56") == Decimal("1234.56")
        assert limpar_valor_monetario("R$ 0,08355") == Decimal("0.08355")
        assert limpar_valor_monetario("") is None

    def test_converter_data_br_para_iso(self):
        assert converter_data_br_para_iso("18/06/2026") == "2026-06-18"


class TestTipoProvento:
    def test_linha_marcada_rendimento(self):
        linha = {"Rendimento": "X", "Amortização": ""}
        assert identificar_tipo_provento(linha) == "Rendimento"

    def test_linha_marcada_amortizacao(self):
        linha = {"Rendimento": "", "Amortização": "X"}
        assert identificar_tipo_provento(linha) == "Amortização"


class TestExtracaoDocumento:
    def test_extrai_documento_flat(self):
        doc = extrair_documento_provento(
            FLAT_HTML,
            "1224160",
            "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=1224160",
            "2026-07-29T14:30:00-03:00",
            "ALZR11",
            "20294",
        )
        assert doc is not None
        assert doc.entidade.nome.startswith("ALIANZA")
        assert doc.entidade.cnpj.value == "28.737.771/0001-85"
        assert doc.provento.codigo_isin.value == "BRALZRCTF006"
        assert doc.provento.codigo_negociacao == "ALZR11"
        assert doc.provento.tipo == "Rendimento"
        assert doc.provento.valor_por_unidade.value == Decimal("0.08355")
        assert doc.provento.isento_ir is True
        assert doc.provento.ano_referencia == 2026

    def test_extrai_documento_tabela_colunar(self):
        doc = extrair_documento_provento(
            TABLE_HTML, "1224160", "https://x?id=1224160", "t", "ALZR11", "20294"
        )
        assert doc is not None
        assert doc.provento.codigo_isin.value == "BRALZRCTF006"
        assert doc.provento.codigo_negociacao == "ALZR11"
        assert doc.provento.tipo == "Rendimento"
        assert doc.provento.valor_por_unidade.value == Decimal("0.08355")
        assert doc.provento.isento_ir is False

    def test_extrai_amortizacao(self):
        doc = extrair_documento_provento(
            AMORTIZACAO_HTML, "7", "https://x?id=7", "t", "ALZR11", "20294"
        )
        assert doc is not None
        assert doc.provento.tipo == "Amortização"

    def test_documento_sem_dados_retorna_none(self):
        doc = extrair_documento_provento(
            SEM_DADOS_HTML, "9", "https://x?id=9", "t", "PETR4", "1"
        )
        assert doc is None

    def test_to_text_contem_campos_extraidos(self):
        doc = extrair_documento_provento(
            FLAT_HTML, "1224160", "https://x?id=1224160", "t", "ALZR11", "20294"
        )
        texto = doc.to_text()
        assert "ALIANZA" in texto
        assert "Rendimento" in texto
        assert "BRALZRCTF006" in texto


class TestIsentoIR:
    def test_isento_sim(self):
        from flowscope.infrastructure.b3.structured_parser import parse_html

        soup = parse_html("<p><strong>Rendimento isento de IR*:</strong> Sim</p>")
        assert extrair_isento_ir(soup) is True

    def test_isento_nao(self):
        from flowscope.infrastructure.b3.structured_parser import parse_html

        soup = parse_html("<p><strong>Rendimento isento de IR*:</strong> Não</p>")
        assert extrair_isento_ir(soup) is False


class TestB3FundosClient:
    @responses.activate
    def test_resolver_ticker_sucesso(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        fundos = {
            "language": "pt-br",
            "typeFund": "FII",
            "pageNumber": 1,
            "pageSize": 20,
        }
        responses.get(
            f"{_BASE}/GetListFunds/{_token(fundos)}",
            json={
                "page": {"totalPages": 1},
                "results": [{"acronym": "ALZR", "id": 870}],
            },
            status=200,
        )
        classes = {
            "language": "pt-br",
            "idFNET": "870",
            "idCEM": "ALZR",
            "typeFund": "FII",
        }
        responses.get(
            f"{_BASE}/GetListClassFund/{_token(classes)}",
            json=[
                {
                    "id": "870",
                    "idMain": None,
                    "tradingName": "Fundo: 28.737.771/0001-85",
                },
                {
                    "id": "20294",
                    "idMain": "870",
                    "tradingName": "28.737.771/0001-85",
                },
            ],
            status=200,
        )
        assert client.resolver_ticker("ALZR11") == "20294"

    @responses.activate
    def test_resolver_ticker_sem_dados_retorna_none(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        fundos = {
            "language": "pt-br",
            "typeFund": "FII",
            "pageNumber": 1,
            "pageSize": 20,
        }
        responses.get(
            f"{_BASE}/GetListFunds/{_token(fundos)}",
            json={"page": {"totalPages": 1}, "results": []},
            status=200,
        )
        assert client.resolver_ticker("PETR4") is None

    @responses.activate
    def test_resolver_ticker_nao_cacheia_ausencia(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        fundos = {
            "language": "pt-br",
            "typeFund": "FII",
            "pageNumber": 1,
            "pageSize": 20,
        }
        url = f"{_BASE}/GetListFunds/{_token(fundos)}"
        responses.get(
            url, json={"page": {"totalPages": 1}, "results": []}, status=200
        )
        assert client.resolver_ticker("PETR4") is None
        assert client.resolver_ticker("PETR4") is None
        assert len(responses.calls) == 2

    @responses.activate
    def test_listar_documentos_pagina_unica(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        payload = {
            "language": "pt-br",
            "dataInicial": "2026-01-01",
            "dataFinal": "2026-07-29",
            "pageNumber": 1,
            "pageSize": 20,
            "idFNET": "20294",
            "typeFund": "FII",
            "type": 41,
        }
        responses.get(
            f"{_BASE}/GetStructuredReports/{_token(payload)}",
            json={
                "page": {"totalPages": 1, "totalRecords": 1},
                "results": [{"urlViewerFundosNet": "https://fnet?id=1224160"}],
            },
            status=200,
        )
        docs = client.listar_documentos(
            "20294", date(2026, 1, 1), date(2026, 7, 29), 41
        )
        assert len(docs) == 1
        assert len(responses.calls) == 1

    @responses.activate
    def test_listar_documentos_multiplas_paginas(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        for page in (1, 2, 3):
            payload = {
                "language": "pt-br",
                "dataInicial": "2026-01-01",
                "dataFinal": "2026-07-29",
                "pageNumber": page,
                "pageSize": 20,
                "idFNET": "20294",
                "typeFund": "FII",
                "type": 41,
            }
            responses.get(
                f"{_BASE}/GetStructuredReports/{_token(payload)}",
                json={
                    "page": {"totalPages": 3, "totalRecords": 3},
                    "results": [{"id": page}],
                },
                status=200,
            )
        docs = client.listar_documentos(
            "20294", date(2026, 1, 1), date(2026, 7, 29), 41
        )
        assert len(docs) == 3
        assert len(responses.calls) == 3

    @responses.activate
    def test_buscar_html_documento(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(
            "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=1224160",
            body="<html><body>documento</body></html>",
            status=200,
        )
        html = client.buscar_html_documento("1224160")
        assert "documento" in html


class TestFundosRepository:
    def test_resolver_delega_ao_client(self):
        client = MagicMock()
        client.resolver_ticker.return_value = "20294"
        repo = FundosRepository(client=client)
        assert repo.resolver_ticker("ALZR11") == "20294"

    def test_listar_delega_ao_client(self):
        client = MagicMock()
        client.listar_documentos.return_value = [{"urlViewerFundosNet": "https://x?id=1"}]
        repo = FundosRepository(client=client)
        docs = repo.listar_documentos("20294", date(2026, 1, 1), date(2026, 7, 29), 41)
        assert docs == [{"urlViewerFundosNet": "https://x?id=1"}]

    def test_extrair_detalhes_usando_client_e_parser(self):
        client = MagicMock()
        client.buscar_html_documento.return_value = FLAT_HTML
        repo = FundosRepository(client=client)
        doc = repo.extrair_detalhes(
            {
                "urlViewerFundosNet": "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=1224160",
                "ticker": "ALZR11",
                "id_fnet": "20294",
            }
        )
        client.buscar_html_documento.assert_called_once_with("1224160")
        assert doc.id_documento == "1224160"
        assert doc.ticker == "ALZR11"
        assert doc.id_fnet == "20294"
        assert doc.provento.codigo_isin.value == "BRALZRCTF006"

    def test_extrair_detalhes_sem_provento_levanta(self):
        client = MagicMock()
        client.buscar_html_documento.return_value = SEM_DADOS_HTML
        repo = FundosRepository(client=client)
        with pytest.raises(ValueError):
            repo.extrair_detalhes(
                {"urlViewerFundosNet": "https://fnet?id=9", "ticker": "PETR4"}
            )
