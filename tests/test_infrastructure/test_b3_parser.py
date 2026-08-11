from datetime import date
from decimal import Decimal

import pytest

from flowscope.infrastructure.b3.parser import (
    ParseError,
    _parse_date,
    _parse_decimal,
    parse_csv,
    parse_index_csv,
)


class TestParseCSV:
    def test_parse_valid(self, sample_csv):
        trades = parse_csv(sample_csv)
        assert len(trades) == 3
        assert trades[0].ticker.value == "PETR4"
        assert trades[0].avg_price.value == Decimal("28.80")
        assert trades[0].fin_vol == Decimal(432000)
        assert trades[0].trades_qty.value == 15000

    def test_parse_valid_asserts_all_fields(self, sample_csv):
        trades = parse_csv(sample_csv)
        t = trades[0]
        assert t.date == date(2026, 6, 25)
        assert t.ticker.value == "PETR4"
        assert t.segment == "CASH"
        assert t.min_price.value == Decimal("28.50")
        assert t.max_price.value == Decimal("29.10")
        assert t.avg_price.value == Decimal("28.80")
        assert t.last_price.value == Decimal("28.90")
        assert t.trades_qty.value == 15000
        assert t.fin_vol == Decimal(432000)
        assert t.fin_instr_qty == 15000

    def test_parse_with_empty_fields(self, sample_csv_with_empty):
        trades = parse_csv(sample_csv_with_empty)
        assert len(trades) == 2

    def test_empty_string_raises(self):
        with pytest.raises(ParseError, match="sem cabeçalho"):
            parse_csv("")

    def test_empty_content_raises(self):
        with pytest.raises(ParseError):
            parse_csv(";;;\n")

    def test_continues_after_invalid_row(self):
        content = (
            "RptDt;TckrSymb;SgmtNm;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;NtlFinVol;FinInstrmQty\n"
            "invalid-date;PETR4;CASH;28,50;29,10;28,80;28,90;15000;432000;15000\n"
            "2026-06-25;PETR4;CASH;28,50;29,10;28,80;28,90;15000;432000;15000\n"
        )
        trades = parse_csv(content)
        assert len(trades) == 1
        assert trades[0].ticker.value == "PETR4"


class TestParseCSVSegmentFilter:
    def test_default_filters_non_cash(self, sample_csv_mixed_segments):
        trades = parse_csv(sample_csv_mixed_segments)
        tickers = [t.ticker.value for t in trades]
        assert "PETR4" in tickers
        assert "VALE3" in tickers
        assert "WINZ5" not in tickers
        assert "DOLZ5" not in tickers

    def test_no_segment_filter_returns_all(self, sample_csv_mixed_segments):
        trades = parse_csv(sample_csv_mixed_segments, segment_filter=None)
        assert len(trades) == 4

    def test_custom_segment_filter(self, sample_csv_mixed_segments):
        trades = parse_csv(sample_csv_mixed_segments, segment_filter="BMF")
        assert len(trades) == 1
        assert trades[0].ticker.value == "WINZ5"


class TestParseDate:
    def test_iso_format(self):
        assert _parse_date("2026-06-25", 2) == date(2026, 6, 25)

    def test_dd_mm_yyyy_format(self):
        assert _parse_date("25/06/2026", 2) == date(2026, 6, 25)

    def test_dd_mm_yy_format(self):
        assert _parse_date("25/06/26", 2) == date(25, 6, 26)

    def test_empty_raises(self):
        with pytest.raises(ParseError, match="Data vazia"):
            _parse_date("", 2)

    def test_invalid_format_raises(self):
        with pytest.raises(ParseError, match="Formato de data inválido"):
            _parse_date("20260625", 2)

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError):
            _parse_date("2026-13-45", 2)


class TestParseDecimal:
    def test_normal_with_comma(self):
        assert _parse_decimal("28,90", 2) == Decimal("28.90")

    def test_empty_returns_zero(self):
        assert _parse_decimal("", 2) == Decimal(0)

    def test_whitespace_returns_zero(self):
        assert _parse_decimal("   ", 2) == Decimal(0)


class TestParseIndex:
    def test_parse_index_csv_idiv(self, sample_idiv_csv):
        tickers = parse_index_csv(sample_idiv_csv)
        assert tickers == ["ABCB4", "ALOS3", "BBSE3", "PETR4"]

    def test_parse_index_csv_ibov(self, sample_ibov_csv):
        tickers = parse_index_csv(sample_ibov_csv)
        assert tickers == ["VALE3", "PETR4", "ITUB4", "B3SA3"]

    def test_parse_index_csv_ifix(self, sample_ifix_csv):
        tickers = parse_index_csv(sample_ifix_csv)
        assert tickers == ["KINP11", "HGLG11", "KNRI11"]

    def test_parse_index_csv_ignores_footer(self, sample_idiv_csv):
        tickers = parse_index_csv(sample_idiv_csv)
        assert "Quantidade" not in tickers
        assert "Redutor" not in tickers
        assert "Quantidade Teórica Total" not in tickers

    def test_parse_index_csv_ignores_ibov_footer(self, sample_ibov_csv):
        tickers = parse_index_csv(sample_ibov_csv)
        assert "Quantidade" not in tickers
        assert "Redutor" not in tickers

    def test_parse_index_csv_empty(self):
        assert parse_index_csv("") == []

    def test_continues_after_blank_line(self):
        content = "PETR4;X\n\nVALE3;Y\n"
        assert parse_index_csv(content) == ["PETR4", "VALE3"]

    def test_continues_after_empty_ticker_line(self):
        content = ";X\nPETR4;Y\n"
        assert parse_index_csv(content) == ["PETR4"]

    def test_continues_after_footer(self):
        content = "PETR4;X\nRedutor;;;0,99999999;\nVALE3;Y\n"
        assert parse_index_csv(content) == ["PETR4", "VALE3"]

    def test_skips_non_uppercase_ticker(self):
        content = "abc4;X\nPETR4;Y\n"
        assert parse_index_csv(content) == ["PETR4"]
