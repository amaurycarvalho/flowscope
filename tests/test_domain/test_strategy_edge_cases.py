from datetime import date
from decimal import Decimal

from flowscope.domain.entities import TradeDay
from flowscope.domain.engine import IndicatorEngine
from flowscope.domain.indicators import default_engine
from flowscope.domain.strategies import (
    BuyingPressureStrategy,
    DailyEfficiencyStrategy,
    DailyMoneyFlowStrategy,
    DominanceScoreStrategy,
    FinancialDensityStrategy,
    MoneyFlowVolumeStrategy,
    RangePercentualStrategy,
    RangeStrategy,
    SellingPressureStrategy,
    TopTickersStrategy,
    TradeDensityStrategy,
    VWAPDistanceStrategy,
    VWAPStrategy,
    VolumeDensityStrategy,
    VolumeProfileStrategy,
)
from flowscope.domain.value_objects import Delta, Price, Ticker, Volume

D = date(2026, 6, 25)


def make_trade(
    ticker: str = "TEST",
    min_price: str = "10",
    max_price: str = "20",
    last_price: str = "15",
    avg_price: str = "15",
    qty: int = 100,
    fin_vol: str = "1000",
    fin_instr_qty: int = 100,
) -> TradeDay:
    return TradeDay(
        date=D,
        ticker=Ticker(ticker),
        segment="CASH",
        min_price=Price(min_price),
        max_price=Price(max_price),
        avg_price=Price(avg_price),
        last_price=Price(last_price),
        trades_qty=Volume(qty),
        fin_vol=Decimal(fin_vol),
        fin_instr_qty=fin_instr_qty,
    )


class TestVWAPStrategyEdgeCases:
    def test_skips_zero_qty(self):
        s = VWAPStrategy()
        result = s.compute([make_trade(fin_instr_qty=0)], {})
        assert "TEST" not in result

    def test_skips_negative_qty(self):
        s = VWAPStrategy()
        result = s.compute([make_trade(fin_instr_qty=-5)], {})
        assert "TEST" not in result

    def test_continues_after_zero_qty(self):
        s = VWAPStrategy()
        result = s.compute(
            [make_trade(ticker="A", fin_instr_qty=0), make_trade(ticker="B")],
            {},
        )
        assert "B" in result

    def test_daily_vwap_is_avg_price(self):
        s = VWAPStrategy()
        trade = make_trade(fin_instr_qty=100, avg_price="28.80")
        result = s.compute([trade], {})
        assert result["TEST"]["daily_vwap"][D] == Decimal("28.80")


class TestVolumeProfileStrategyEdgeCases:
    def test_default_tick_size(self):
        s = VolumeProfileStrategy()
        assert s._tick_size == 0.01

    def test_exact_buckets_with_remainder(self):
        s = VolumeProfileStrategy(0.01)
        trade = make_trade(min_price="10.00", max_price="10.02", fin_vol="100")
        result = s.compute([trade], {})
        assert result["TEST"] == {
            Decimal("10.00"): Decimal(33),
            Decimal("10.01"): Decimal(33),
            Decimal("10.02"): Decimal(34),
        }

    def test_exact_buckets_no_remainder(self):
        s = VolumeProfileStrategy(0.01)
        trade = make_trade(min_price="10.035", max_price="10.075", fin_vol="1000")
        result = s.compute([trade], {})
        assert result["TEST"] == {
            Decimal("10.03"): Decimal(200),
            Decimal("10.04"): Decimal(200),
            Decimal("10.05"): Decimal(200),
            Decimal("10.06"): Decimal(200),
            Decimal("10.07"): Decimal(200),
        }


class TestTopTickersStrategyEdgeCases:
    def test_default_n(self):
        s = TopTickersStrategy()
        assert s._n == 15

    def test_orders_by_fin_vol_desc(self):
        s = TopTickersStrategy(n=2)
        result = s.compute(
            [
                make_trade(ticker="ZETA", fin_vol="100"),
                make_trade(ticker="ALFA", fin_vol="9999"),
                make_trade(ticker="ZETA", fin_vol="100"),
            ],
            {},
        )
        assert result["_all"] == ["ALFA", "ZETA"]


