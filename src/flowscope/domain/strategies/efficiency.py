from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies.base import IndicatorStrategy


class DailyEfficiencyStrategy(IndicatorStrategy):
    id = "daily_efficiency"
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
                desloc = abs(t.last_price.value - t.avg_price.value)
                ef = desloc / r
            else:
                ef = None
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = ef
        return result
