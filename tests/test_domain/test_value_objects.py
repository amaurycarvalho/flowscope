from decimal import Decimal

import pytest

from flowscope.domain.value_objects import Delta, Price, Ticker, Volume


class TestPrice:
    def test_from_decimal(self):
        p = Price(Decimal("28.50"))
        assert p.value == Decimal("28.50")

    def test_from_string(self):
        p = Price("28,50")
        assert p.value == Decimal("28.50")

    def test_from_int(self):
        p = Price(30)
        assert p.value == Decimal(30)

    def test_equality(self):
        assert Price("28.50") == Price("28.50")
        assert Price("28.50") != Price("30.00")

    def test_not_equal_to_non_price(self):
        assert (Price("28.50") == "28.50") is False

    def test_repr(self):
        assert repr(Price("28.50")) == "Price(28.50)"

    def test_hash_matches_value(self):
        assert hash(Price("28.50")) == hash(Price("28.50"))


class TestVolume:
    def test_positive(self):
        v = Volume(1000)
        assert v.value == 1000

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="negativo"):
            Volume(-1)

    def test_not_equal_to_non_volume(self):
        assert (Volume(1) == 1) is False

    def test_repr(self):
        assert repr(Volume(1000)) == "Volume(1000)"

    def test_hash_matches_value(self):
        assert hash(Volume(1000)) == hash(Volume(1000))


class TestDelta:
    def test_positive(self):
        d = Delta(1.5)
        assert d.value == 1.5

    def test_negative(self):
        d = Delta(-2.3)
        assert d.value == -2.3

    def test_not_equal_to_non_delta(self):
        assert (Delta(1.5) == 1.5) is False

    def test_repr(self):
        assert repr(Delta(1.5)) == "Delta(1.5)"

    def test_hash_matches_value(self):
        assert hash(Delta(1.5)) == hash(Delta(1.5))


class TestTicker:
    def test_valid(self):
        t = Ticker("PETR4")
        assert t.value == "PETR4"

    def test_uppercase(self):
        t = Ticker("petr4")
        assert t.value == "PETR4"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="vazio"):
            Ticker("")

    def test_not_equal_to_non_ticker(self):
        assert (Ticker("PETR4") == "PETR4") is False

    def test_repr(self):
        assert repr(Ticker("PETR4")) == "Ticker(PETR4)"

    def test_hash_matches_value(self):
        assert hash(Ticker("PETR4")) == hash(Ticker("PETR4"))
