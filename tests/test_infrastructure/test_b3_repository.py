from datetime import date
from unittest.mock import patch

import pytest

from flowscope.domain.sampling import SamplingConfig
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

    def test_fetch_file_called_with_expected_args(self, repo: B3DataRepository, sample_csv):
        repo._client.fetch_file.return_value = sample_csv
        repo.fetch_trades([date(2026, 6, 25)])
        repo._client.fetch_file.assert_called_once_with(
            date(2026, 6, 25), progress_callback=None, cache_only=False
        )

    def test_fetch_file_passes_cache_only(self, repo: B3DataRepository, sample_csv):
        repo._client.fetch_file.return_value = sample_csv
        repo.fetch_trades([date(2026, 6, 25)], cache_only=True)
        repo._client.fetch_file.assert_called_once_with(
            date(2026, 6, 25), progress_callback=None, cache_only=True
        )

    def test_fetch_file_passes_progress_callback(self, repo: B3DataRepository, sample_csv):
        repo._client.fetch_file.return_value = sample_csv
        cb = lambda msg, done: None
        repo.fetch_trades([date(2026, 6, 25)], progress_callback=cb)
        repo._client.fetch_file.assert_called_once_with(
            date(2026, 6, 25), progress_callback=cb, cache_only=False
        )

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

    def test_ignora_content_none_e_continua(self, repo: B3DataRepository, sample_csv):
        repo._client.fetch_file.side_effect = [None, sample_csv]
        dates = [date(2026, 6, 25), date(2026, 6, 24)]
        trades = repo.fetch_trades(dates)
        assert len(trades) == 3

    def test_progress_callback_recebe_erro_de_download(self, repo: B3DataRepository, sample_csv):
        repo._client.fetch_file.side_effect = [Exception("Timeout"), sample_csv]
        calls = []
        repo.fetch_trades(
            [date(2026, 6, 25), date(2026, 6, 24)],
            progress_callback=lambda msg, done: calls.append((msg, done)),
        )
        assert any("erro ao baixar" in msg for msg, _ in calls)

    def test_progress_callback_download_error_done_true(self, repo: B3DataRepository, sample_csv):
        repo._client.fetch_file.side_effect = [Exception("Timeout")]
        calls = []
        repo.fetch_trades(
            [date(2026, 6, 25)],
            progress_callback=lambda msg, done: calls.append((msg, done)),
        )
        assert calls[0] == (f"{date(2026, 6, 25)} (erro ao baixar)", True)

    def test_progress_callback_recebe_erro_de_parse(self, repo: B3DataRepository, sample_csv):
        repo._client.fetch_file.side_effect = ["invalid;;;\n", sample_csv]
        calls = []
        repo.fetch_trades(
            [date(2026, 6, 25), date(2026, 6, 24)],
            progress_callback=lambda msg, done: calls.append((msg, done)),
        )
        assert any("erro ao processar CSV" in msg for msg, _ in calls)

    def test_progress_callback_parse_error_done_true(self, repo: B3DataRepository, sample_csv):
        repo._client.fetch_file.side_effect = ["invalid;;;\n"]
        calls = []
        repo.fetch_trades(
            [date(2026, 6, 25)],
            progress_callback=lambda msg, done: calls.append((msg, done)),
        )
        assert calls[0] == (f"{date(2026, 6, 25)} (erro ao processar CSV)", True)


