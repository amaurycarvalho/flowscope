from dataclasses import dataclass
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



