import base64
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
    B3InformeMensal,
    B3ReportReference,
)
from flowscope.domain.fii.analysis import PatrimonioFii
from flowscope.infrastructure.b3.encoder import encode_b3_payload
from flowscope.infrastructure.b3.fund_repository import B3FundRepository
from flowscope.infrastructure.b3.funds_client import (
    B3FundosClient,
    _selecionar_fund,
)
from flowscope.infrastructure.b3.informe_mensal_parser import (
    extrair_informe_mensal,
)
from flowscope.infrastructure.b3.rate_limit import SerializadorPorHost
from flowscope.infrastructure.b3.reports_repository import (
    B3ReportsRepository,
    _payload,
)
from flowscope.infrastructure.b3.retry import executar_com_retry
from flowscope.infrastructure.cache import CacheManager

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "b3"
REFERENCIA = date(2026, 9, 4)


def _fixture(nome: str) -> object:
    return json.loads((_FIXTURES / nome).read_text(encoding="utf-8"))


def _decodificar_token(url: str) -> dict:
    token = url.rstrip("/").rsplit("/", 1)[-1]
    return json.loads(base64.b64decode(token).decode("utf-8"))


class _RespostaJson:
    def __init__(self, payload: object) -> None:
        self._payload = payload
        self.status_code = 200
        self.headers: dict[str, str] = {}

    @property
    def text(self) -> str:
        return json.dumps(self._payload)

    def json(self) -> object:
        return self._payload

    def raise_for_status(self) -> None:
        pass


class _SessaoFake:
    def __init__(self, respostas: list) -> None:
        self._respostas = list(respostas)
        self.urls: list[str] = []

    def get(self, url: str, **kwargs) -> _RespostaJson:
        self.urls.append(url)
        indice = len(self.urls) - 1
        resposta = self._respostas[min(indice, len(self._respostas) - 1)]
        if isinstance(resposta, Exception):
            raise resposta
        return _RespostaJson(resposta)


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

    def _repo_patrimonio(self, informe=None, cvm=None, erro_informe=None):
        from flowscope.infrastructure.fii.b3_fundamental_repository import (
            B3FundamentalRepository,
        )

        class _Fundos:
            def find_by_ticker(self, ticker):
                return _FundoFake()

        class _Relatorios:
            def extrair_proventos(self, *args, **kwargs):
                return []

            def extrair_informe(self, *args, **kwargs):
                if erro_informe is not None:
                    raise erro_informe
                return informe

        class _Cvm:
            def patrimonio(self, ticker, reference_date):
                return cvm

        return B3FundamentalRepository(
            fund_repository=_Fundos(),
            reports_repository=_Relatorios(),
            patrimonio_source=_Cvm(),
        )

    def test_obter_patrimonio_b3_primario(self):
        informe = B3InformeMensal(
            document_id=1,
            reference_date=REFERENCIA,
            reference_month="07/2026",
            cotistas=206111,
            patrimonio_liquido=Decimal("1773014664.80"),
            cotas_emitidas=Decimal("164444501.0000"),
            valor_patrimonial_cota=Decimal("10.781842"),
        )
        cvm = PatrimonioFii(REFERENCIA, Decimal(1), Decimal(1), 1, "CVM")
        repo = self._repo_patrimonio(informe=informe, cvm=cvm)
        resultado = repo.obter_patrimonio("ALZR11", REFERENCIA)
        assert resultado is not None
        assert resultado.fonte == "B3"
        assert resultado.cotistas == 206111
        assert resultado.net_asset_value == Decimal("1773014664.80")
        assert resultado.vp_cota == Decimal("10.781842")

    def test_obter_patrimonio_cvm_fallback(self):
        cvm = PatrimonioFii(
            REFERENCIA, Decimal(2943000000), Decimal(144355726), 100000, "CVM"
        )
        repo = self._repo_patrimonio(informe=None, cvm=cvm)
        assert repo.obter_patrimonio("ALZR11", REFERENCIA) is cvm

    def test_obter_patrimonio_ambos_ausentes(self):
        repo = self._repo_patrimonio(informe=None, cvm=None)
        assert repo.obter_patrimonio("ALZR11", REFERENCIA) is None

    def test_obter_patrimonio_b3_indisponivel_usa_cvm(self):
        cvm = PatrimonioFii(REFERENCIA, Decimal(1), Decimal(1), 1, "CVM")
        repo = self._repo_patrimonio(
            erro_informe=requests.ConnectionError("fora do ar"), cvm=cvm
        )
        assert repo.obter_patrimonio("ALZR11", REFERENCIA) is cvm


