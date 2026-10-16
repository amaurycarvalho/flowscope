import base64
import json

import pytest
import responses

from flowscope.infrastructure.b3 import funds_client as fc
from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.cache import CacheManager

_LISTED = fc._LISTED_BASE_URL


def _token(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"))
    return base64.b64encode(raw.encode()).decode()


def _url_empresas(company: str, page_number: int = 1) -> str:
    payload = {
        "language": "pt-br",
        "pageNumber": page_number,
        "pageSize": 120,
        "company": company,
    }
    return f"{_LISTED}/GetInitialCompanies/{_token(payload)}"


class TestResolverCodeCvm:
    @responses.activate
    def test_ticker_listado_retorna_code_cvm(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(
            _url_empresas("PETR"),
            json={
                "page": {"totalPages": 1},
                "results": [
                    {
                        "codeCVM": "009512",
                        "issuingCompany": "PETR",
                        "companyName": "PETROLEO BRASILEIRO S.A. PETROBRAS",
                    }
                ],
            },
            status=200,
        )
        assert client.resolver_code_cvm("PETR4") == "9512"

    @responses.activate
    def test_casa_pela_raiz_do_ticker_e_ignora_homonimos(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(
            _url_empresas("VALE"),
            json={
                "page": {"totalPages": 1},
                "results": [
                    {"codeCVM": "913574", "issuingCompany": "ADAG"},
                    {"codeCVM": "4170", "issuingCompany": "VALE"},
                ],
            },
            status=200,
        )
        assert client.resolver_code_cvm("VALE3") == "4170"

    @responses.activate
    def test_pagina_ate_encontrar_a_raiz(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(
            _url_empresas("AGRO", page_number=1),
            json={
                "page": {"totalPages": 2},
                "results": [{"codeCVM": "1", "issuingCompany": "OUTRO"}],
            },
            status=200,
        )
        responses.get(
            _url_empresas("AGRO", page_number=2),
            json={
                "page": {"totalPages": 2},
                "results": [
                    {"codeCVM": "20036", "issuingCompany": "AGRO"},
                ],
            },
            status=200,
        )
        assert client.resolver_code_cvm("AGRO3") == "20036"
        assert len(responses.calls) == 2

    @responses.activate
    def test_ticker_invalido_retorna_none(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(
            _url_empresas("TICKER_INEXISTENTE"),
            json={"page": {"totalPages": 1}, "results": []},
            status=200,
        )
        assert client.resolver_code_cvm("TICKER_INEXISTENTE") is None
        assert len(responses.calls) == 1

    @responses.activate
    def test_segunda_chamada_usando_cache(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(
            _url_empresas("VALE"),
            json={"page": {"totalPages": 1}, "results": [{"codeCVM": "4170", "issuingCompany": "VALE"}]},
            status=200,
        )
        assert client.resolver_code_cvm("VALE3") == "4170"
        assert client.resolver_code_cvm("VALE3") == "4170"
        assert len(responses.calls) == 1

    @responses.activate
    def test_cache_armazena_none(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(_url_empresas("SEM_CVM"), json={"page": {"totalPages": 1}, "results": []}, status=200)
        assert client.resolver_code_cvm("SEM_CVM") is None
        assert client.resolver_code_cvm("SEM_CVM") is None
        assert len(responses.calls) == 1

    @responses.activate
    def test_api_indisponivel_nao_usa_cadastro_csv(self, tmp_path):
        client = B3FundosClient(
            cache=CacheManager(cache_dir=tmp_path), retry_delays=(0,)
        )
        responses.get(_url_empresas("ITUB"), status=500)
        assert client.resolver_code_cvm("ITUB4") is None
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == _url_empresas("ITUB")

    @responses.activate
    def test_falha_de_resolucao_nao_e_cacheada(self, tmp_path):
        cache = CacheManager(cache_dir=tmp_path)
        client = B3FundosClient(cache=cache, retry_delays=(0,))
        responses.get(_url_empresas("ITUB"), status=500)
        assert client.resolver_code_cvm("ITUB4") is None
        chave = client._chave_cache("codecvm", "ITUB4")
        assert cache.read_meta(chave) is None
        responses.get(
            _url_empresas("ITUB"),
            json={
                "page": {"totalPages": 1},
                "results": [{"codeCVM": "751", "issuingCompany": "ITUB"}],
            },
            status=200,
        )
        assert client.resolver_code_cvm("ITUB4") == "751"
        assert len(responses.calls) == 2

    @responses.activate
    def test_nome_de_negociacao_reaproveita_cache(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(
            _url_empresas("PETR"),
            json={
                "page": {"totalPages": 1},
                "results": [
                    {
                        "codeCVM": "009512",
                        "issuingCompany": "PETR",
                        "companyName": "PETROLEO BRASILEIRO S.A. PETROBRAS",
                        "tradingName": "PETROBRAS",
                    }
                ],
            },
            status=200,
        )
        assert client.resolver_code_cvm("PETR4") == "9512"
        assert client.obter_nome_negociacao("PETR4") == "PETROBRAS"
        assert len(responses.calls) == 1

    @responses.activate
    def test_nome_usa_company_name_quando_sem_trading_name(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(
            _url_empresas("VALE"),
            json={
                "page": {"totalPages": 1},
                "results": [
                    {
                        "codeCVM": "4170",
                        "issuingCompany": "VALE",
                        "companyName": "VALE S.A.",
                    }
                ],
            },
            status=200,
        )
        assert client.obter_nome_negociacao("VALE3") == "VALE S.A."
