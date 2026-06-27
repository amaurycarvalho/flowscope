from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from flowscope.domain.value_objects import Price, Volume, Ticker


@dataclass
class TradeDay:
    date: date
    ticker: Ticker
    segment: str
    min_price: Price
    max_price: Price
    avg_price: Price
    last_price: Price
    trades_qty: Volume
    fin_vol: Decimal
    fin_instr_qty: int


@dataclass
class AggregatedMetrics:
    ticker: Ticker
    cvd: float
    vwap: Decimal
    volume_profile: dict[Decimal, Decimal]
    daily_breakdown: dict[date, dict[str, Decimal | int | float]] = field(default_factory=dict)