class TestListarFundos:
    def _client(self, tmp_path, respostas):
        return B3FundosClient(
            cache=CacheManager(cache_dir=tmp_path),
            session=_SessaoFake(respostas),
            retry_delays=(0,),
        )

    def test_pagina_multiplas_paginas(self, tmp_path):
        pagina1 = {
            "page": {"pageNumber": 1, "totalPages": 2},
            "results": [{"acronym": "ALZR", "id": 870}],
        }
        pagina2 = {
            "page": {"pageNumber": 2, "totalPages": 2},
            "results": [
                {"acronym": "HGLG", "id": 123},
                {"acronym": "VISC", "id": 456},
            ],
        }
        client = self._client(tmp_path, [pagina1, pagina2])
        fundos = client.listar_fundos("FII")
        assert [fundo["acronym"] for fundo in fundos] == ["ALZR", "HGLG", "VISC"]

    def test_resolver_ticker_fluxo_completo(self, tmp_path):
        fundos = {
            "page": {"totalPages": 1},
            "results": [{"acronym": "ALZR", "id": 870}],
        }
        classes = _fixture("fund_alzr.json")
        sessao = _SessaoFake([fundos, classes])
        client = B3FundosClient(
            cache=CacheManager(cache_dir=tmp_path),
            session=sessao,
            retry_delays=(0,),
        )
        assert client.resolver_ticker("ALZR11") == "20294"
        classe_url = [url for url in sessao.urls if "GetListClassFund" in url][-1]
        assert _decodificar_token(classe_url)["idFNET"] == "870"

    def test_resolver_ticker_nao_cacheia_ausencia(self, tmp_path):
        vazio = {"page": {"totalPages": 1}, "results": []}
        fundos = {
            "page": {"totalPages": 1},
            "results": [{"acronym": "ALZR", "id": 870}],
        }
        classes = _fixture("fund_alzr.json")
        client = self._client(
            tmp_path, [vazio, vazio, vazio, vazio, fundos, classes]
        )
        assert client.resolver_ticker("ALZR11") is None
        assert client.resolver_ticker("ALZR11") == "20294"


