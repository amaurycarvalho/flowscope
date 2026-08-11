"""Estratégias de indicadores de densidade."""

from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies.base import IndicatorStrategy


class FinancialDensityStrategy(IndicatorStrategy):
    """Calcula a densidade financeira (volume/range) diária."""

    id = "financial_density"
    dependencies: ClassVar[list[str]] = ["range"]

    def compute(
        self: "FinancialDensityStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        """Retorna o volume financeiro por unidade de range."""
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
    """Calcula a densidade de negócios diária por ticker."""

    id = "trade_density"
    dependencies: ClassVar[list[str]] = ["range"]

    def compute(
        self: "TradeDensityStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        """Retorna a quantidade de negócios por unidade de range."""
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
    """Calcula a densidade de volume diária por ticker."""

    id = "volume_density"
    dependencies: ClassVar[list[str]] = ["range"]

    def compute(
        self: "VolumeDensityStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        """Retorna a quantidade de instrumentos financeiros por unidade de range."""
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
