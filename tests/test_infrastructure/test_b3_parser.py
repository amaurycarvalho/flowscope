from decimal import Decimal

import pytest

from flowscope.infrastructure.b3.parser import ParseError, parse_csv


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
