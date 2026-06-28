from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies.base import IndicatorStrategy


class CLVStrategy(IndicatorStrategy):
    id = "clv"
    dependencies: ClassVar[list[str]] = []

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        result: dict[str, dict[date, Decimal | None]] = {}
        for t in trades:
            ticker = t.ticker.value
            high = t.max_price.value
            low = t.min_price.value
            close = t.last_price.value
            r = high - low
            if r != 0:
                upper = close - low
                lower = high - close
                clv = (upper - lower) / r
            else:
                clv = None
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = clv
        return result


class MoneyFlowMultiplierStrategy(IndicatorStrategy):
    id = "money_flow_multiplier"
    dependencies: ClassVar[list[str]] = ["clv"]

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        return dep_results["clv"]


class BuyingPressureStrategy(IndicatorStrategy):
    id = "buying_pressure"
    dependencies: ClassVar[list[str]] = ["range"]

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        range_data = dep_results["range"]
        result: dict[str, dict[date, Decimal | None]] = {}
        for t in trades:
            ticker = t.ticker.value
            r = range_data.get(ticker, {}).get(t.date)
            if r is not None and r != 0:
                bp = (t.last_price.value - t.min_price.value) / r
            else:
                bp = None
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = bp
        return result


class SellingPressureStrategy(IndicatorStrategy):
    id = "selling_pressure"
    dependencies: ClassVar[list[str]] = ["range"]

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        range_data = dep_results["range"]
        result: dict[str, dict[date, Decimal | None]] = {}
        for t in trades:
            ticker = t.ticker.value
            r = range_data.get(ticker, {}).get(t.date)
            if r is not None and r != 0:
                sp = (t.max_price.value - t.last_price.value) / r
            else:
                sp = None
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = sp
        return result


class MoneyFlowVolumeStrategy(IndicatorStrategy):
    id = "money_flow_volume"
    dependencies: ClassVar[list[str]] = ["money_flow_multiplier"]

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, Decimal]:
        mfm_data = dep_results["money_flow_multiplier"]
        result: dict[str, Decimal] = defaultdict(Decimal)
        for t in trades:
            ticker = t.ticker.value
            mfm = mfm_data.get(ticker, {}).get(t.date)
            if mfm is not None:
                result[ticker] += mfm * t.fin_vol
        return dict(result)