class TestGetAvailableDates:
    @pytest.mark.parametrize(
        "method",
        ["fibonacci", "fibonacci_reverse", "fibonacci_double", "monte_carlo", "monte_carlo_double"],
    )
    def test_sampling_method_uses_has_data(self, repo: B3DataRepository, method: str):
        config = SamplingConfig(period_days=60, method=method)
        with patch("flowscope.infrastructure.b3.repository.resolve_dates") as mock_resolve:
            mock_resolve.return_value = []
            repo.get_available_dates(date(2026, 6, 25), config)
        args, kwargs = mock_resolve.call_args
        assert args[1] is config
        assert kwargs["has_data"] == repo._has_data

    def test_fibonacci_30_dias_usa_fibonacci_dates(self, repo: B3DataRepository):
        config = SamplingConfig(period_days=30, method="fibonacci")
        with patch("flowscope.infrastructure.b3.repository.fibonacci_dates") as mock_fib:
            mock_fib.return_value = []
            repo.get_available_dates(date(2026, 6, 25), config)
        mock_fib.assert_called_once()
        assert mock_fib.call_args.kwargs["has_data"] == repo._has_data

    def test_period_30_nao_fibonacci_usa_resolve_dates(self, repo: B3DataRepository):
        config = SamplingConfig(period_days=30, method="monte_carlo")
        with patch("flowscope.infrastructure.b3.repository.resolve_dates") as mock_resolve:
            mock_resolve.return_value = []
            repo.get_available_dates(date(2026, 6, 25), config)
        mock_resolve.assert_called_once()

    def test_sem_config_usa_fibonacci_default(self, repo: B3DataRepository):
        dates = repo.get_available_dates(date(2026, 6, 25))
        assert isinstance(dates, list)
        assert all(isinstance(d, date) for d in dates)

    def test_config_fibonacci_30_dias(self, repo: B3DataRepository):
        dates = repo.get_available_dates(
            date(2026, 6, 25), SamplingConfig(period_days=30, method="fibonacci")
        )
        assert isinstance(dates, list)

    def test_config_method_nao_reconhecido(self, repo: B3DataRepository):
        dates = repo.get_available_dates(
            date(2026, 6, 25), SamplingConfig(period_days=15, method="custom")
        )
        assert isinstance(dates, list)

    def test_has_data_checks_cache_for_date(self, repo: B3DataRepository):
        repo._client._cache.get.return_value = "header\nrow1\nrow2"
        assert repo._has_data(date(2026, 6, 25)) is True
        repo._client._cache.get.assert_called_with(date(2026, 6, 25))

    def test_has_data_com_cache_vazio_retorna_false(self, repo: B3DataRepository):
        repo._client._cache.get.return_value = ""
        assert repo._has_data(date(2026, 6, 25)) is False

    def test_has_data_sem_cache_retorna_true(self, repo: B3DataRepository):
        repo._client._cache.get.return_value = None
        assert repo._has_data(date(2026, 6, 25)) is True

    def test_has_data_with_lines_returns_true(self, repo: B3DataRepository):
        repo._client._cache.get.return_value = "row1\nrow2\nrow3"
        assert repo._has_data(date(2026, 6, 25)) is True

    def test_has_data_with_header(self, repo: B3DataRepository):
        repo._client._cache.get.return_value = "RptDt;header\nrow1"
        assert repo._has_data(date(2026, 6, 25)) is True

    def test_has_data_requires_more_than_one_row(self, repo: B3DataRepository):
        repo._client._cache.get.return_value = "row1\nrow2"
        assert repo._has_data(date(2026, 6, 25)) is False

    def test_has_data_header_only_returns_false(self, repo: B3DataRepository):
        repo._client._cache.get.return_value = "RptDt;header"
        assert repo._has_data(date(2026, 6, 25)) is False


class TestGetIndexTickers:
    def test_passes_index(self, repo: B3DataRepository):
        repo._client.fetch_portfolio.return_value = ["PETR4"]
        repo.get_index_tickers("IBOV")
        repo._client.fetch_portfolio.assert_called_once_with("IBOV", progress_callback=None)

    def test_com_callback(self, repo: B3DataRepository):
        calls = []
        repo._client.fetch_portfolio.side_effect = (
            lambda index, language="pt-br", progress_callback=None: (
                progress_callback(f"Portfólio {index}", False),
                ["PETR4", "VALE3", "ITUB4"],
            )[1]
        )
        tickers = repo.get_index_tickers(
            "IBOV", progress_callback=lambda msg, done: calls.append((msg, done))
        )
        assert tickers == ["PETR4", "VALE3", "ITUB4"]
        assert calls
