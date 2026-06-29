from datetime import date
from decimal import Decimal

from flowscope.domain.strategies.daily_money_flow import DailyMoneyFlowStrategy
from flowscope.domain.strategies.dominance_score import DominanceScoreStrategy
from flowscope.domain.strategies.classifiers import (
    classify_dominance,
    classify_conviction,
    DominanceClassification,
    ConvictionClassification,
)
from flowscope.domain.entities import TradeDay
from flowscope.domain.value_objects import Price, Ticker, Volume


class TestDailyMoneyFlowStrategy:
    def test_positive_flow(self):
        s = DailyMoneyFlowStrategy()
        clv_data = {"TEST": {date(2026, 6, 25): Decimal("0.5")}}
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("15"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"), fin_instr_qty=100,
        )
        result = s.compute([trade], {"clv": clv_data})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("500")

    def test_negative_flow(self):
        s = DailyMoneyFlowStrategy()
        clv_data = {"TEST": {date(2026, 6, 25): Decimal("-0.3")}}
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("15"),
            trades_qty=Volume(100), fin_vol=Decimal("2000"), fin_instr_qty=100,
        )
        result = s.compute([trade], {"clv": clv_data})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("-600")

    def test_clv_is_none(self):
        s = DailyMoneyFlowStrategy()
        clv_data = {"TEST": {date(2026, 6, 25): None}}
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("10"),
            avg_price=Price("10"), last_price=Price("10"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"), fin_instr_qty=100,
        )
        result = s.compute([trade], {"clv": clv_data})
        assert result["TEST"][date(2026, 6, 25)] is None

    def test_multiple_tickers(self):
        s = DailyMoneyFlowStrategy()
        clv_data = {
            "T1": {date(2026, 6, 25): Decimal("0.5")},
            "T2": {date(2026, 6, 25): Decimal("-0.2")},
        }
        trades = [
            TradeDay(
                date=date(2026, 6, 25), ticker=Ticker("T1"),
                segment="CASH", min_price=Price("10"), max_price=Price("20"),
                avg_price=Price("15"), last_price=Price("15"),
                trades_qty=Volume(100), fin_vol=Decimal("1000"), fin_instr_qty=100,
            ),
            TradeDay(
                date=date(2026, 6, 25), ticker=Ticker("T2"),
                segment="CASH", min_price=Price("10"), max_price=Price("20"),
                avg_price=Price("15"), last_price=Price("15"),
                trades_qty=Volume(100), fin_vol=Decimal("500"), fin_instr_qty=100,
            ),
        ]
        result = s.compute(trades, {"clv": clv_data})
        assert result["T1"][date(2026, 6, 25)] == Decimal("500")
        assert result["T2"][date(2026, 6, 25)] == Decimal("-100")

    def test_empty(self):
        s = DailyMoneyFlowStrategy()
        assert s.compute([], {"clv": {}}) == {}


class TestDominanceScoreStrategy:
    def test_positive_convincing(self):
        s = DominanceScoreStrategy()
        clv_data = {"TEST": {date(2026, 6, 25): Decimal("0.80")}}
        eff_data = {"TEST": {date(2026, 6, 25): Decimal("0.90")}}
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("15"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"), fin_instr_qty=100,
        )
        result = s.compute([trade], {"clv": clv_data, "daily_efficiency": eff_data})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("0.72")

    def test_positive_not_convincing(self):
        s = DominanceScoreStrategy()
        clv_data = {"TEST": {date(2026, 6, 25): Decimal("0.80")}}
        eff_data = {"TEST": {date(2026, 6, 25): Decimal("0.20")}}
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("15"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"), fin_instr_qty=100,
        )
        result = s.compute([trade], {"clv": clv_data, "daily_efficiency": eff_data})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("0.16")

    def test_negative_convincing(self):
        s = DominanceScoreStrategy()
        clv_data = {"TEST": {date(2026, 6, 25): Decimal("-0.70")}}
        eff_data = {"TEST": {date(2026, 6, 25): Decimal("0.85")}}
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("20"),
            avg_price=Price("15"), last_price=Price("15"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"), fin_instr_qty=100,
        )
        result = s.compute([trade], {"clv": clv_data, "daily_efficiency": eff_data})
        assert result["TEST"][date(2026, 6, 25)] == Decimal("-0.595")

    def test_clv_or_efficiency_none(self):
        s = DominanceScoreStrategy()
        clv_data = {"TEST": {date(2026, 6, 25): None}}
        eff_data = {"TEST": {date(2026, 6, 25): Decimal("0.50")}}
        trade = TradeDay(
            date=date(2026, 6, 25), ticker=Ticker("TEST"),
            segment="CASH", min_price=Price("10"), max_price=Price("10"),
            avg_price=Price("10"), last_price=Price("10"),
            trades_qty=Volume(100), fin_vol=Decimal("1000"), fin_instr_qty=100,
        )
        result = s.compute([trade], {"clv": clv_data, "daily_efficiency": eff_data})
        assert result["TEST"][date(2026, 6, 25)] is None


