from datetime import date
from unittest.mock import MagicMock

import pytest

from flowscope.infrastructure.b3.repository import B3DataRepository


@pytest.fixture
def repo(mock_b3_client):
    return B3DataRepository(client=mock_b3_client)


class TestFetchTrades:
    def test_multiplas_datas_processa_ambas(self, repo: B3DataRepository, sample_csv):
        repo._client.fetch_file.side_effect = [sample_csv, sample_csv]
        dates = [date(2026, 6, 25), date(2026, 6, 24)]
        trades = repo.fetch_trades(dates)
        assert len(trades) == 6

    def test_ignora_parse_error_e_continua(self, repo: B3DataRepository, sample_csv, sample_csv_with_empty):
        repo._client.fetch_file.side_effect = ["invalid;;;\n", sample_csv]
        dates = [date(2026, 6, 25), date(2026, 6, 24)]
        trades = repo.fetch_trades(dates)
        assert len(trades) == 3

    def test_ignora_download_error_e_continua(self, repo: B3DataRepository, sample_csv):
        repo._client.fetch_file.side_effect = [Exception("Timeout"), sample_csv]
        dates = [date(2026, 6, 25), date(2026, 6, 24)]
        trades = repo.fetch_trades(dates)
        assert len(trades) == 3

    def test_filtro_tickers(self, repo: B3DataRepository, sample_csv):
        repo._client.fetch_file.return_value = sample_csv
        dates = [date(2026, 6, 25)]
        trades = repo.fetch_trades(dates, tickers=["PETR4"])
        assert len(trades) == 1
        assert trades[0].ticker.value == "PETR4"