class TestResolucaoMultiTipo:
    def _client(self, tmp_path, respostas):
        return B3FundosClient(
            cache=CacheManager(cache_dir=tmp_path),
            session=_SessaoFake(respostas),
            retry_delays=(0,),
        )

    def _vazio(self):
        return {"page": {"totalPages": 1}, "results": []}

    def _fiagro(self):
        return {
            "page": {"totalPages": 1},
            "results": [{"acronym": "BBGO", "id": 6919}],
        }

    def _classe_fiagro(self):
        return [
            {
                "id": "999",
                "idMain": None,
                "tradingName": "BBGO FUNDO - 12.345.678/0001-95",
                "fundName": "BBGO FIAGRO",
            }
        ]

    def test_fiagro_resolvido_fora_do_tipo_fii(self, tmp_path):
        sessao = _SessaoFake([self._vazio(), self._fiagro(), self._classe_fiagro()])
        client = B3FundosClient(
            cache=CacheManager(cache_dir=tmp_path),
            session=sessao,
            retry_delays=(0,),
        )
        assert client.resolver_ticker("BBGO11") == "999"
        classe_url = [url for url in sessao.urls if "GetListClassFund" in url][-1]
        assert _decodificar_token(classe_url)["typeFund"] == "FIAGRO"

    def test_tipo_fundo_fiagro(self, tmp_path):
        client = self._client(
            tmp_path, [self._vazio(), self._fiagro(), self._classe_fiagro()]
        )
        assert client.tipo_fundo("BBGO11") == "FIAGRO"

    def test_listagem_por_tipo_e_cacheada(self, tmp_path):
        client = self._client(tmp_path, [self._fiagro()])
        client.listar_fundos("FIAGRO")
        client.listar_fundos("FIAGRO")
        urls = [url for url in client._session.urls if "GetListFunds" in url]
        assert len(urls) == 1

    def test_ticker_inexistente_retorna_ausencia(self, tmp_path):
        client = self._client(tmp_path, [self._vazio()])
        assert client.resolver_ticker("XPTO11") is None
        assert client.tipo_fundo("XPTO11") is None

    def test_resolver_identidade_cnpj_fiagro(self, tmp_path):
        from flowscope.infrastructure.cvm.identity import resolver_identidade

        client = self._client(
            tmp_path, [self._vazio(), self._fiagro(), self._classe_fiagro()]
        )
        repo = B3FundRepository(client=client)
        identidade = resolver_identidade("BBGO11", fund_repository=repo)
        assert identidade is not None
        assert identidade.cnpj_fundo_classe == "12345678000195"


class TestInformeMensalParser:
    def test_extrai_campos_do_informe(self):
        html = (_FIXTURES / "informe_alzr.html").read_text(encoding="utf-8")
        informe = extrair_informe_mensal(
            html,
            document_id=1293566,
            reference_date=date(2026, 7, 1),
            reference_month="07/2026",
        )
        assert informe.cotistas == 206111
        assert informe.patrimonio_liquido == Decimal("1773014664.80")
        assert informe.cotas_emitidas == Decimal("164444501.0000")
        assert informe.valor_patrimonial_cota == Decimal("10.781842")
        assert informe.reference_date == date(2026, 7, 1)
        assert informe.fonte == "B3"

    def test_sem_campos_retorna_none(self):
        informe = extrair_informe_mensal(
            "<html><body></body></html>", document_id=1
        )
        assert informe.cotistas is None
        assert informe.patrimonio_liquido is None
        assert informe.cotas_emitidas is None
        assert informe.valor_patrimonial_cota is None
        assert informe.cnpj is None
        assert informe.nome_administrador is None
        assert informe.cnpj_administrador is None

    def test_extrai_identidade_fiscal(self):
        html = (_FIXTURES / "informe_cycr.html").read_text(encoding="utf-8")
        informe = extrair_informe_mensal(html, document_id=1294589)
        assert informe.cnpj == "36.501.233/0001-15"
        assert informe.nome_administrador == "BANCO GENIAL S.A."
        assert informe.cnpj_administrador == "45.246.410/0001-55"

    def test_extrai_classificacao_autorregulacao(self):
        html = (_FIXTURES / "informe_cycr.html").read_text(encoding="utf-8")
        informe = extrair_informe_mensal(html, document_id=1294589)
        assert informe.classificacao == "Papel"
        assert informe.subclassificacao == "Híbrido"
        assert informe.gestao == "Ativa"
        assert informe.segmento_atuacao == "Outros"

    def test_sem_classificacao_mantem_demais_campos(self):
        html = (_FIXTURES / "informe_alzr.html").read_text(encoding="utf-8")
        informe = extrair_informe_mensal(html, document_id=1293566)
        assert informe.classificacao is None
        assert informe.subclassificacao is None
        assert informe.gestao is None
        assert informe.segmento_atuacao is None
        assert informe.cotistas == 206111
        assert informe.patrimonio_liquido == Decimal("1773014664.80")


