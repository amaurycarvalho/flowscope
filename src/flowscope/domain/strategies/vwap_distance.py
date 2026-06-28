from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies.base import IndicatorStrategy


class VWAPDistanceStrategy(IndicatorStrategy):
    id = "vwap_distance"
    dependencies: ClassVar[list[str]] = ["vwap"]

    def compute(
        self, trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        vwap_data = dep_results.get("vwap", {})
        result: dict[str, dict[date, Decimal | None]] = {}
        for t in trades:
            ticker = t.ticker.value
            vwap_info = vwap_data.get(ticker)
            if vwap_info is None:
                continue
            daily_vwap = vwap_info.get("daily_vwap", {}).get(t.date)
            if daily_vwap is None or daily_vwap == 0:
                continue
            distance = (t.last_price.value - daily_vwap) / daily_vwap
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = distance
        return result
