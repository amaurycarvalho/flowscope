import base64
import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
import responses

from flowscope.infrastructure.b3.client import B3Client
from flowscope.infrastructure.cache import CacheManager

_BASE = B3Client._BASE_URL
_PORTFOLIO_BASE = B3Client._BASE_PORTFOLIO_URL


@pytest.fixture
def b3_client(tmp_path) -> B3Client:
    return B3Client(cache=CacheManager(cache_dir=tmp_path))


class TestBustStalePortfolioCache:
    def test_removes_empty_cache_files(self, tmp_path):
        cache = CacheManager(cache_dir=tmp_path)
        for index in ("IBOV", "IDIV", "IFIX"):
            meta = tmp_path / f"portfolio_{index}.json"
            meta.write_text(json.dumps({"tickers": [], "index": index}), encoding="utf-8")
        B3Client(cache=cache)
        for index in ("IBOV", "IDIV", "IFIX"):
            assert not (tmp_path / f"portfolio_{index}.json").exists()

    def test_keeps_non_empty_cache_files(self, tmp_path):
        cache = CacheManager(cache_dir=tmp_path)
        meta = tmp_path / "portfolio_IBOV.json"
        meta.write_text(json.dumps({"tickers": ["PETR4"], "index": "IBOV"}), encoding="utf-8")
        B3Client(cache=cache)
        assert meta.exists()

    def test_ignores_invalid_json(self, tmp_path):
        cache = CacheManager(cache_dir=tmp_path)
        meta = tmp_path / "portfolio_IBOV.json"
        meta.write_text("not-json", encoding="utf-8")
        B3Client(cache=cache)
        assert meta.exists()


class TestRequestToken:
    @patch("requests.get")
    def test_passes_expected_params_and_timeout(self, mock_get, b3_client: B3Client):
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = {"token": "abc"}
        b3_client._request_token("TradeInformationConsolidated", date(2026, 6, 25))
        args, kwargs = mock_get.call_args
        assert args[0] == f"{_BASE}/api/download/requestname"
        assert kwargs["params"] == {
            "fileName": "TradeInformationConsolidated",
            "date": "2026-06-25",
        }
        assert kwargs["timeout"] == 30

    @patch("requests.get")
    def test_http_error_raises(self, mock_get, b3_client: B3Client):
        from requests import HTTPError

        mock_get.return_value.raise_for_status.side_effect = HTTPError("boom")
        with pytest.raises(RuntimeError, match="Erro HTTP"):
            b3_client._request_token("X", date(2026, 6, 25))


class TestDownloadCSV:
    @patch("requests.get")
    def test_passes_token_and_timeout(self, mock_get, b3_client: B3Client):
        resp = mock_get.return_value
        resp.raise_for_status.return_value = None
        resp.apparent_encoding = "latin-1"
        resp.text = "data"
        b3_client._download_csv("tok123")
        args, kwargs = mock_get.call_args
        assert args[0] == f"{_BASE}/api/download/"
        assert kwargs["params"] == {"token": "tok123"}
        assert kwargs["timeout"] == 60

    @patch("requests.get")
    def test_encoding_fallback_to_utf8(self, mock_get, b3_client: B3Client):
        resp = mock_get.return_value
        resp.raise_for_status.return_value = None
        resp.apparent_encoding = None
        resp.text = "data"
        b3_client._download_csv("tok")
        assert resp.encoding == "utf-8"

    @patch("requests.get")
    def test_http_error_raises(self, mock_get, b3_client: B3Client):
        from requests import HTTPError

        mock_get.return_value.raise_for_status.side_effect = HTTPError("boom")
        with pytest.raises(RuntimeError, match="Erro HTTP"):
            b3_client._download_csv("tok")


class TestFetchFileCacheOnly:
    @responses.activate
    def test_cache_only_callback_sem_cache(self, b3_client: B3Client):
        d = date(2026, 6, 25)
        callback = MagicMock()
        result = b3_client.fetch_file(d, progress_callback=callback, cache_only=True)
        assert result is None
        callback.assert_called_once_with(f"{d} (sem cache)", True)

    @responses.activate
    def test_cache_only_sem_callback(self, b3_client: B3Client):
        d = date(2026, 6, 25)
        assert b3_client.fetch_file(d, cache_only=True) is None


