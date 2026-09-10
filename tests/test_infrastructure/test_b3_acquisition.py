import json
import threading
import time
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
import requests

from flowscope.domain.b3 import (
    AcquisitionResult,
    B3Fund,
    B3ReportReference,
)
from flowscope.infrastructure.b3.encoder import encode_b3_payload
from flowscope.infrastructure.b3.fund_repository import B3FundRepository
from flowscope.infrastructure.b3.funds_client import _selecionar_fund
from flowscope.infrastructure.b3.rate_limit import SerializadorPorHost
from flowscope.infrastructure.b3.reports_repository import (
    B3ReportsRepository,
    _payload,
)
from flowscope.infrastructure.b3.retry import executar_com_retry

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "b3"
REFERENCIA = date(2026, 9, 4)


def _fixture(nome: str) -> object:
    return json.loads((_FIXTURES / nome).read_text(encoding="utf-8"))


class TestContratoFixtures:
    def test_fixture_fundo_alzr(self):
        candidatos = _fixture("fund_alzr.json")
        assert isinstance(candidatos, list)
        assert _selecionar_fund(candidatos)["id"] == "20294"

    def test_fixture_distribuicoes_alzr(self):
        dados = _fixture("distributions_alzr.json")
        assert dados["page"]["totalPages"] == 1
        assert len(dados["results"]) == 2

    def test_chaves_de_data_confirmadas(self):
        payload = _payload("20294", date(2026, 1, 1), date(2026, 7, 29))
        assert payload["dataInicial"] == "2026-01-01"
        assert payload["dataFinal"] == "2026-07-29"
        assert "dateInitial" not in payload


class TestSelecionarFund:
    def test_prefere_registro_com_idmain(self):
        candidatos = [
            {"id": "1", "idMain": None, "tradingName": "A"},
            {"id": "2", "idMain": "1", "tradingName": "B"},
        ]
        assert _selecionar_fund(candidatos)["id"] == "2"

    def test_sem_idmain_ignora_registro_fundo(self):
        candidatos = [
            {"id": "870", "tradingName": "Fundo: 28.737.771/0001-85"},
            {"id": "20294", "tradingName": "28.737.771/0001-85"},
        ]
        assert _selecionar_fund(candidatos)["id"] == "20294"

    def test_lista_vazia_retorna_none(self):
        assert _selecionar_fund([]) is None


class TestEncoder:
    def test_token_alzr(self):
        token = encode_b3_payload(
            {"language": "pt-br", "idCEM": "ALZR", "typeFund": "FII"}
        )
        assert (
            token
            == "eyJsYW5ndWFnZSI6InB0LWJyIiwiaWRDRU0iOiJBTFpSIiwidHlwZUZ1bmQiOiJGSUkifQ=="
        )


class TestRetry:
    def test_repete_erro_transitorio(self):
        tentativas = {"n": 0}

        def fn():
            tentativas["n"] += 1
            if tentativas["n"] < 3:
                raise requests.ConnectionError("transitório")
            return "ok"

        assert executar_com_retry(fn, delays=(0, 0, 0), sleep=lambda _: None) == "ok"
        assert tentativas["n"] == 3

    def test_nao_repete_404(self):
        tentativas = {"n": 0}

        def fn():
            tentativas["n"] += 1
            erro = requests.HTTPError("404")
            erro.response = _Resposta(404)
            raise erro

        with pytest.raises(requests.HTTPError):
            executar_com_retry(fn, delays=(0, 0, 0), sleep=lambda _: None)
        assert tentativas["n"] == 1


class _Resposta:
    def __init__(self, status: int) -> None:
        self.status_code = status


