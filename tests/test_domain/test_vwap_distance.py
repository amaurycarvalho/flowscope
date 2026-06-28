from datetime import date
from decimal import Decimal

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies import VWAPDistanceStrategy
from flowscope.domain.value_objects import Price, Ticker, Volume


class TestVWAPDistanceStrategy:
    def test_above_vwap(self):
        s = VWAPDistanceStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("49"), max_price=Price("51"),
            avg_price=Price("50"), last_price=Price("52"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        dep_results = {
            "vwap": {
                "TEST": {
                    "period_vwap": Decimal("50"),
                    "daily_vwap": {date(2026, 6, 25): Decimal("50")},
                    "total_fin_instr_qty": 100,
                }
            }
        }
        result = s.compute([trade], dep_results)
        assert result["TEST"][date(2026, 6, 25)] == Decimal("0.04")

    def test_below_vwap(self):
        s = VWAPDistanceStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("47"), max_price=Price("50"),
            avg_price=Price("48"), last_price=Price("46"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        dep_results = {
            "vwap": {
                "TEST": {
                    "period_vwap": Decimal("48"),
                    "daily_vwap": {date(2026, 6, 25): Decimal("48")},
                    "total_fin_instr_qty": 100,
                }
            }
        }
        result = s.compute([trade], dep_results)
        assert result["TEST"][date(2026, 6, 25)] == Decimal("-0.04166666666666666666666666667")

    def test_at_vwap(self):
        s = VWAPDistanceStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("49"), max_price=Price("51"),
            avg_price=Price("50"), last_price=Price("50"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        dep_results = {
            "vwap": {
                "TEST": {
                    "period_vwap": Decimal("50"),
                    "daily_vwap": {date(2026, 6, 25): Decimal("50")},
                    "total_fin_instr_qty": 100,
                }
            }
        }
        result = s.compute([trade], dep_results)
        assert result["TEST"][date(2026, 6, 25)] == Decimal("0")

    def test_no_vwap_data(self):
        s = VWAPDistanceStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("49"), max_price=Price("51"),
            avg_price=Price("50"), last_price=Price("52"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        result = s.compute([trade], {})
        assert result == {}

    def test_empty(self):
        s = VWAPDistanceStrategy()
        assert s.compute([], {}) == {}

    def test_dependency_id(self):
        assert VWAPDistanceStrategy.id == "vwap_distance"
        assert "vwap" in VWAPDistanceStrategy.dependencies
