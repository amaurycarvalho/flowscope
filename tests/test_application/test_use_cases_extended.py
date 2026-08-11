from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from flowscope.application.use_cases import (
    AnalyzeTickersUseCase,
    ExportVWAPUseCase,
    _build_daily_data,
    _build_result,
    _collect_vwap_dates,
    _derive_tickers,
    _find_replacement_date,
    _format_vwap_rows,
    _resolve_sampling_dates,
)
from flowscope.domain.entities import TradeDay
from flowscope.domain.sampling import SamplingConfig
from flowscope.domain.value_objects import Price, Ticker, Volume


def _trade_on(d: date, ticker: str = "PETR4") -> TradeDay:
    return TradeDay(
        date=d,
        ticker=Ticker(ticker),
        segment="CASH",
        min_price=Price("28.50"),
        max_price=Price("29.10"),
        avg_price=Price("28.80"),
        last_price=Price("28.90"),
        trades_qty=Volume(15000),
        fin_vol=Decimal(432000),
        fin_instr_qty=15000,
    )


def _make_mock_repo(trades: list[TradeDay]):
    repo = MagicMock()
    repo.get_available_dates.return_value = [date(2026, 6, 25), date(2026, 6, 24)]
    repo.fetch_trades.return_value = trades
    return repo


_TRADES = [
    _trade_on(date(2026, 6, 25)),
    _trade_on(date(2026, 6, 24)),
    _trade_on(date(2026, 6, 25), ticker="VALE3"),
]


class TestAnalyzeExecuteArgs:
    def test_passes_args_to_repository(self):
        repo = _make_mock_repo(_TRADES)
        engine = MagicMock()
        engine.execute.return_value = {}
        uc = AnalyzeTickersUseCase(repo, engine=engine)
        config = SamplingConfig(period_days=60, method="fibonacci")
        callback = MagicMock()
        uc.execute(
            ref_date=date(2026, 6, 26),
            tickers=["PETR4"],
            progress_callback=callback,
            config=config,
        )
        repo.get_available_dates.assert_called_once_with(date(2026, 6, 26), config=config)
        repo.fetch_trades.assert_called_once()
        args, kwargs = repo.fetch_trades.call_args
        assert args[0] == [date(2026, 6, 25), date(2026, 6, 24)]
        assert args[1] == ["PETR4"]
        assert kwargs["progress_callback"] is callback
        assert kwargs["cache_only"] is True
        engine.execute.assert_called_once()

    def test_cache_only_true_for_period_60(self):
        repo = _make_mock_repo(_TRADES)
        engine = MagicMock()
        engine.execute.return_value = {}
        uc = AnalyzeTickersUseCase(repo, engine=engine)
        uc.execute(
            ref_date=date(2026, 6, 26),
            tickers=["PETR4"],
            config=SamplingConfig(period_days=60, method="fibonacci"),
        )
        assert repo.fetch_trades.call_args.kwargs["cache_only"] is True

    def test_cache_only_false_for_period_30(self):
        repo = _make_mock_repo(_TRADES)
        engine = MagicMock()
        engine.execute.return_value = {}
        uc = AnalyzeTickersUseCase(repo, engine=engine)
        uc.execute(
            ref_date=date(2026, 6, 26),
            tickers=["PETR4"],
            config=SamplingConfig(period_days=30, method="fibonacci"),
        )
        assert repo.fetch_trades.call_args.kwargs["cache_only"] is False

    def test_cache_only_true_for_period_31(self):
        repo = _make_mock_repo(_TRADES)
        engine = MagicMock()
        engine.execute.return_value = {}
        uc = AnalyzeTickersUseCase(repo, engine=engine)
        uc.execute(
            ref_date=date(2026, 6, 26),
            tickers=["PETR4"],
            config=SamplingConfig(period_days=31, method="fibonacci"),
        )
        assert repo.fetch_trades.call_args.kwargs["cache_only"] is True

    def test_cache_only_false_without_config(self):
        repo = _make_mock_repo(_TRADES)
        engine = MagicMock()
        engine.execute.return_value = {}
        uc = AnalyzeTickersUseCase(repo, engine=engine)
        uc.execute(ref_date=date(2026, 6, 26), tickers=["PETR4"])
        assert repo.fetch_trades.call_args.kwargs["cache_only"] is False

    def test_filters_to_requested_tickers(self):
        repo = _make_mock_repo(_TRADES)
        uc = AnalyzeTickersUseCase(repo)
        result = uc.execute(ref_date=date(2026, 6, 26), tickers=["PETR4"])
        assert "VALE3" not in result
        assert result["PETR4"]["daily_data"] != []

    def test_includes_sampling_dates(self):
        repo = _make_mock_repo(_TRADES)
        uc = AnalyzeTickersUseCase(repo)
        result = uc.execute(ref_date=date(2026, 6, 26), tickers=["PETR4"])
        assert result["_sampling_dates"] == [date(2026, 6, 25), date(2026, 6, 24)]

    def test_execute_passes_cache_only_to_resolution(self):
        repo = MagicMock()
        repo.get_available_dates.return_value = [date(2026, 6, 26)]

        def fake_fetch(dates, tickers, **kw):
            if dates == [date(2026, 6, 25)]:
                return [_trade_on(date(2026, 6, 25))]
            return []

        repo.fetch_trades.side_effect = fake_fetch
        engine = MagicMock()
        engine.execute.return_value = {}
        uc = AnalyzeTickersUseCase(repo, engine=engine)
        uc.execute(
            ref_date=date(2026, 6, 26),
            tickers=["PETR4"],
            config=SamplingConfig(period_days=60, method="fibonacci"),
        )
        assert repo.fetch_trades.call_args_list
        assert all(c.kwargs.get("cache_only") is True for c in repo.fetch_trades.call_args_list)


