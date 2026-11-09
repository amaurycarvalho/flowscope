import base64
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from flowscope.infrastructure.b3.client import B3Client
from flowscope.infrastructure.b3.parser import (
    INDEX_HISTORY_SCHEMA_VERSION,
    parse_index_history,
)
from flowscope.infrastructure.b3.repository import B3DataRepository
from flowscope.infrastructure.cache import CacheManager
from flowscope.domain.index_history import IndexClose
from tests.support_calendar import FakeBusinessDayLookup


class TestParseIndexHistory:
    def test_ano_completo(self):
        payload = {
            "results": [
                {"day": 2, "rateValue1": "125.432,10", "rateValue2": "126.000,00"},
                {"day": 3, "rateValue1": 127000.5, "rateValue2": None},
            ]
        }
        serie = parse_index_history(payload, 2026)
        assert serie == [
            IndexClose(date(2026, 1, 2), Decimal("125432.10")),
            IndexClose(date(2026, 1, 3), Decimal("127000.5")),
            IndexClose(date(2026, 2, 2), Decimal("126000.00")),
        ]

    def test_mes_parcial_e_nulos(self):
        payload = {"results": [{"day": 10, "rateValue1": 100, "rateValue2": None}]}
        serie = parse_index_history(payload, 2026)
        assert [c.date for c in serie] == [date(2026, 1, 10)]

    def test_valor_invalido_ignorado(self):
        payload = {
            "results": [
                {"day": 5, "rateValue1": "abc", "rateValue2": "10,5"},
                {"day": "x", "rateValue1": 1},
            ]
        }
        serie = parse_index_history(payload, 2026)
        assert serie == [IndexClose(date(2026, 2, 5), Decimal("10.5"))]

    @pytest.mark.parametrize("payload", [{}, {"results": []}, {"results": "x"}, None, "not json"])
    def test_resposta_vazia_ou_malformada(self, payload):
        assert parse_index_history(payload, 2026) == []


class TestFetchIndexDailyHistory:
    @patch("requests.get")
    def test_monta_url_e_payload(self, mock_get):
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.text = json.dumps({"results": []})
        mock_get.return_value.json.return_value = {"results": [
            {"day": 2, "rateValue1": "100,00"}
        ]}
        client = B3Client(cache=CacheManager(), business_day=FakeBusinessDayLookup([]))
        serie = client.fetch_index_daily_history("IBOV", 2026)
        assert serie == [IndexClose(date(2026, 1, 2), Decimal("100.00"))]
        url = mock_get.call_args[0][0]
        token = url.removeprefix(B3Client._BASE_INDEX_HISTORY_URL)
        assert json.loads(base64.b64decode(token)) == {
            "index": "IBOV", "language": "pt-br", "year": "2026",
        }

    @patch("requests.get")
    def test_resposta_vazia_vira_ausencia(self, mock_get, caplog):
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.text = ""
        client = B3Client(cache=CacheManager(), business_day=FakeBusinessDayLookup([]))
        assert client.fetch_index_daily_history("XXXX", 2026) == []
        assert "resposta vazia" in caplog.text

    @patch("requests.get")
    def test_json_invalido_vira_ausencia(self, mock_get):
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.text = "raw"
        mock_get.return_value.json.side_effect = ValueError("bad")
        client = B3Client(cache=CacheManager(), business_day=FakeBusinessDayLookup([]))
        assert client.fetch_index_daily_history("IBOV", 2026) == []


class FakeClient:
    def __init__(self, cache, series):
        self._cache = cache
        self._series = series
        self.calls = []

    def fetch_index_daily_history(self, index, year):
        self.calls.append((index, year))
        return list(self._series.get((index, year), []))


def _repo(tmp_path, series):
    cache = CacheManager(cache_dir=tmp_path)
    client = FakeClient(cache, series)
    return B3DataRepository(client=client), client


class TestIndexHistoryRepository:
    def test_filtra_intervalo_e_reusa_cache(self, tmp_path):
        serie = [
            IndexClose(date(2025, 12, 31), Decimal("1")),
            IndexClose(date(2026, 1, 2), Decimal("2")),
            IndexClose(date(2026, 2, 2), Decimal("3")),
        ]
        repo, client = _repo(tmp_path, {("IBOV", 2025): serie[:1], ("IBOV", 2026): serie[1:]})
        resultado = repo.get_index_history("IBOV", date(2025, 12, 30), date(2026, 1, 31))
        assert resultado == [
            IndexClose(date(2025, 12, 31), Decimal("1")),
            IndexClose(date(2026, 1, 2), Decimal("2")),
        ]
        assert client.calls == [("IBOV", 2025), ("IBOV", 2026)]
        repo.get_index_history("IBOV", date(2025, 12, 30), date(2026, 1, 31))
        assert len(client.calls) == 2

    def test_ano_corrente_expira_em_um_dia(self, tmp_path):
        ano = date.today().year
        repo, client = _repo(tmp_path, {("IBOV", ano): []})
        repo.get_index_history("IBOV", date(ano, 1, 1), date(ano, 1, 2))
        meta = tmp_path / f"index_history_IBOV_{ano}.json"
        dados = json.loads(meta.read_text(encoding="utf-8"))
        dados["cached_at"] = (
            datetime.now(timezone.utc) - timedelta(days=2)
        ).isoformat()
        meta.write_text(json.dumps(dados), encoding="utf-8")
        repo.get_index_history("IBOV", date(ano, 1, 1), date(ano, 1, 2))
        assert len(client.calls) == 2

    def test_ano_anterior_imutavel(self, tmp_path):
        repo, client = _repo(tmp_path, {("IBOV", 2024): []})
        repo.get_index_history("IBOV", date(2024, 1, 1), date(2024, 1, 2))
        meta = tmp_path / "index_history_IBOV_2024.json"
        dados = json.loads(meta.read_text(encoding="utf-8"))
        dados["cached_at"] = (
            datetime.now(timezone.utc) - timedelta(days=400)
        ).isoformat()
        meta.write_text(json.dumps(dados), encoding="utf-8")
        repo.get_index_history("IBOV", date(2024, 1, 1), date(2024, 1, 2))
        assert len(client.calls) == 1

    def test_versao_de_schema_invalida(self, tmp_path):
        repo, client = _repo(tmp_path, {("IBOV", 2024): []})
        meta = tmp_path / "index_history_IBOV_2024.json"
        meta.write_text(json.dumps({
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": INDEX_HISTORY_SCHEMA_VERSION + 1,
            "values": [],
        }), encoding="utf-8")
        repo.get_index_history("IBOV", date(2024, 1, 1), date(2024, 1, 2))
        assert client.calls == [("IBOV", 2024)]
