"""Estratégias de indicadores baseadas em preço."""

from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies.base import IndicatorStrategy


class RangeStrategy(IndicatorStrategy):
    """Calcula a amplitude diária (máxima menos mínima) por ticker."""

    id = "range"
    dependencies: ClassVar[list[str]] = []

    def compute(
        self: "RangeStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal]]:
        """Retorna a amplitude diária de cada ticker."""
        result: dict[str, dict[date, Decimal]] = {}
        for t in trades:
            ticker = t.ticker.value
            r = t.max_price.value - t.min_price.value
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = r
        return result


class TypicalPriceStrategy(IndicatorStrategy):
    """Calcula o preço típico diário por ticker."""

    id = "typical_price"
    dependencies: ClassVar[list[str]] = []

    def compute(
        self: "TypicalPriceStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal]]:
        """Retorna o preço típico (média de máxima, mínima e última)."""
        result: dict[str, dict[date, Decimal]] = {}
        for t in trades:
            ticker = t.ticker.value
            tp = (t.max_price.value + t.min_price.value + t.last_price.value) / Decimal(3)
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = tp
        return result


class MedianPriceStrategy(IndicatorStrategy):
    """Calcula o preço mediano diário por ticker."""

    id = "median_price"
    dependencies: ClassVar[list[str]] = []

    def compute(
        self: "MedianPriceStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal]]:
        """Retorna o preço mediano entre máxima e mínima."""
        result: dict[str, dict[date, Decimal]] = {}
        for t in trades:
            ticker = t.ticker.value
            mp = (t.max_price.value + t.min_price.value) / Decimal(2)
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = mp
        return result


class WeightedCloseStrategy(IndicatorStrategy):
    """Calcula o preço de fechamento ponderado diário por ticker."""

    id = "weighted_close"
    dependencies: ClassVar[list[str]] = []

    def compute(
        self: "WeightedCloseStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal]]:
        """Retorna o fechamento ponderado (2*última + máxima + mínima)/4."""
        result: dict[str, dict[date, Decimal]] = {}
        for t in trades:
            ticker = t.ticker.value
            wc = (t.max_price.value + t.min_price.value + Decimal(2) * t.last_price.value) / Decimal(4)
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = wc
        return result


class RangePercentualStrategy(IndicatorStrategy):
    """Calcula o range percentual em relação ao preço médio."""

    id = "range_percentual"
    dependencies: ClassVar[list[str]] = ["range"]

    def compute(
        self: "RangePercentualStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        """Retorna o range dividido pelo preço médio, quando disponível."""
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
