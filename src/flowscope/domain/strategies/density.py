from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies.base import IndicatorStrategy


class FinancialDensityStrategy(IndicatorStrategy):
    id = "financial_density"
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
                val = t.fin_vol / r
            else:
                val = None
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = val
        return result


class TradeDensityStrategy(IndicatorStrategy):
    id = "trade_density"
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
                val = Decimal(str(t.trades_qty.value)) / r
            else:
                val = None
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = val
        return result


class VolumeDensityStrategy(IndicatorStrategy):
    id = "volume_density"
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
                val = Decimal(str(t.fin_instr_qty)) / r
            else:
                val = None
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = val
        return result
