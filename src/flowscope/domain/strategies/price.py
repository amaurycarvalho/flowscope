from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies.base import IndicatorStrategy


class RangeStrategy(IndicatorStrategy):
    id = "range"
    dependencies: ClassVar[list[str]] = []

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal]]:
        result: dict[str, dict[date, Decimal]] = {}
        for t in trades:
            ticker = t.ticker.value
            r = t.max_price.value - t.min_price.value
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = r
        return result


class TypicalPriceStrategy(IndicatorStrategy):
    id = "typical_price"
    dependencies: ClassVar[list[str]] = []

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal]]:
        result: dict[str, dict[date, Decimal]] = {}
        for t in trades:
            ticker = t.ticker.value
            tp = (t.max_price.value + t.min_price.value + t.last_price.value) / Decimal("3")
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = tp
        return result


class MedianPriceStrategy(IndicatorStrategy):
    id = "median_price"
    dependencies: ClassVar[list[str]] = []

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal]]:
        result: dict[str, dict[date, Decimal]] = {}
        for t in trades:
            ticker = t.ticker.value
            mp = (t.max_price.value + t.min_price.value) / Decimal("2")
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = mp
        return result


class WeightedCloseStrategy(IndicatorStrategy):
    id = "weighted_close"
    dependencies: ClassVar[list[str]] = []

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal]]:
        result: dict[str, dict[date, Decimal]] = {}
        for t in trades:
            ticker = t.ticker.value
            wc = (t.max_price.value + t.min_price.value + Decimal("2") * t.last_price.value) / Decimal("4")
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = wc
        return result


class RangePercentualStrategy(IndicatorStrategy):
    id = "range_percentual"
    dependencies: ClassVar[list[str]] = ["range"]

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        range_data = dep_results["range"]
        result: dict[str, dict[date, Decimal | None]] = {}
        for t in trades:
            ticker = t.ticker.value
            r = range_data.get(ticker, {}).get(t.date)
            if r is not None and r != 0 and t.avg_price.value != 0:
                val = r / t.avg_price.value
            else:
                val = None
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = val
        return result
