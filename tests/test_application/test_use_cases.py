from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from flowscope.application.use_cases import AnalyzeTickersUseCase, ExportVWAPUseCase
from flowscope.domain.entities import TradeDay
from flowscope.domain.value_objects import Price, Ticker, Volume


def _make_mock_repo(trades: list[TradeDay]):
    repo = MagicMock()
    repo.get_available_dates.return_value = [
        date(2026, 6, 25),
        date(2026, 6, 24),
    ]
    repo.fetch_trades.return_value = trades
    return repo


_TRADES = [
    TradeDay(
        date=date(2026, 6, 25),
        ticker=Ticker("PETR4"),
        segment="CASH",
        min_price=Price("28.50"),
        max_price=Price("29.10"),
        avg_price=Price("28.80"),
        last_price=Price("28.90"),
        trades_qty=Volume(15000),
        fin_vol=Decimal("432000"),
        fin_instr_qty=15000,
    ),
    TradeDay(
        date=date(2026, 6, 24),
        ticker=Ticker("PETR4"),
        segment="CASH",
        min_price=Price("28.00"),
        max_price=Price("28.80"),
        avg_price=Price("28.40"),
        last_price=Price("28.30"),
        trades_qty=Volume(12000),
        fin_vol=Decimal("340800"),
        fin_instr_qty=12000,
    ),
    TradeDay(
        date=date(2026, 6, 25),
        ticker=Ticker("VALE3"),
        segment="CASH",
        min_price=Price("62.10"),
        max_price=Price("63.50"),
        avg_price=Price("62.80"),
        last_price=Price("62.50"),
        trades_qty=Volume(8000),
        fin_vol=Decimal("502400"),
        fin_instr_qty=8000,
    ),
]


class TestExportVWAPUseCase:
    def test_export_all_tickers(self):
        repo = _make_mock_repo(_TRADES)
        use_case = ExportVWAPUseCase(repo)
        result = use_case.execute(ref_date=date(2026, 6, 26))
        assert "PETR4" in result
        assert "VALE3" in result

    def test_export_with_ticker_filter(self):
        repo = _make_mock_repo(_TRADES)
        use_case = ExportVWAPUseCase(repo)
        result = use_case.execute(
            ref_date=date(2026, 6, 26),
            ticker_filter=["PETR4"],
        )
        assert "PETR4" in result
        assert "VALE3" not in result

    def test_export_daily_columns(self):
        repo = _make_mock_repo(_TRADES)
        use_case = ExportVWAPUseCase(repo)
        csv = use_case.execute(ref_date=date(2026, 6, 26))
        lines = csv.split("\n")
        header = lines[0]
        assert "VWAP_Periodo" in header
        assert "2026-06-24" in header
        assert "2026-06-25" in header
        assert len(lines) >= 2


class TestAnalyzeTickersUseCase:
    def test_execute_com_tickers(self, mock_trades):
        repo = _make_mock_repo(mock_trades)
        uc = AnalyzeTickersUseCase(repo)
        result = uc.execute(ref_date=date(2026, 6, 26), tickers=["PETR4", "VALE3"])
        assert "PETR4" in result
        assert "VALE3" in result
        for ticker in ("PETR4", "VALE3"):
            assert "vwap" in result[ticker]
            assert "volume_profile" in result[ticker]
            assert "daily_data" in result[ticker]
            assert "money_flow_volume" in result[ticker]
            assert "all_indicators" in result[ticker]

    def test_execute_sem_tickers_usa_top_tickers(self, mock_trades):
        repo = _make_mock_repo(mock_trades)
        uc = AnalyzeTickersUseCase(repo)
        result = uc.execute(ref_date=date(2026, 6, 26))
        assert len(result) > 0

    def test_execute_com_progress_callback(self, mock_trades):
        repo = _make_mock_repo(mock_trades)
        callback = MagicMock()
        uc = AnalyzeTickersUseCase(repo)
        uc.execute(ref_date=date(2026, 6, 26), tickers=["PETR4"], progress_callback=callback)
        callback.assert_called()

    def test_execute_sem_trades_retorna_dict_com_tickers_mas_sem_dados(self):
        repo = _make_mock_repo([])
        uc = AnalyzeTickersUseCase(repo)
        result = uc.execute(ref_date=date(2026, 6, 26), tickers=["PETR4"])
        assert "PETR4" in result
        assert result["PETR4"]["daily_data"] == []
