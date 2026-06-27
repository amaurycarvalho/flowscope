from collections import defaultdict
from datetime import date
from decimal import Decimal

from flowscope.domain.entities import TradeDay


def calculate_vwap(trades: list[TradeDay]) -> dict[str, dict]:
    daily: dict[str, dict[date, Decimal]] = defaultdict(dict)
    qty_total: dict[str, int] = defaultdict(int)
    vwap_sum: dict[str, Decimal] = defaultdict(Decimal)

    for t in trades:
        ticker = t.ticker.value
        if t.fin_instr_qty <= 0:
            continue
        qty = t.fin_instr_qty
        daily_vwap = t.avg_price.value
        daily[ticker][t.date] = daily_vwap
        vwap_sum[ticker] += t.avg_price.value * Decimal(str(qty))
        qty_total[ticker] += qty

    result = {}
    for ticker in vwap_sum:
        period_vwap = vwap_sum[ticker] / Decimal(str(qty_total[ticker]))
        result[ticker] = {
            "period_vwap": period_vwap,
            "daily_vwap": dict(daily[ticker]),
            "total_fin_instr_qty": qty_total[ticker],
        }
    return result


def calculate_cvd(trades: list[TradeDay]) -> dict[str, dict]:
    daily_cvd: dict[str, dict[date, float]] = defaultdict(dict)
    accumulated: dict[str, float] = defaultdict(float)

    for t in trades:
        ticker = t.ticker.value
        if t.last_price.value > t.avg_price.value:
            delta = float(t.fin_vol)
        elif t.last_price.value < t.avg_price.value:
            delta = -float(t.fin_vol)
        else:
            delta = 0.0
        daily_cvd[ticker][t.date] = daily_cvd[ticker].get(t.date, 0.0) + delta
        accumulated[ticker] += delta

    result = {}
    for ticker in accumulated:
        result[ticker] = {
            "accumulated_cvd": accumulated[ticker],
            "daily_cvd": dict(daily_cvd[ticker]),
        }
    return result


def calculate_volume_profile(
    trades: list[TradeDay], tick_size: float
) -> dict[str, dict[Decimal, Decimal]]:
    tick_decimal = Decimal(str(tick_size))
    profiles: dict[str, defaultdict[Decimal, Decimal]] = defaultdict(
        lambda: defaultdict(Decimal)
    )

    for t in trades:
        ticker = t.ticker.value
        low = (t.min_price.value // tick_decimal) * tick_decimal
        high = (t.max_price.value // tick_decimal) * tick_decimal
        bucket_count = int((high - low) / tick_decimal) + 1
        if bucket_count <= 0:
            bucket_count = 1
        vol_per_bucket = t.fin_vol // Decimal(str(bucket_count))
        remainder = t.fin_vol - vol_per_bucket * Decimal(str(bucket_count))

        for i in range(bucket_count):
            bucket = low + tick_decimal * Decimal(str(i))
            profiles[ticker][bucket] += vol_per_bucket
        if remainder and bucket_count > 0:
            last_bucket = low + tick_decimal * Decimal(str(bucket_count - 1))
            profiles[ticker][last_bucket] += remainder

    return {t: dict(p) for t, p in profiles.items()}


def select_top_tickers(
    trades: list[TradeDay], n: int = 15
) -> list[str]:
    fin_vol_sums: dict[str, Decimal] = defaultdict(Decimal)
    for t in trades:
        fin_vol_sums[t.ticker.value] += t.fin_vol
    sorted_tickers = sorted(
        fin_vol_sums.items(), key=lambda x: x[1], reverse=True
    )
    return [ticker for ticker, _ in sorted_tickers[:n]]