class TestB3FundamentalDataProvider:
    def _provider(self, informe, patrimonio=None):
        class _Repo:
            def obter_nome(self, ticker):
                return "CYRELA CRÉDITO"

            def obter_informe(self, ticker, reference_date):
                return informe

            def obter_patrimonio(self, ticker, reference_date):
                return patrimonio

        from flowscope.infrastructure.fii.b3_fundamental_provider import (
            B3FundamentalDataProvider,
        )

        return B3FundamentalDataProvider(_Repo())

    def test_emite_identidade_fiscal(self):
        informe = B3InformeMensal(
            document_id=1,
            reference_date=date(2026, 7, 1),
            reference_month="07/2026",
            cotistas=None,
            patrimonio_liquido=None,
            cotas_emitidas=None,
            valor_patrimonial_cota=None,
            cnpj="36.501.233/0001-15",
            nome_administrador="BANCO GENIAL S.A.",
            cnpj_administrador="45.246.410/0001-55",
        )
        campos = self._provider(informe).obter("CYCR11", REFERENCIA)
        assert campos["cnpj"].valor == "36.501.233/0001-15"
        assert campos["administrador"].valor == "BANCO GENIAL S.A."
        assert campos["cnpj_administrador"].valor == "45.246.410/0001-55"
        assert campos["cnpj"].fonte == "B3"

    def test_emite_classificacao_autorregulacao(self):
        informe = B3InformeMensal(
            document_id=1,
            reference_date=date(2026, 7, 1),
            reference_month="07/2026",
            cotistas=16778,
            patrimonio_liquido=Decimal("346086182.72"),
            cotas_emitidas=Decimal(36549445),
            valor_patrimonial_cota=Decimal("9.468986"),
            classificacao="Papel",
            subclassificacao="Híbrido",
            gestao="Ativa",
            segmento_atuacao="Outros",
        )
        campos = self._provider(informe).obter("CYCR11", REFERENCIA)
        assert campos["classificacao_fii"].valor == "Papel"
        assert campos["discriminador"].valor == "fii"
        assert campos["segmento"].valor == "Outros"
        assert campos["gestao"].valor == "Ativa"
        assert all(campo.fonte == "B3" for campo in campos.values())

    def test_emite_vp_cota_reportado(self):
        informe = B3InformeMensal(
            document_id=1,
            reference_date=date(2026, 7, 1),
            reference_month="07/2026",
            cotistas=None,
            patrimonio_liquido=None,
            cotas_emitidas=None,
            valor_patrimonial_cota=None,
        )
        patrimonio = PatrimonioFii(
            reference_date=REFERENCIA,
            net_asset_value=Decimal("346086182.72"),
            shares_outstanding=Decimal(36549445),
            cotistas=16778,
            fonte="B3",
            vp_cota=Decimal("9.468986"),
        )
        campos = self._provider(informe, patrimonio).obter("CYCR11", REFERENCIA)
        assert campos["vp_cota"].valor == Decimal("9.468986")

    def test_deriva_vp_cota_quando_ausente(self):
        informe = B3InformeMensal(
            document_id=1,
            reference_date=date(2026, 7, 1),
            reference_month="07/2026",
            cotistas=None,
            patrimonio_liquido=None,
            cotas_emitidas=None,
            valor_patrimonial_cota=None,
        )
        patrimonio = PatrimonioFii(
            reference_date=REFERENCIA,
            net_asset_value=Decimal(100),
            shares_outstanding=Decimal(10),
            cotistas=None,
            fonte="B3",
        )
        campos = self._provider(informe, patrimonio).obter("CYCR11", REFERENCIA)
        assert campos["vp_cota"].valor == Decimal(10)

    def test_sem_informe_emite_apenas_nome(self):
        campos = self._provider(None).obter("CYCR11", REFERENCIA)
        assert "cnpj" not in campos
        assert "classificacao_fii" not in campos