class TestDeriveTickers:
    def test_returns_top_tickers(self):
        engine = MagicMock()
        engine.execute.return_value = {"top_tickers": {"_all": ["PETR4", "VALE3"]}}
        assert _derive_tickers(engine, []) == ["PETR4", "VALE3"]

    def test_missing_top_tickers_returns_empty(self):
        engine = MagicMock()
        engine.execute.return_value = {}
        assert _derive_tickers(engine, []) == []


class TestFindReplacementDate:
    def test_prefers_nearest_backward(self):
        d = date(2026, 6, 25)
        repo = MagicMock()

        def fake(dates, tickers, **kw):
            if dates == [date(2026, 6, 24)]:
                return [_trade_on(date(2026, 6, 24))]
            return []

        repo.fetch_trades.side_effect = fake
        result, trades = _find_replacement_date(d, {d}, {"PETR4"}, repo, False, date(2026, 6, 30))
        assert result == date(2026, 6, 24)
        assert trades

    def test_checks_forward_when_backward_empty(self):
        d = date(2026, 6, 25)
        repo = MagicMock()

        def fake(dates, tickers, **kw):
            if dates == [date(2026, 6, 26)]:
                return [_trade_on(date(2026, 6, 26))]
            return []

        repo.fetch_trades.side_effect = fake
        result, _ = _find_replacement_date(d, {d}, {"PETR4"}, repo, False, date(2026, 6, 30))
        assert result == date(2026, 6, 26)

    def test_never_returns_after_ref_date(self):
        d = date(2026, 6, 25)
        repo = MagicMock()

        def fake(dates, tickers, **kw):
            if dates == [date(2026, 6, 27)]:
                return [_trade_on(date(2026, 6, 27))]
            return []

        repo.fetch_trades.side_effect = fake
        result, _ = _find_replacement_date(d, {d}, {"PETR4"}, repo, False, date(2026, 6, 26))
        assert result is None

    def test_finds_at_max_deviation(self):
        d = date(2026, 6, 25)
        repo = MagicMock()

        def fake(dates, tickers, **kw):
            if dates == [date(2026, 7, 3)]:
                return [_trade_on(date(2026, 7, 3))]
            return []

        repo.fetch_trades.side_effect = fake
        result, _ = _find_replacement_date(d, {d}, {"PETR4"}, repo, False, date(2026, 6, 30))
        assert result is None

    def test_skips_seen_dates(self):
        d = date(2026, 6, 25)
        seen = {d, date(2026, 6, 26)}
        repo = MagicMock()

        def fake(dates, tickers, **kw):
            if dates == [date(2026, 6, 26)]:
                return [_trade_on(date(2026, 6, 26))]
            return []

        repo.fetch_trades.side_effect = fake
        result, _ = _find_replacement_date(d, seen, {"PETR4"}, repo, False, date(2026, 6, 30))
        assert result is None

    def test_skips_weekend_candidates(self):
        d = date(2026, 6, 24)
        repo = MagicMock()

        def fake(dates, tickers, **kw):
            if dates == [date(2026, 6, 27)]:
                return [_trade_on(date(2026, 6, 27))]
            return []

        repo.fetch_trades.side_effect = fake
        result, _ = _find_replacement_date(d, {d}, {"PETR4"}, repo, False, date(2026, 6, 30))
        assert result is None

    def test_continues_after_weekend_skipped(self):
        d = date(2026, 6, 28)
        repo = MagicMock()

        def fake(dates, tickers, **kw):
            if dates == [date(2026, 6, 29)]:
                return [_trade_on(date(2026, 6, 29))]
            return []

        repo.fetch_trades.side_effect = fake
        result, _ = _find_replacement_date(d, {d}, {"PETR4"}, repo, False, date(2026, 6, 30))
        assert result == date(2026, 6, 29)

    def test_fetch_args(self):
        d = date(2026, 6, 25)
        repo = MagicMock()
        repo.fetch_trades.return_value = [_trade_on(date(2026, 6, 24))]
        _find_replacement_date(d, {d}, {"PETR4", "VALE3"}, repo, cache_only=True, ref_date=date(2026, 6, 30))
        repo.fetch_trades.assert_called_once()
        args, kwargs = repo.fetch_trades.call_args
        assert args[0] == [date(2026, 6, 24)]
        assert sorted(args[1]) == ["PETR4", "VALE3"]
        assert kwargs["progress_callback"] is None
        assert kwargs["cache_only"] is True