class TestSerializadorPorHost:
    def test_serializa_por_host(self):
        serializador = SerializadorPorHost()
        ativos = {"n": 0}
        maximo = {"n": 0}

        def tarefa():
            with serializador.serializar("https://host.exemplo/a"):
                ativos["n"] += 1
                maximo["n"] = max(maximo["n"], ativos["n"])
                time.sleep(0.02)
                ativos["n"] -= 1

        threads = [threading.Thread(target=tarefa) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert maximo["n"] == 1


class TestModelos:
    def test_lista_vazia_e_disponivel(self):
        resultado = AcquisitionResult(fund=None, distributions=())
        assert resultado.disponivel() is True

    def test_erro_nao_e_disponivel(self):
        resultado = AcquisitionResult(errors=("distributions unavailable",))
        assert resultado.disponivel() is False


class _ClienteFake:
    def __init__(self, candidato=None, documentos=None, erro=None):
        self._candidato = candidato
        self._documentos = documentos or []
        self._erro = erro

    def selecionar_candidato(self, ticker):
        return self._candidato

    def listar_documentos(self, *args, **kwargs):
        if self._erro is not None:
            raise self._erro
        return self._documentos


class TestFundRepository:
    def test_find_by_ticker(self):
        candidatos = _fixture("fund_alzr.json")
        repo = B3FundRepository(client=_ClienteFake(candidato=candidatos[1]))
        fundo = repo.find_by_ticker("ALZR11")
        assert isinstance(fundo, B3Fund)
        assert fundo.fnet_id == "20294"
        assert fundo.primary_id == "870"
        assert fundo.ticker == "ALZR11"

    def test_find_by_ticker_sem_dados(self):
        repo = B3FundRepository(client=_ClienteFake(candidato=None))
        assert repo.find_by_ticker("XPTO11") is None


class TestReportsRepository:
    def test_get_distributions_converte_referencias(self):
        documentos = _fixture("distributions_alzr.json")["results"]
        repo = B3ReportsRepository(client=_ClienteFake(documentos=documentos))
        referencias = repo.get_distributions("20294", date(2026, 1, 1), REFERENCIA)
        assert len(referencias) == 2
        assert isinstance(referencias[0], B3ReportReference)
        assert referencias[0].document_id == 1252542
        assert referencias[0].reference_date == date(2026, 7, 17)
        assert referencias[0].report_type == "Rendimentos e Amortizações"

    def test_acquire_distributions_preserva_bruto_e_metadados(self):
        documentos = _fixture("distributions_alzr.json")["results"]
        repo = B3ReportsRepository(client=_ClienteFake(documentos=documentos))
        resultado = repo.acquire_distributions("20294", date(2026, 1, 1), REFERENCIA)
        assert resultado.disponivel() is True
        assert len(resultado.distributions) == 2
        assert len(resultado.raw_documents) == 2
        assert resultado.metadata[0].endpoint == "GetStructuredReports(type=41)"
        assert resultado.metadata[0].request_payload["idFNET"] == "20294"

    def test_acquire_distributions_registra_erro(self):
        repo = B3ReportsRepository(
            client=_ClienteFake(erro=requests.ConnectionError("fora do ar"))
        )
        resultado = repo.acquire_distributions("20294", date(2026, 1, 1), REFERENCIA)
        assert resultado.disponivel() is False
        assert resultado.errors
        assert resultado.distributions == ()


class TestExtrairProventos:
    def test_extrai_provento_do_documento(self):
        from tests.fixtures.structured_documents import FLAT_HTML

        class _ClienteComHtml:
            def listar_documentos(self, *args, **kwargs):
                return [
                    {
                        "urlViewerFundosNet": "https://fnet?id=1224160",
                        "ticker": "ALZR11",
                        "id_fnet": "20294",
                    }
                ]

            def buscar_html_documento(self, id_documento):
                return FLAT_HTML

        repo = B3ReportsRepository(client=_ClienteComHtml())
        proventos = repo.extrair_proventos(
            "20294", date(2026, 1, 1), REFERENCIA, "ALZR11"
        )
        assert len(proventos) == 1
        assert proventos[0].provento.codigo_isin.value == "BRALZRCTF006"

    def test_documento_sem_provento_e_ignorado(self):
        from tests.fixtures.structured_documents import SEM_DADOS_HTML

        class _ClienteSemProvento:
            def listar_documentos(self, *args, **kwargs):
                return [{"urlViewerFundosNet": "https://fnet?id=9"}]

            def buscar_html_documento(self, id_documento):
                return SEM_DADOS_HTML

        repo = B3ReportsRepository(client=_ClienteSemProvento())
        assert repo.extrair_proventos("1", date(2026, 1, 1), REFERENCIA, "PETR4") == []


class _FundoFake:
    def __init__(self, fnet_id="20294"):
        self.fnet_id = fnet_id
        self.name = "Alianza Trust"


class TestB3FundamentalRepository:
    def _repo(self, documentos=None):
        from flowscope.infrastructure.fii.b3_fundamental_repository import (
            B3FundamentalRepository,
        )

        class _Fundos:
            def find_by_ticker(self, ticker):
                return _FundoFake()

        class _Relatorios:
            def extrair_proventos(self, *args, **kwargs):
                return documentos or []

        return B3FundamentalRepository(
            fund_repository=_Fundos(), reports_repository=_Relatorios()
        )

    def test_obter_nome(self):
        repo = self._repo()
        assert repo.obter_nome("ALZR11") == "Alianza Trust"

    def test_obter_proventos(self):
        from flowscope.domain.structured import ISIN, Provento, ValorProvento

        provento = Provento(
            codigo_isin=ISIN("BRALZRCTF006"),
            codigo_negociacao="ALZR11",
            tipo="Rendimento",
            data_base=date(2026, 7, 10),
            valor_por_unidade=ValorProvento(Decimal("0.55")),
            data_pagamento=date(2026, 7, 20),
            periodo_referencia="",
            isento_ir=True,
        )

        class _Documento:
            def __init__(self, p):
                self.provento = p

        repo = self._repo(documentos=[_Documento(provento)])
        proventos = repo.obter_proventos("ALZR11", REFERENCIA)
        assert len(proventos) == 1
        assert proventos[0].valor_por_unidade.value == Decimal("0.55")

    def test_obter_patrimonio_indisponivel(self):
        repo = self._repo()
        assert repo.obter_patrimonio("ALZR11", REFERENCIA) is None
