import base64
import json
from datetime import date
from unittest.mock import MagicMock

import pytest
import responses

from flowscope.infrastructure.b3.client import B3Client
from flowscope.infrastructure.cache import CacheManager

_BASE = B3Client._BASE_URL
_PORTFOLIO_BASE = B3Client._BASE_PORTFOLIO_URL


@pytest.fixture
def b3_client(tmp_path) -> B3Client:
    return B3Client(cache=CacheManager(cache_dir=tmp_path))


class TestFetchFile:
    @responses.activate
    def test_cache_hit_retorna_sem_requisicao(self, b3_client: B3Client):
        d = date(2026, 6, 25)
        b3_client._cache.put(d, "cached-content")
        result = b3_client.fetch_file(d)
        assert result == "cached-content"

    @responses.activate
    def test_cache_miss_faz_requisicao_http(self, b3_client: B3Client):
        d = date(2026, 6, 25)
        responses.get(
            f"{_BASE}/api/download/requestname",
            json={"token": "abc123"},
            status=200,
        )
        responses.get(
            f"{_BASE}/api/download/",
            body="date;ticker\n2026-06-25;PETR4",
            status=200,
        )
        result = b3_client.fetch_file(d)
        assert "PETR4" in result
        cached = b3_client._cache.get(d)
        assert cached == result

    @responses.activate
    def test_erro_http_levanta_runtime_error(self, b3_client: B3Client):
        d = date(2026, 6, 25)
        responses.get(f"{_BASE}/api/download/requestname", status=500)
        with pytest.raises(RuntimeError, match="Erro HTTP"):
            b3_client.fetch_file(d)

    @responses.activate
    def test_callback_cache_hit(self, b3_client: B3Client):
        d = date(2026, 6, 25)
        b3_client._cache.put(d, "cached-content")
        callback = MagicMock()
        b3_client.fetch_file(d, progress_callback=callback)
        callback.assert_called_once_with(f"{d} (em cache)", False)

    @responses.activate
    def test_callback_cache_miss(self, b3_client: B3Client):
        d = date(2026, 6, 25)
        responses.get(
            f"{_BASE}/api/download/requestname",
            json={"token": "t1"},
            status=200,
        )
        responses.get(f"{_BASE}/api/download/", body="data", status=200)
        callback = MagicMock()
        b3_client.fetch_file(d, progress_callback=callback)
        callback.assert_called_once()


class TestFetchPortfolio:
    @responses.activate
    def test_sucesso_retorna_tickers(self, b3_client: B3Client):
        raw = (
            "IBOV - Carteira do Dia\n"
            "Código;Ação;Tipo;Qtde. Teórica;Part. (%)\n"
            "PETR4;PETROBRAS;PN;100;10\n"
            "VALE3;VALE;ON;200;20\n"
        )
        b64 = base64.b64encode(raw.encode("latin-1")).decode()
        responses.get(f"{_PORTFOLIO_BASE}?index=IBOV&language=pt-br", status=404)
        url = b3_client._build_portfolio_url("IBOV")
        responses.get(url, body=b64, status=200)
        result = b3_client.fetch_portfolio("IBOV")
        assert result == ["PETR4", "VALE3"]

    @responses.activate
    def test_resposta_vazia_retorna_lista_vazia(self, b3_client: B3Client):
        url = b3_client._build_portfolio_url("IBOV")
        responses.get(url, body="", status=200)
        result = b3_client.fetch_portfolio("IBOV")
        assert result == []

    @responses.activate
    def test_erro_http_retorna_lista_vazia(self, b3_client: B3Client):
        url = b3_client._build_portfolio_url("IBOV")
        responses.get(url, status=500)
        result = b3_client.fetch_portfolio("IBOV")
        assert result == []


class TestBuildPortfolioUrl:
    def test_url_contem_base64_do_payload(self, tmp_path):
        client = B3Client(cache=CacheManager(cache_dir=tmp_path))
        url = client._build_portfolio_url("IBOV")
        assert url.startswith(_PORTFOLIO_BASE)
        b64_part = url[len(_PORTFOLIO_BASE):]
        decoded = base64.b64decode(b64_part).decode()
        payload = json.loads(decoded)
        assert payload == {"index": "IBOV", "language": "pt-br"}