class TestB3FundamentalRepositoryPatrimonio:
    def test_patrimonio_memoizado_por_ticker_e_data(self):
        from flowscope.infrastructure.fii.b3_fundamental_repository import (
            B3FundamentalRepository,
        )

        class _Fundos:
            def find_by_ticker(self, ticker):
                return None

        class _FonteCvm:
            def __init__(self):
                self.chamadas = 0

            def patrimonio(self, ticker, reference_date):
                self.chamadas += 1
                return PatrimonioFii(
                    reference_date=reference_date,
                    net_asset_value=Decimal(100),
                    shares_outstanding=Decimal(10),
                    cotistas=None,
                    fonte="CVM",
                )

        fonte = _FonteCvm()
        repo = B3FundamentalRepository(
            fund_repository=_Fundos(), patrimonio_source=fonte
        )
        primeiro = repo.obter_patrimonio("CYCR11", REFERENCIA)
        segundo = repo.obter_patrimonio("CYCR11", REFERENCIA)
        assert primeiro is segundo
        assert fonte.chamadas == 1


class TestInformeMensalRepository:
    def test_get_monthly_reports_lista_referencias(self):
        documentos = _fixture("monthly_reports_alzr.json")["results"]
        repo = B3ReportsRepository(client=_ClienteFake(documentos=documentos))
        referencias = repo.get_monthly_reports(
            "20294", date(2026, 1, 1), REFERENCIA
        )
        assert len(referencias) == 2
        assert referencias[0].report_type == "Informe Mensal Estruturado"

    def test_extrair_informe_mais_recente_ate_referencia(self):
        html = (_FIXTURES / "informe_alzr.html").read_text(encoding="utf-8")

        class _ClienteInforme:
            def __init__(self):
                self.baixado = None

            def listar_documentos(self, *args, **kwargs):
                return [
                    {
                        "urlViewerFundosNet": "https://fnet?id=1250291",
                        "referenceDate": "2026-06-01T00:00:00-03:00",
                        "referenceDateFormat": "06/2026",
                        "status": "1 (Ativo)",
                    },
                    {
                        "urlViewerFundosNet": "https://fnet?id=1293566",
                        "referenceDate": "2026-07-01T00:00:00-03:00",
                        "referenceDateFormat": "07/2026",
                        "status": "1 (Ativo)",
                    },
                    {
                        "urlViewerFundosNet": "https://fnet?id=999",
                        "referenceDate": "2026-08-01T00:00:00-03:00",
                        "referenceDateFormat": "08/2026",
                        "status": "1 (Ativo)",
                    },
                ]

            def buscar_html_documento(self, id_documento):
                self.baixado = id_documento
                return html

        cliente = _ClienteInforme()
        repo = B3ReportsRepository(client=cliente)
        informe = repo.extrair_informe(
            "20294", date(2026, 1, 1), REFERENCIA, date(2026, 7, 15)
        )
        assert informe is not None
        assert informe.document_id == 1293566
        assert cliente.baixado == "1293566"

    def test_extrair_informe_sem_documentos_retorna_none(self):
        repo = B3ReportsRepository(client=_ClienteFake(documentos=[]))
        assert (
            repo.extrair_informe("20294", date(2026, 1, 1), REFERENCIA, REFERENCIA)
            is None
        )

    def test_extrair_informe_falha_de_download_propaga(self):
        class _ClienteFalha:
            def listar_documentos(self, *args, **kwargs):
                return [
                    {
                        "urlViewerFundosNet": "https://fnet?id=1",
                        "referenceDate": "2026-07-01T00:00:00-03:00",
                        "status": "1 (Ativo)",
                    }
                ]

            def buscar_html_documento(self, id_documento):
                raise requests.ConnectionError("fora do ar")

        repo = B3ReportsRepository(client=_ClienteFalha())
        with pytest.raises(requests.ConnectionError):
            repo.extrair_informe(
                "20294", date(2026, 1, 1), REFERENCIA, REFERENCIA
            )