class TestResolveSamplingDates:
    def test_keeps_dates_with_trades(self):
        dates = [date(2026, 6, 25)]
        filtered = [_trade_on(date(2026, 6, 25))]
        repo = MagicMock()
        sampling, _ = _resolve_sampling_dates(dates, filtered, {"PETR4"}, repo, False, date(2026, 6, 30))
        assert sampling == dates
        repo.fetch_trades.assert_not_called()

    def test_replaces_date_without_trades(self):
        dates = [date(2026, 6, 26), date(2026, 6, 24)]
        filtered = [_trade_on(date(2026, 6, 24))]
        repo = MagicMock()

        def fake(dates, tickers, **kw):
            if dates == [date(2026, 6, 25)]:
                return [_trade_on(date(2026, 6, 25))]
            return []

        repo.fetch_trades.side_effect = fake
        sampling, _ = _resolve_sampling_dates(dates, filtered, {"PETR4"}, repo, False, date(2026, 6, 30))
        assert sampling[0] == date(2026, 6, 25)
        assert repo.fetch_trades.call_args.kwargs["cache_only"] is False

    def test_does_not_reach_beyond_ref_date(self):
        dates = [date(2026, 6, 26)]
        filtered = []
        repo = MagicMock()

        def fake(dates, tickers, **kw):
            if dates == [date(2026, 6, 27)]:
                return [_trade_on(date(2026, 6, 27))]
            return []

        repo.fetch_trades.side_effect = fake
        sampling, _ = _resolve_sampling_dates(dates, filtered, {"PETR4"}, repo, False, date(2026, 6, 26))
        assert sampling[0] == date(2026, 6, 26)


class TestBuildDailyData:
    def test_builds_entries_with_all_fields(self):
        data = _build_daily_data(_TRADES)
        entry = data["PETR4"][0]
        assert entry == {
            "date": date(2026, 6, 25),
            "avg_price": Decimal("28.80"),
            "min_price": Decimal("28.50"),
            "max_price": Decimal("29.10"),
            "last_price": Decimal("28.90"),
            "fin_vol": Decimal(432000),
            "fin_instr_qty": 15000,
            "segment": "CASH",
            "trades_qty": 15000,
        }

    def test_empty(self):
        assert _build_daily_data([]) == {}


class TestBuildResult:
    def test_structure(self):
        tickers = ["PETR4"]
        results = {
            "vwap": {"PETR4": {"period_vwap": Decimal("28.7")}},
            "top_tickers": {"_all": ["PETR4"]},
            "clv": {"PETR4": Decimal("0.5")},
        }
        daily_data = {"PETR4": [{"date": date(2026, 6, 25)}]}
        sampling = [date(2026, 6, 25)]
        result = _build_result(tickers, results, daily_data, sampling)
        assert result["_sampling_dates"] == sampling
        ticker_result = result["PETR4"]
        assert ticker_result["vwap"] == {"period_vwap": Decimal("28.7")}
        assert ticker_result["volume_profile"] == {}
        assert ticker_result["daily_data"] == [{"date": date(2026, 6, 25)}]
        assert ticker_result["money_flow_volume"] is None
        assert ticker_result["all_indicators"] == {"clv": Decimal("0.5")}
        assert "top_tickers" not in ticker_result["all_indicators"]
        assert "vwap" not in ticker_result["all_indicators"]
        assert "volume_profile" not in ticker_result["all_indicators"]


class TestVWAPFormatting:
    def test_collect_vwap_dates(self):
        vwap = {
            "A": {"daily_vwap": {date(2026, 6, 25): 1, date(2026, 6, 24): 2}},
            "B": {"daily_vwap": {date(2026, 6, 24): 3}},
        }
        assert _collect_vwap_dates(vwap) == [date(2026, 6, 24), date(2026, 6, 25)]

    def test_format_vwap_rows(self):
        vwap = {
            "PETR4": {
                "period_vwap": Decimal("28.7"),
                "daily_vwap": {
                    date(2026, 6, 24): Decimal("28.4"),
                    date(2026, 6, 25): Decimal("28.8"),
                },
            },
            "EMPTY": None,
        }
        all_dates = _collect_vwap_dates(vwap)
        lines = _format_vwap_rows(vwap, all_dates)
        assert lines[0] == "Ticker;VWAP_Periodo;2026-06-24;2026-06-25"
        assert "PETR4;28.7;28.4;28.8" in lines
        assert not any("EMPTY" in line for line in lines)


class TestExportVWAPExecute:
    def test_passes_args(self):
        repo = _make_mock_repo(_TRADES)
        engine = MagicMock()
        engine.execute.return_value = {"vwap": {}}
        uc = ExportVWAPUseCase(repo, engine=engine)
        uc.execute(ref_date=date(2026, 6, 26), tickers=["PETR4"])
        repo.get_available_dates.assert_called_once_with(date(2026, 6, 26))
        repo.fetch_trades.assert_called_once_with(
            [date(2026, 6, 25), date(2026, 6, 24)], ["PETR4"]
        )
