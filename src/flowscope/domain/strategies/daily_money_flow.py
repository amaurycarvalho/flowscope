from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies.base import IndicatorStrategy


class DailyMoneyFlowStrategy(IndicatorStrategy):
    id = "daily_money_flow"
    dependencies: ClassVar[list[str]] = ["clv"]

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        clv_data = dep_results["clv"]
        result: dict[str, dict[date, Decimal | None]] = {}
        for t in trades:
            ticker = t.ticker.value
            clv = clv_data.get(ticker, {}).get(t.date)
            if clv is not None:
                dmf = clv * t.fin_vol
            else:
                dmf = None
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = dmf
        return result
