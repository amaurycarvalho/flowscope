"""Estratégias de indicadores relacionadas a volume e VWAP."""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies.base import IndicatorStrategy


class VWAPStrategy(IndicatorStrategy):
    """Calcula o VWAP por período e diário por ticker."""

    id = "vwap"
    dependencies: ClassVar[list[str]] = []

    def compute(
        self: "VWAPStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict]:
        """Agrega os trades e retorna o VWAP por ticker."""
        daily: dict[str, dict[date, Decimal]] = defaultdict(dict)
        qty_total: dict[str, int] = defaultdict(int)
        vwap_sum: dict[str, Decimal] = defaultdict(Decimal)

        for t in trades:
            ticker = t.ticker.value
            if t.fin_instr_qty <= 0:
                continue
            qty = t.fin_instr_qty
            daily[ticker][t.date] = t.avg_price.value
            vwap_sum[ticker] += t.avg_price.value * Decimal(str(qty))
            qty_total[ticker] += qty

        result = {}
        for ticker, vwap_total in vwap_sum.items():
            period_vwap = vwap_total / Decimal(str(qty_total[ticker]))
            result[ticker] = {
                "period_vwap": period_vwap,
                "daily_vwap": dict(daily[ticker]),
                "total_fin_instr_qty": qty_total[ticker],
            }
        return result


class VolumeProfileStrategy(IndicatorStrategy):
    """Calcula o perfil de volume por faixa de preço."""

    id = "volume_profile"
    dependencies: ClassVar[list[str]] = []

    def __init__(self: "VolumeProfileStrategy", tick_size: float = 0.01) -> None:
        """Inicializa a estratégia com o tamanho do tick de preço."""
        self._tick_size = tick_size

    def compute(
        self: "VolumeProfileStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, dict[Decimal, Decimal]]:
        """Distribui o volume em buckets de preço por ticker."""
        tick_decimal = Decimal(str(self._tick_size))
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


class TopTickersStrategy(IndicatorStrategy):
    """Seleciona os tickers de maior volume financeiro."""

    id = "top_tickers"
    dependencies: ClassVar[list[str]] = []

    def __init__(self: "TopTickersStrategy", n: int = 15) -> None:
        """Inicializa a estratégia com a quantidade de tickers a selecionar."""
        self._n = n

    def compute(
        self: "TopTickersStrategy", trades: list[TradeDay], dep_results: dict[str, dict[str, Any]]
    ) -> dict[str, list[str]]:
        """Ordena os tickers por volume financeiro e retorna os n maiores."""
        fin_vol_sums: dict[str, Decimal] = defaultdict(Decimal)
        for t in trades:
            fin_vol_sums[t.ticker.value] += t.fin_vol
        sorted_tickers = sorted(
            fin_vol_sums.items(), key=lambda x: x[1], reverse=True
        )
        return {"_all": [ticker for ticker, _ in sorted_tickers[:self._n]]}
