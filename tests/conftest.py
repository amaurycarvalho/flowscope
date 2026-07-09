import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
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

SAMPLE_IBOV_CSV = (
    "IBOV - Carteira do Dia 28/06/26\n"
    "Código;Ação;Tipo;Qtde. Teórica;Part. (%)\n"
    "VALE3;VALE;ON      NM;542.345.678;11,432;\n"
    "PETR4;PETROBRAS;PN      N2;398.765.432;9,876;\n"
    "ITUB4;ITAÚ UNIBANCO;PN      N1;287.654.321;7,654;\n"
    "B3SA3;B3;ON      NM;198.765.432;5,432;\n"
    "Quantidade Teórica Total;;;1.427.530.863;100,000\n"
    "Redutor;;;0,99999999;\n"
)

SAMPLE_IFIX_CSV = (
    "IFIX - Fundos Listados\n"
    "Código;Ação;Tipo;Qtde. Teórica;Part. (%)\n"
    "KINP11;KINEA;FII;12.345.678;2,345;\n"
    "HGLG11;HG LOGÍSTICA;FII;9.876.543;1,876;\n"
    "KNRI11;KINEA RENDA;FII;8.765.432;1,654;\n"
    "Quantidade Teórica Total;;;30.987.653;100,000\n"
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
def sample_ibov_csv() -> str:
    return SAMPLE_IBOV_CSV


@pytest.fixture
def sample_ifix_csv() -> str:
    return SAMPLE_IFIX_CSV


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
    client.fetch_portfolio.return_value = ["PETR4", "VALE3", "ITUB4"]
    return client


@pytest.fixture
def mock_repository(mock_b3_client):
    from flowscope.infrastructure.b3.repository import B3DataRepository
    repo = MagicMock(spec=B3DataRepository)
    repo._client = mock_b3_client
    repo.get_available_dates.return_value = [date(2026, 6, 25), date(2026, 6, 24)]
    repo.get_index_tickers.return_value = ["PETR4", "VALE3", "ITUB4"]
    return repo


@pytest.fixture
def sample_cached_portfolio(tmp_path: Path) -> Path:
    meta_path = tmp_path / "portfolio_IBOV.json"
    payload = {
        "cached_at": datetime.now().isoformat(),
        "tickers": ["PETR4", "VALE3"],
        "index": "IBOV",
    }
    meta_path.write_text(json.dumps(payload), encoding="utf-8")
    return tmp_path
