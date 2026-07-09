from datetime import date
from decimal import Decimal

import pytest

from flowscope.domain.engine import IndicatorEngine
from flowscope.domain.strategies import (
    RangeStrategy,
    TypicalPriceStrategy,
    MedianPriceStrategy,
    WeightedCloseStrategy,
    CLVStrategy,
    MoneyFlowMultiplierStrategy,
    BuyingPressureStrategy,
    SellingPressureStrategy,
    MoneyFlowVolumeStrategy,
    AverageTradeSizeStrategy,
    AverageFinancialTicketStrategy,
    RangePercentualStrategy,
    DailyEfficiencyStrategy,
    FinancialDensityStrategy,
    TradeDensityStrategy,
    VolumeDensityStrategy,
    VWAPStrategy,
    VolumeProfileStrategy,
    TopTickersStrategy,
)
from flowscope.domain.entities import TradeDay
from flowscope.domain.value_objects import Price, Ticker, Volume


class TestIndicatorEngine:
    def test_execute_empty_registry(self):
        engine = IndicatorEngine()
        assert engine.execute([]) == {}

    def test_simple_dag_resolution(self):
        engine = IndicatorEngine()
        engine.register(RangeStrategy())
        result = engine.execute([])
        assert "range" in result

    def test_dependency_order(self):
        engine = IndicatorEngine()
        engine.register(BuyingPressureStrategy(), RangeStrategy())
        result = engine.execute([])
        assert "range" in result
        assert "buying_pressure" in result

    def test_circular_dependency(self):
        from flowscope.domain.strategies.base import IndicatorStrategy
        from typing import ClassVar

        class A(IndicatorStrategy):
            id = "a"
            dependencies: ClassVar[list[str]] = ["b"]
            def compute(self, trades, dep_results): return {}

        class B(IndicatorStrategy):
            id = "b"
            dependencies: ClassVar[list[str]] = ["a"]
            def compute(self, trades, dep_results): return {}

        engine = IndicatorEngine()
        engine.register(A(), B())
        with pytest.raises(ValueError, match="Circular dependency"):
            engine.execute([])

    def test_cache_reuse(self, mock_trades):
        engine = IndicatorEngine()
        engine.register(
            RangeStrategy(),
            BuyingPressureStrategy(),
            SellingPressureStrategy(),
        )
        result = engine.execute(mock_trades)
        assert "range" in result
        assert "buying_pressure" in result
        assert "selling_pressure" in result
        for ticker in ("PETR4", "VALE3"):
            assert ticker in result["range"]
            assert ticker in result["buying_pressure"]
            assert ticker in result["selling_pressure"]

    def test_unknown_dependency(self):
        from flowscope.domain.strategies.base import IndicatorStrategy
        from typing import ClassVar

        class Bad(IndicatorStrategy):
            id = "bad"
            dependencies: ClassVar[list[str]] = ["nonexistent"]
            def compute(self, trades, dep_results): return {}

        engine = IndicatorEngine()
        engine.register(Bad())
        with pytest.raises(ValueError, match="depends on unknown"):
            engine.execute([])