class TestFetchFileCallbacks:
    @responses.activate
    def test_callback_after_download(self, b3_client: B3Client):
        d = date(2026, 6, 25)
        responses.get(f"{_BASE}/api/download/requestname", json={"token": "t1"}, status=200)
        responses.get(f"{_BASE}/api/download/", body="data", status=200)
        callback = MagicMock()
        b3_client.fetch_file(d, progress_callback=callback)
        callback.assert_any_call(str(d), False)

    @responses.activate
    def test_default_file_name_in_request(self, b3_client: B3Client):
        d = date(2026, 6, 25)
        responses.get(f"{_BASE}/api/download/requestname", json={"token": "t1"}, status=200)
        responses.get(f"{_BASE}/api/download/", body="data", status=200)
        b3_client.fetch_file(d)
        url = responses.calls[0].request.url
        assert "fileName=TradeInformationConsolidated" in url
        assert "date=2026-06-25" in url

    @responses.activate
    def test_uses_redirect_url_when_no_token(self, b3_client: B3Client):
        d = date(2026, 6, 25)
        responses.get(f"{_BASE}/api/download/requestname", json={"redirectUrl": "tokX"}, status=200)
        responses.get(f"{_BASE}/api/download/", body="data", status=200)
        result = b3_client.fetch_file(d)
        assert result == "data"
        url = responses.calls[1].request.url
        assert "token=tokX" in url

    @responses.activate
    def test_uses_token_when_present(self, b3_client: B3Client):
        d = date(2026, 6, 25)
        responses.get(f"{_BASE}/api/download/requestname", json={"token": "abc123"}, status=200)
        responses.get(f"{_BASE}/api/download/", body="data", status=200)
        b3_client.fetch_file(d)
        url = responses.calls[1].request.url
        assert "token=abc123" in url

    @responses.activate
    def test_no_token_no_redirect_uses_empty(self, b3_client: B3Client):
        d = date(2026, 6, 25)
        responses.get(f"{_BASE}/api/download/requestname", json={"nope": "x"}, status=200)
        responses.get(f"{_BASE}/api/download/", body="data", status=200)
        b3_client.fetch_file(d)
        url = responses.calls[1].request.url
        assert "token=" in url
        assert "None" not in url


class TestFetchPortfolioCallbacks:
    @responses.activate
    def test_callback_success(self, b3_client: B3Client):
        raw = "PETR4;PETROBRAS;PN;100;10\nVALE3;VALE;ON;200;20\n"
        b64 = base64.b64encode(raw.encode("latin-1")).decode()
        url = b3_client._build_portfolio_url("IBOV")
        responses.get(url, body=b64, status=200)
        callback = MagicMock()
        result = b3_client.fetch_portfolio("IBOV", progress_callback=callback)
        assert result == ["PETR4", "VALE3"]
        callback.assert_called_once_with("Portfólio IBOV: 2 ativos", False)

    @responses.activate
    def test_callback_failure(self, b3_client: B3Client):
        url = b3_client._build_portfolio_url("IBOV")
        responses.get(url, status=500)
        callback = MagicMock()
        result = b3_client.fetch_portfolio("IBOV", progress_callback=callback)
        assert result == []
        callback.assert_called_once_with("Falha ao baixar portfólio IBOV", True)

    @responses.activate
    def test_language_param_passed(self, b3_client: B3Client):
        raw = "PETR4;PETROBRAS;PN;100;10\n"
        b64 = base64.b64encode(raw.encode("latin-1")).decode()
        url = b3_client._build_portfolio_url("IBOV", language="en")
        responses.get(url, body=b64, status=200)
        result = b3_client.fetch_portfolio("IBOV", language="en")
        assert result == ["PETR4"]


class TestBuildPortfolioUrl:
    def test_url_contem_base64_do_payload(self, tmp_path):
        client = B3Client(cache=CacheManager(cache_dir=tmp_path))
        url = client._build_portfolio_url("IBOV")
        assert url.startswith(_PORTFOLIO_BASE)
        b64_part = url[len(_PORTFOLIO_BASE):]
        decoded = base64.b64decode(b64_part).decode()
        payload = json.loads(decoded)
        assert payload == {"index": "IBOV", "language": "pt-br"}

    def test_url_compact_separators(self, tmp_path):
        client = B3Client(cache=CacheManager(cache_dir=tmp_path))
        url = client._build_portfolio_url("IBOV")
        b64_part = url[len(_PORTFOLIO_BASE):]
        decoded = base64.b64decode(b64_part).decode()
        assert "{" in decoded
        assert " " not in decoded
