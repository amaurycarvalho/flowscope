from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from flowscope.domain.entities import TradeDay
from flowscope.domain.value_objects import Price, Ticker, Volume

SAMPLE_CSV = (
    "RptDt;TckrSymb;SgmtNm;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;NtlFinVol;FinInstrmQty\n"
    "2026-06-25;PETR4;CASH;28,50;29,10;28,80;28,90;15000;432000;15000\n"
    "2026-06-25;VALE3;CASH;62,10;63,50;62,80;62,50;8000;502400;8000\n"
    "2026-06-25;ITUB4;CASH;32,00;32,80;32,40;32,60;12000;388800;12000\n"
)

SAMPLE_CSV_WITH_EMPTY = (
    "RptDt;TckrSymb;SgmtNm;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;NtlFinVol;FinInstrmQty\n"
    "2026-06-25;PETR4;CASH;28,50;29,10;28,80;28,90;15000;432000;15000\n"
    "2026-06-25;;CASH;;;28,80;;;;\n"
    "2026-06-25;VALE3;CASH;62,10;63,50;62,80;62,50;8000;502400;8000\n"
)


@pytest.fixture
def sample_csv() -> str:
    return SAMPLE_CSV


@pytest.fixture
def sample_csv_with_empty() -> str:
    return SAMPLE_CSV_WITH_EMPTY


@pytest.fixture
def mock_trades() -> list[TradeDay]:
    return [
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
        TradeDay(
            date=date(2026, 6, 24),
            ticker=Ticker("VALE3"),
            segment="CASH",
            min_price=Price("61.50"),
            max_price=Price("62.90"),
            avg_price=Price("62.20"),
            last_price=Price("62.80"),
            trades_qty=Volume(10000),
            fin_vol=Decimal("622000"),
            fin_instr_qty=10000,
        ),
    ]


@pytest.fixture
def mock_b3_client():
    client = MagicMock()
    client.fetch_file.return_value = SAMPLE_CSV
    return client