class TestBuyingSellingPressureEdgeCases:
    def test_buying_missing_ticker_returns_none(self):
        s = BuyingPressureStrategy()
        result = s.compute([make_trade()], {"range": {}})
        assert result["TEST"][D] is None

    def test_selling_missing_ticker_returns_none(self):
        s = SellingPressureStrategy()
        result = s.compute([make_trade()], {"range": {}})
        assert result["TEST"][D] is None

    def test_buying_zero_range_returns_none(self):
        s = BuyingPressureStrategy()
        result = s.compute([make_trade()], {"range": {"TEST": {D: Decimal(0)}}})
        assert result["TEST"][D] is None

    def test_selling_zero_range_returns_none(self):
        s = SellingPressureStrategy()
        result = s.compute([make_trade()], {"range": {"TEST": {D: Decimal(0)}}})
        assert result["TEST"][D] is None

    def test_buying_unit_range_computes(self):
        s = BuyingPressureStrategy()
        trade = make_trade(min_price="10", last_price="11")
        result = s.compute([trade], {"range": {"TEST": {D: Decimal(1)}}})
        assert result["TEST"][D] == Decimal(1)

    def test_selling_unit_range_computes(self):
        s = SellingPressureStrategy()
        trade = make_trade(max_price="20", last_price="19")
        result = s.compute([trade], {"range": {"TEST": {D: Decimal(1)}}})
        assert result["TEST"][D] == Decimal(1)

    def test_buying_normal_computes(self):
        s = BuyingPressureStrategy()
        trade = make_trade(min_price="10", last_price="15")
        result = s.compute([trade], {"range": {"TEST": {D: Decimal(10)}}})
        assert result["TEST"][D] == Decimal("0.5")


class TestMoneyFlowVolumeEdgeCases:
    def test_missing_ticker_accumulates_nothing(self):
        s = MoneyFlowVolumeStrategy()
        mfm = {"TEST": {D: Decimal("0.5")}}
        result = s.compute([make_trade(ticker="OTHER")], {"money_flow_multiplier": mfm})
        assert "OTHER" not in result


class TestMissingTickerInDepData:
    def test_daily_money_flow(self):
        s = DailyMoneyFlowStrategy()
        result = s.compute([make_trade()], {"clv": {}})
        assert result["TEST"][D] is None

    def test_dominance_score(self):
        s = DominanceScoreStrategy()
        result = s.compute([make_trade()], {"clv": {}, "daily_efficiency": {}})
        assert result["TEST"][D] is None

    def test_daily_efficiency(self):
        s = DailyEfficiencyStrategy()
        result = s.compute([make_trade()], {"range": {}})
        assert result["TEST"][D] is None

    def test_financial_density(self):
        s = FinancialDensityStrategy()
        result = s.compute([make_trade()], {"range": {}})
        assert result["TEST"][D] is None

    def test_trade_density(self):
        s = TradeDensityStrategy()
        result = s.compute([make_trade()], {"range": {}})
        assert result["TEST"][D] is None

    def test_volume_density(self):
        s = VolumeDensityStrategy()
        result = s.compute([make_trade()], {"range": {}})
        assert result["TEST"][D] is None

    def test_range_percentual(self):
        s = RangePercentualStrategy()
        result = s.compute([make_trade()], {"range": {}})
        assert result["TEST"][D] is None


class TestRangeEdgeCases:
    def test_efficiency_range_one(self):
        s = DailyEfficiencyStrategy()
        trade = make_trade(last_price="18", avg_price="15")
        result = s.compute([trade], {"range": {"TEST": {D: Decimal(1)}}})
        assert result["TEST"][D] == Decimal(3)

    def test_range_percentual_range_one(self):
        s = RangePercentualStrategy()
        trade = make_trade(avg_price="20")
        result = s.compute([trade], {"range": {"TEST": {D: Decimal(1)}}})
        assert result["TEST"][D] == Decimal("0.05")


