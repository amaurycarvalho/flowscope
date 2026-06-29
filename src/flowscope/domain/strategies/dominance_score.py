from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies.base import IndicatorStrategy


class DominanceScoreStrategy(IndicatorStrategy):
    id = "dominance_score"
    dependencies: ClassVar[list[str]] = ["clv", "daily_efficiency"]

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        clv_data = dep_results["clv"]
        eff_data = dep_results["daily_efficiency"]
        result: dict[str, dict[date, Decimal | None]] = {}
        for t in trades:
            ticker = t.ticker.value
            clv = clv_data.get(ticker, {}).get(t.date)
            eff = eff_data.get(ticker, {}).get(t.date)
            if clv is not None and eff is not None:
                ds = clv * eff
            else:
                ds = None
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = ds
        return result
