import base64
import json

import pytest
import responses

from flowscope.infrastructure.b3 import funds_client as fc
from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.cache import CacheManager

_LISTED = fc._LISTED_BASE_URL
_CADASTRO = fc._CADASTRO_EMPRESAS_URL


def _token(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"))
    return base64.b64encode(raw.encode()).decode()


class TestResolverCodeCvm:
    @responses.activate
    def test_ticker_listado_retorna_code_cvm(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        payload = {"language": "pt-br", "pageNumber": 1, "pageSize": 20, "tradingName": "PETR4"}
        responses.get(
            f"{_LISTED}/GetListedCompany/{_token(payload)}",
            json={
                "page": {"totalPages": 1},
                "results": [
                    {
                        "codeCVM": "009512",
                        "companyName": "PETROLEO BRASILEIRO S.A. PETROBRAS",
                        "tradingName": "PETROBRAS",
                    }
                ],
            },
            status=200,
        )
        assert client.resolver_code_cvm("PETR4") == "9512"

    @responses.activate
    def test_ticker_invalido_retorna_none(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        payload = {"language": "pt-br", "pageNumber": 1, "pageSize": 20, "tradingName": "TICKER_INEXISTENTE"}
        responses.get(
            f"{_LISTED}/GetListedCompany/{_token(payload)}",
            json={"page": {"totalPages": 1}, "results": []},
            status=200,
        )
        assert client.resolver_code_cvm("TICKER_INEXISTENTE") is None
        assert len(responses.calls) == 1

    @responses.activate
    def test_segunda_chamada_usando_cache(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        payload = {"language": "pt-br", "pageNumber": 1, "pageSize": 20, "tradingName": "VALE3"}
        url = f"{_LISTED}/GetListedCompany/{_token(payload)}"
        responses.get(
            url,
            json={"page": {"totalPages": 1}, "results": [{"codeCVM": "4170"}]},
            status=200,
        )
        assert client.resolver_code_cvm("VALE3") == "4170"
        assert client.resolver_code_cvm("VALE3") == "4170"
        assert len(responses.calls) == 1

    @responses.activate
    def test_cache_armazena_none(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        payload = {"language": "pt-br", "pageNumber": 1, "pageSize": 20, "tradingName": "SEM_CVM"}
        url = f"{_LISTED}/GetListedCompany/{_token(payload)}"
        responses.get(url, json={"page": {"totalPages": 1}, "results": []}, status=200)
        assert client.resolver_code_cvm("SEM_CVM") is None
        assert client.resolver_code_cvm("SEM_CVM") is None
        assert len(responses.calls) == 1

    @responses.activate
    def test_api_indisponivel_usa_cadastro_csv(self, tmp_path):
        client = B3FundosClient(
            cache=CacheManager(cache_dir=tmp_path), retry_delays=(0,)
        )
        payload = {"language": "pt-br", "pageNumber": 1, "pageSize": 20, "tradingName": "ITUB4"}
        responses.get(
            f"{_LISTED}/GetListedCompany/{_token(payload)}", status=500
        )
        csv = (
            "Empresa;Ticker;Código CVM;Segmento\n"
            "PETROBRAS;PETR4;009512;N2\n"
            "ITAÚ UNIBANCO;ITUB4;000751;N1\n"
        )
        responses.get(_CADASTRO, body=csv, status=200)
        assert client.resolver_code_cvm("ITUB4") == "751"


class TestMontarIndice:
    def test_monta_indice_do_csv(self):
        csv = (
            "Empresa;Ticker;Código CVM;Segmento\n"
            "PETROBRAS;PETR4;009512;N2\n"
            "VALE;VALE3;4170;NM\n"
        )
        indice = fc.montar_indice_code_cvm(csv)
        assert indice == {"PETR4": "9512", "VALE3": "4170"}

    def test_csv_vazio_retorna_dict_vazio(self):
        assert fc.montar_indice_code_cvm("") == {}

    def test_sem_colunas_esperadas_retorna_vazio(self):
        csv = "Nome;Cidade\nA;B\n"
        assert fc.montar_indice_code_cvm(csv) == {}
