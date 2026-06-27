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

SAMPLE_CSV_MIXED_SEGMENTS = (
    "RptDt;TckrSymb;SgmtNm;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;NtlFinVol;FinInstrmQty\n"
    "2026-06-25;PETR4;CASH;28,50;29,10;28,80;28,90;15000;432000;15000\n"
    "2026-06-25;WINZ5;BMF;100;101;100,50;100,50;5000;502500;5000\n"
    "2026-06-25;VALE3;CASH;62,10;63,50;62,80;62,50;8000;502400;8000\n"
    "2026-06-25;DOLZ5;FUTURE;5,20;5,30;5,25;5,25;10000;52500;10000\n"
)

SAMPLE_IDIV_CSV = (
    "IDIV - Carteira do Dia 29/06/26\n"
    "Código;Ação;Tipo;Qtde. Teórica;Part. (%)\n"
    "ABCB4;ABC BRASIL;PN      N2;94.194.244;0,443;\n"
    "ALOS3;ALLOS;ON      NM;590.258.296;3,091;\n"
    "BBSE3;BBSEGURIDADE;ON      NM;760.086.076;5,560;\n"
    "PETR4;PETROBRAS;PN      N2;634.203.386;4,508;\n"
    "Quantidade Teórica Total;;;25.884.437.336;100,000\n"
)


@pytest.fixture
def sample_csv() -> str:
    return SAMPLE_CSV


@pytest.fixture
def sample_csv_with_empty() -> str:
    return SAMPLE_CSV_WITH_EMPTY


@pytest.fixture
def sample_csv_mixed_segments() -> str:
    return SAMPLE_CSV_MIXED_SEGMENTS


@pytest.fixture
def sample_idiv_csv() -> str:
    return SAMPLE_IDIV_CSV


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