class TestClassifyDominance:
    def test_venda_muito_forte(self):
        cls = classify_dominance(-0.85)
        assert cls.label == "Venda Muito Forte"
        assert cls.short_label == "Muito Forte"
        assert cls.score == -3

    def test_venda_muito_forte_boundary_neg_1(self):
        cls = classify_dominance(-1.5)
        assert cls.label == "Venda Muito Forte"
        assert cls.score == -3

    def test_venda_forte(self):
        cls = classify_dominance(-0.55)
        assert cls.label == "Venda Forte"
        assert cls.score == -2

    def test_venda_moderada(self):
        cls = classify_dominance(-0.30)
        assert cls.label == "Venda Moderada"
        assert cls.score == -1

    def test_equilibrio(self):
        cls = classify_dominance(0.0)
        assert cls.label == "Equilíbrio"
        assert cls.score == 0

    def test_equilibrio_boundary(self):
        cls = classify_dominance(0.14)
        assert cls.label == "Equilíbrio"
        assert cls.score == 0

    def test_compra_moderada(self):
        cls = classify_dominance(0.25)
        assert cls.label == "Compra Moderada"
        assert cls.score == 1

    def test_compra_forte(self):
        cls = classify_dominance(0.55)
        assert cls.label == "Compra Forte"
        assert cls.score == 2

    def test_compra_muito_forte(self):
        cls = classify_dominance(0.85)
        assert cls.label == "Compra Muito Forte"
        assert cls.score == 3

    def test_compra_muito_forte_boundary_pos_1(self):
        cls = classify_dominance(1.5)
        assert cls.label == "Compra Muito Forte"
        assert cls.score == 3

    def test_equilibrio_exact_boundary(self):
        lower = classify_dominance(-0.15)
        assert lower.label == "Equilíbrio"
        assert lower.score == 0
        upper = classify_dominance(0.15)
        assert upper.label == "Compra Moderada"
        assert upper.score == 1

    def test_returns_dataclass(self):
        cls = classify_dominance(0.55)
        assert isinstance(cls, DominanceClassification)
        assert cls.color == "#388E3C"
        assert cls.short_label == "Forte"


class TestClassifyConviction:
    def test_muito_baixa(self):
        cls = classify_conviction(0.10)
        assert cls.label == "Muito Baixa"
        assert cls.score == -2

    def test_muito_baixa_below_zero(self):
        cls = classify_conviction(-0.1)
        assert cls.label == "Muito Baixa"
        assert cls.score == -2

    def test_baixa(self):
        cls = classify_conviction(0.30)
        assert cls.label == "Baixa"
        assert cls.score == -1

    def test_moderada(self):
        cls = classify_conviction(0.50)
        assert cls.label == "Moderada"
        assert cls.score == 0

    def test_alta(self):
        cls = classify_conviction(0.70)
        assert cls.label == "Alta"
        assert cls.score == 1

    def test_muito_alta(self):
        cls = classify_conviction(0.90)
        assert cls.label == "Muito Alta"
        assert cls.score == 2

    def test_muito_alta_above_one(self):
        cls = classify_conviction(1.5)
        assert cls.label == "Muito Alta"
        assert cls.score == 2

    def test_boundary_exact(self):
        lower = classify_conviction(0.19)
        assert lower.label == "Muito Baixa"
        assert lower.score == -2
        upper = classify_conviction(0.20)
        assert upper.label == "Baixa"
        assert upper.score == -1

    def test_returns_dataclass(self):
        cls = classify_conviction(0.85)
        assert isinstance(cls, ConvictionClassification)
        assert cls.color == "#2E7D32"
        assert cls.short_label == "Muito Alta"


class TestIndicatorIntegration:
    def test_daily_money_flow_in_engine(self, mock_trades):
        from flowscope.domain.engine import IndicatorEngine
        from flowscope.domain.strategies import CLVStrategy
        engine = IndicatorEngine()
        engine.register(
            CLVStrategy(),
            DailyMoneyFlowStrategy(),
        )
        result = engine.execute(mock_trades)
        assert "daily_money_flow" in result
        for ticker in ("PETR4", "VALE3"):
            assert ticker in result["daily_money_flow"]
            for d in result["daily_money_flow"][ticker]:
                val = result["daily_money_flow"][ticker][d]
                if val is not None:
                    clv = result["clv"][ticker][d]
                    trade = next(
                        t for t in mock_trades
                        if t.ticker.value == ticker and t.date == d
                    )
                    assert val == clv * trade.fin_vol

    def test_dominance_score_in_engine(self, mock_trades):
        from flowscope.domain.engine import IndicatorEngine
        from flowscope.domain.strategies import (
            CLVStrategy, RangeStrategy, DailyEfficiencyStrategy,
        )
        engine = IndicatorEngine()
        engine.register(
            RangeStrategy(),
            CLVStrategy(),
            DailyEfficiencyStrategy(),
            DominanceScoreStrategy(),
        )
        result = engine.execute(mock_trades)
        assert "dominance_score" in result
        for ticker in ("PETR4", "VALE3"):
            assert ticker in result["dominance_score"]