class TestVWAPDistanceEdgeCases:
    def test_missing_vwap_data_skips(self):
        s = VWAPDistanceStrategy()
        result = s.compute([make_trade()], {"vwap": {}})
        assert result == {}

    def test_missing_daily_vwap_skips(self):
        s = VWAPDistanceStrategy()
        vwap = {"TEST": {"period_vwap": Decimal(10), "daily_vwap": {}}}
        result = s.compute([make_trade()], {"vwap": vwap})
        assert result == {}

    def test_zero_daily_vwap_skips(self):
        s = VWAPDistanceStrategy()
        vwap = {"TEST": {"period_vwap": Decimal(10), "daily_vwap": {D: Decimal(0)}}}
        result = s.compute([make_trade()], {"vwap": vwap})
        assert result == {}

    def test_unit_daily_vwap_computes(self):
        s = VWAPDistanceStrategy()
        trade = make_trade(last_price="11")
        vwap = {"TEST": {"period_vwap": Decimal(10), "daily_vwap": {D: Decimal(1)}}}
        result = s.compute([trade], {"vwap": vwap})
        assert result["TEST"][D] == Decimal(10)

    def test_continues_after_missing_vwap_info(self):
        s = VWAPDistanceStrategy()
        vwap = {"ALFA": {"period_vwap": Decimal(10), "daily_vwap": {D: Decimal(10)}}}
        result = s.compute(
            [make_trade(ticker="MISSING"), make_trade(ticker="ALFA", last_price="12")],
            {"vwap": vwap},
        )
        assert result["ALFA"][D] == Decimal("0.2")

    def test_continues_after_zero_daily_vwap(self):
        s = VWAPDistanceStrategy()
        vwap = {
            "ZERO": {"period_vwap": Decimal(10), "daily_vwap": {D: Decimal(0)}},
            "ALFA": {"period_vwap": Decimal(10), "daily_vwap": {D: Decimal(10)}},
        }
        result = s.compute(
            [make_trade(ticker="ZERO"), make_trade(ticker="ALFA", last_price="12")],
            {"vwap": vwap},
        )
        assert result["ALFA"][D] == Decimal("0.2")

    def test_normal_computes(self):
        s = VWAPDistanceStrategy()
        trade = make_trade(last_price="12")
        vwap = {"TEST": {"period_vwap": Decimal(10), "daily_vwap": {D: Decimal(10)}}}
        result = s.compute([trade], {"vwap": vwap})
        assert result["TEST"][D] == Decimal("0.2")


class TestDefaultEngine:
    def test_registers_all_indicators(self):
        engine = default_engine()
        expected_ids = {
            "range",
            "typical_price",
            "median_price",
            "weighted_close",
            "clv",
            "money_flow_multiplier",
            "buying_pressure",
            "selling_pressure",
            "money_flow_volume",
            "average_trade_size",
            "average_financial_ticket",
            "range_percentual",
            "daily_efficiency",
            "daily_money_flow",
            "dominance_score",
            "financial_density",
            "trade_density",
            "volume_density",
            "vwap_distance",
            "vwap",
            "volume_profile",
            "top_tickers",
        }
        assert set(engine._registry.keys()) == expected_ids

    def test_passes_tick_size(self):
        engine = default_engine(tick_size=0.5)
        assert engine._registry["volume_profile"]._tick_size == 0.5

    def test_passes_top_n(self):
        engine = default_engine(top_n=7)
        assert engine._registry["top_tickers"]._n == 7


class TestEngineProgress:
    def test_progress_callback_receives_indicator_ids(self):
        engine = IndicatorEngine()
        engine.register(RangeStrategy(), BuyingPressureStrategy())
        calls = []
        engine.execute([make_trade()], progress_callback=lambda msg, done: calls.append((msg, done)))
        assert ("range", False) in calls
        assert ("buying_pressure", False) in calls


class TestResolveOrder:
    def test_multi_dependency_order(self):
        from flowscope.domain.strategies.base import IndicatorStrategy

        class DepA(IndicatorStrategy):
            id = "a"
            dependencies = []
            def compute(self, trades, dep_results):
                return {}

        class DepB(IndicatorStrategy):
            id = "b"
            dependencies = []
            def compute(self, trades, dep_results):
                return {}

        class Multi(IndicatorStrategy):
            id = "c"
            dependencies = ["a", "b"]
            def compute(self, trades, dep_results):
                return {}

        engine = IndicatorEngine()
        engine.register(DepA(), DepB(), Multi())
        order = engine._resolve_order()
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("c")


class TestValueObjects:
    def test_price_hash_matches_value(self):
        p = Price("28.90")
        assert hash(p) == hash(p.value)

    def test_price_equal_objects(self):
        assert Price("28.90") == Price("28.90")
        assert Price("28.90") != Price("28.91")

    def test_volume_hash_matches_value(self):
        v = Volume(15000)
        assert hash(v) == hash(v.value)

    def test_volume_equal_objects(self):
        assert Volume(15000) == Volume(15000)
        assert Volume(15000) != Volume(1)

    def test_delta_hash_matches_value(self):
        d = Delta(1.5)
        assert hash(d) == hash(d.value)

    def test_delta_equal_objects(self):
        assert Delta(1.5) == Delta(1.5)
        assert Delta(1.5) != Delta(2.5)

    def test_ticker_hash_matches_value(self):
        t = Ticker("PETR4")
        assert hash(t) == hash(t.value)

    def test_ticker_equal_objects(self):
        assert Ticker("petr4") == Ticker("PETR4")
        assert Ticker("PETR4") != Ticker("VALE3")