class TestRangeStrategy:
    def test_positive(self, mock_trades):
        s = RangeStrategy()
        result = s.compute(mock_trades, {})
        petr4_d1 = result["PETR4"][date(2026, 6, 25)]
        assert petr4_d1 == Decimal("29.10") - Decimal("28.50")

    def test_zero(self):
        s = RangeStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("10"),
            avg_price=Price("10"), last_price=Price("10"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        result = s.compute([trade], {})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("0")


class TestCLVStrategy:
    def test_at_high(self):
        s = CLVStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("70"), max_price=Price("80"),
            avg_price=Price("75"), last_price=Price("80"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        result = s.compute([trade], {})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("1")

    def test_at_low(self):
        s = CLVStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("70"), max_price=Price("80"),
            avg_price=Price("75"), last_price=Price("70"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        result = s.compute([trade], {})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("-1")

    def test_at_center(self):
        s = CLVStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("70"), max_price=Price("80"),
            avg_price=Price("75"), last_price=Price("75"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        result = s.compute([trade], {})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("0")

    def test_range_zero(self):
        s = CLVStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("75"), max_price=Price("75"),
            avg_price=Price("75"), last_price=Price("75"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        result = s.compute([trade], {})
        assert result["TEST"][date(2026, 6, 25)] is None


class TestPriceIndicators:
    def test_typical_price(self):
        s = TypicalPriceStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("18"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        result = s.compute([trade], {})
        expected = (Decimal("20") + Decimal("10") + Decimal("18")) / Decimal("3")
        assert result["TEST"][date(2026, 6, 25)] == expected

    def test_median_price(self):
        s = MedianPriceStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("18"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        result = s.compute([trade], {})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("15")

    def test_weighted_close(self):
        s = WeightedCloseStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("18"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        result = s.compute([trade], {})
        expected = (Decimal("20") + Decimal("10") + Decimal("2") * Decimal("18")) / Decimal("4")
        assert result["TEST"][date(2026, 6, 25)] == expected


class TestMoneyFlowMultiplier:
    def test_delegates_to_clv(self):
        s = MoneyFlowMultiplierStrategy()
        clv_data = {"TEST": {date(2026, 6, 25): Decimal("0.5")}}
        result = s.compute([], {"clv": clv_data})
        assert result == clv_data


class TestBuyingSellingPressure:
    def test_complementary(self, mock_trades):
        bp = BuyingPressureStrategy()
        sp = SellingPressureStrategy()

        range_data = RangeStrategy().compute(mock_trades, {})
        dep_results = {"range": range_data}

        bp_result = bp.compute(mock_trades, dep_results)
        sp_result = sp.compute(mock_trades, dep_results)

        for ticker in ("PETR4", "VALE3"):
            for d in bp_result[ticker]:
                b = bp_result[ticker][d]
                s = sp_result[ticker][d]
                if b is not None and s is not None:
                    assert abs(float(b + s) - 1.0) < Decimal("1e-10")


class TestAverageTradeSize:
    def test_normal(self):
        s = AverageTradeSizeStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("18"),
            trades_qty=Volume(1000), fin_vol=Decimal("10000"),
            fin_instr_qty=50000,
        )
        result = s.compute([trade], {})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("50")

    def test_zero_trades(self):
        s = AverageTradeSizeStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("18"),
            trades_qty=Volume(0), fin_vol=Decimal("10000"),
            fin_instr_qty=50000,
        )
        result = s.compute([trade], {})
        assert result["TEST"][date(2026, 6, 25)] is None


class TestAverageFinancialTicket:
    def test_normal(self):
        s = AverageFinancialTicketStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("18"),
            trades_qty=Volume(1000), fin_vol=Decimal("100000"),
            fin_instr_qty=50000,
        )
        result = s.compute([trade], {})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("100")

    def test_zero_trades(self):
        s = AverageFinancialTicketStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("18"),
            trades_qty=Volume(0), fin_vol=Decimal("100000"),
            fin_instr_qty=50000,
        )
        result = s.compute([trade], {})
        assert result["TEST"][date(2026, 6, 25)] is None


class TestRangePercentual:
    def test_normal(self):
        s = RangePercentualStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("77.91"), max_price=Price("78.88"),
            avg_price=Price("78.15"), last_price=Price("78.15"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        range_data = {"TEST": {date(2026, 6, 25): Decimal("0.97")}}
        result = s.compute([trade], {"range": range_data})
        expected = Decimal("0.97") / Decimal("78.15")
        assert result["TEST"][date(2026, 6, 25)] == expected

    def test_avg_price_zero(self):
        s = RangePercentualStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("0"), last_price=Price("15"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        range_data = {"TEST": {date(2026, 6, 25): Decimal("10")}}
        result = s.compute([trade], {"range": range_data})
        assert result["TEST"][date(2026, 6, 25)] is None


class TestDailyEfficiency:
    def test_normal(self):
        s = DailyEfficiencyStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("18"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        range_data = {"TEST": {date(2026, 6, 25): Decimal("10")}}
        result = s.compute([trade], {"range": range_data})
        expected = abs(Decimal("18") - Decimal("15")) / Decimal("10")
        assert result["TEST"][date(2026, 6, 25)] == expected

    def test_range_zero(self):
        s = DailyEfficiencyStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("10"),
            avg_price=Price("10"), last_price=Price("10"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )
        range_data = {"TEST": {date(2026, 6, 25): Decimal("0")}}
        result = s.compute([trade], {"range": range_data})
        assert result["TEST"][date(2026, 6, 25)] is None


class TestMoneyFlowVolume:
    def test_accumulated(self):
        s = MoneyFlowVolumeStrategy()
        mfm_data = {
            "TEST": {
                date(2026, 6, 24): Decimal("0.5"),
                date(2026, 6, 25): Decimal("-0.3"),
            }
        }
        trades = [
            TradeDay(
                date=date(2026, 6, 24), ticker=Ticker("TEST"),
                segment="CASH", min_price=Price("10"), max_price=Price("20"),
                avg_price=Price("15"), last_price=Price("15"),
                trades_qty=Volume(100), fin_vol=Decimal("1000"),
                fin_instr_qty=100,
            ),
            TradeDay(
                date=date(2026, 6, 25), ticker=Ticker("TEST"),
                segment="CASH", min_price=Price("10"), max_price=Price("20"),
                avg_price=Price("15"), last_price=Price("15"),
                trades_qty=Volume(100), fin_vol=Decimal("2000"),
                fin_instr_qty=100,
            ),
        ]
        result = s.compute(trades, {"money_flow_multiplier": mfm_data})
        expected = Decimal("0.5") * Decimal("1000") + Decimal("-0.3") * Decimal("2000")
        assert result["TEST"] == expected


class TestDensityIndicators:
    def test_financial(self):
        s = FinancialDensityStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("15"),
            trades_qty=Volume(100), fin_vol=Decimal("10000"),
            fin_instr_qty=100,
        )
        range_data = {"TEST": {date(2026, 6, 25): Decimal("10")}}
        result = s.compute([trade], {"range": range_data})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("1000")

    def test_trade(self):
        s = TradeDensityStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("15"),
            trades_qty=Volume(500), fin_vol=Decimal("10000"),
            fin_instr_qty=100,
        )
        range_data = {"TEST": {date(2026, 6, 25): Decimal("10")}}
        result = s.compute([trade], {"range": range_data})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("50")

    def test_volume(self):
        s = VolumeDensityStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("15"),
            trades_qty=Volume(100), fin_vol=Decimal("10000"),
            fin_instr_qty=2000,
        )
        range_data = {"TEST": {date(2026, 6, 25): Decimal("10")}}
        result = s.compute([trade], {"range": range_data})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("200")

    def test_range_zero(self):
        s = FinancialDensityStrategy()
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("10"),
            avg_price=Price("10"), last_price=Price("10"),
            trades_qty=Volume(100), fin_vol=Decimal("10000"),
            fin_instr_qty=100,
        )
        range_data = {"TEST": {date(2026, 6, 25): Decimal("0")}}
        result = s.compute([trade], {"range": range_data})
        assert result["TEST"][date(2026, 6, 25)] is None


class TestVWAPStrategy:
    def test_single_ticker(self, mock_trades):
        s = VWAPStrategy()
        petr4_trades = [t for t in mock_trades if t.ticker.value == "PETR4"]
        result = s.compute(petr4_trades, {})
        assert "PETR4" in result
        vwap_val = result["PETR4"]["period_vwap"]
        total_price_qty = (
            Decimal("28.80") * Decimal("15000")
            + Decimal("28.40") * Decimal("12000")
        )
        total_qty = Decimal("15000") + Decimal("12000")
        expected = total_price_qty / total_qty
        assert vwap_val == expected
        assert result["PETR4"]["total_fin_instr_qty"] == 27000

    def test_multi_ticker(self, mock_trades):
        s = VWAPStrategy()
        result = s.compute(mock_trades, {})
        assert "PETR4" in result
        assert "VALE3" in result

    def test_empty(self):
        s = VWAPStrategy()
        assert s.compute([], {}) == {}


class TestVolumeProfileStrategy:
    def test_single_ticker(self, mock_trades):
        s = VolumeProfileStrategy(0.01)
        trades = [t for t in mock_trades if t.ticker.value == "PETR4"]
        result = s.compute(trades, {})
        assert "PETR4" in result
        profile = result["PETR4"]
        assert len(profile) > 0
        total_distributed = sum(profile.values(), Decimal("0"))
        total_fin_vol = Decimal("432000") + Decimal("340800")
        assert total_distributed == total_fin_vol

    def test_empty(self):
        s = VolumeProfileStrategy(0.01)
        assert s.compute([], {}) == {}


class TestTopTickersStrategy:
    def test_top_n(self, mock_trades):
        s = TopTickersStrategy(n=1)
        result = s.compute(mock_trades, {})
        assert len(result["_all"]) == 1

    def test_all_when_less_than_n(self, mock_trades):
        s = TopTickersStrategy(n=10)
        result = s.compute(mock_trades, {})
        assert len(result["_all"]) == 2
