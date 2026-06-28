from decimal import Decimal

import pytest

from flowscope.infrastructure.b3.parser import ParseError, parse_csv, parse_index_csv


class TestParseCSV:
    def test_parse_valid(self, sample_csv):
        trades = parse_csv(sample_csv)
        assert len(trades) == 3
        assert trades[0].ticker.value == "PETR4"
        assert trades[0].avg_price.value == Decimal("28.80")
        assert trades[0].fin_vol == Decimal("432000")
        assert trades[0].trades_qty.value == 15000

    def test_parse_with_empty_fields(self, sample_csv_with_empty):
        trades = parse_csv(sample_csv_with_empty)
        assert len(trades) == 2

    def test_empty_string_raises(self):
        with pytest.raises(ParseError, match="sem cabeçalho"):
            parse_csv("")

    def test_empty_content_raises(self):
        with pytest.raises(ParseError):
            parse_csv(";;;\n")


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
