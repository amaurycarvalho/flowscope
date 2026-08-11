"""Estratégias de indicadores de tamanho médio das negociações."""

from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies.base import IndicatorStrategy


class AverageTradeSizeStrategy(IndicatorStrategy):
    """Calcula o tamanho médio dos negócios diário."""

    id = "average_trade_size"
    dependencies: ClassVar[list[str]] = []

    def compute(
        self: "AverageTradeSizeStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        """Retorna a média de instrumentos financeiros por negócio."""
        result: dict[str, dict[date, Decimal | None]] = {}
        for t in trades:
            ticker = t.ticker.value
            if t.trades_qty.value != 0:
                val = Decimal(str(t.fin_instr_qty)) / Decimal(str(t.trades_qty.value))
            else:
                val = None
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = val
        return result


class AverageFinancialTicketStrategy(IndicatorStrategy):
    """Calcula o ticket financeiro médio diário."""

    id = "average_financial_ticket"
    dependencies: ClassVar[list[str]] = []

    def compute(
        self: "AverageFinancialTicketStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[date, Decimal | None]]:
        """Retorna o volume financeiro médio por negócio."""
        result: dict[str, dict[date, Decimal | None]] = {}
        for t in trades:
            ticker = t.ticker.value
            if t.trades_qty.value != 0:
                val = t.fin_vol / Decimal(str(t.trades_qty.value))
            else:
                val = None
            if ticker not in result:
                result[ticker] = {}
            result[ticker][t.date] = val
        return result
