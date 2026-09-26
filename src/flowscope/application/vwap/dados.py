"""Preparação dos dados para o gráfico de distribuição em torno do VWAP.

Contém as funções puras responsáveis por transformar os dados brutos dos
ativos em estruturas prontas para o desenho dos violinos, mantendo o
cálculo isolado da camada de apresentação gráfica.
"""

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class DadosVwap:
    """Séries percentuais e marcos por ativo para o gráfico de VWAP."""

    tickers: tuple[str, ...]
    violin_data: tuple[tuple[tuple[float, ...], tuple[float, ...]], ...]
    vwap_values_abs: tuple[float, ...]
    min_prices_pct: tuple[float, ...]
    max_prices_pct: tuple[float, ...]
    last_prices_pct: tuple[float, ...]


@dataclass(frozen=True)
class FormasViolino:
    """Formas dos violinos, volume máximo e tamanho de bucket usados no desenho."""

    shapes: tuple[tuple[tuple[float, ...], tuple[float, ...]], ...]
    max_vol: float
    bucket_size: float


def to_pct(price: float, vwap: float) -> float:
    """Devolve o percentual de diferença entre o preço e o VWAP."""
    return (price - vwap) / vwap * 100


def collect_ticker_data(data: dict) -> DadosVwap:
    """Extrai as séries de cada ativo em formato pronto para o gráfico.

    Returns:
        Read-model com tickers, dados de violino, VWAPs absolutos, mínimos,
        máximos e últimos percentuais para cada ativo com dados válidos.
    """
    tickers: list[str] = []
    violin_data: list[tuple[tuple[float, ...], tuple[float, ...]]] = []
    vwap_values_abs: list[float] = []
    min_prices_pct: list[float] = []
    max_prices_pct: list[float] = []
    last_prices_pct: list[float] = []

    for ticker, info in data.items():
        daily = info.get("daily_data", [])
        if not daily:
            continue

        vwap_info = info.get("vwap") or {}
        vwap_abs = float(vwap_info.get("period_vwap", 0))
        if vwap_abs == 0:
            continue

        tickers.append(ticker)
        vwap_values_abs.append(vwap_abs)

        prices_pct = tuple(to_pct(float(d["avg_price"]), vwap_abs) for d in daily)
        qtys = tuple(d["fin_instr_qty"] for d in daily)
        violin_data.append((prices_pct, qtys))

        min_prices_pct.append(
            to_pct(float(min(d["min_price"] for d in daily)), vwap_abs)
        )
        max_prices_pct.append(
            to_pct(float(max(d["max_price"] for d in daily)), vwap_abs)
        )

        last_day = max(daily, key=lambda d: d["date"])
        last_prices_pct.append(to_pct(float(last_day["last_price"]), vwap_abs))

    return DadosVwap(
        tickers=tuple(tickers),
        violin_data=tuple(violin_data),
        vwap_values_abs=tuple(vwap_values_abs),
        min_prices_pct=tuple(min_prices_pct),
        max_prices_pct=tuple(max_prices_pct),
        last_prices_pct=tuple(last_prices_pct),
    )


def estimate_bucket_size(violin_data: list) -> float:
    """Estima o tamanho do intervalo percentual usado nos buckets dos violinos."""
    all_prices: list[float] = []
    for prices, _ in violin_data:
        all_prices.extend(prices)
    if not all_prices:
        return 0.01
    price_range = max(all_prices) - min(all_prices)
    if price_range <= 0.5:
        return 0.01
    elif price_range <= 2:
        return 0.05
    elif price_range <= 10:
        return 0.25
    else:
        return 0.50


def compute_violin_shapes(violin_data: list) -> FormasViolino:
    """Acumula os volumes em buckets e devolve as formas dos violinos.

    Returns:
        Read-model com a lista de formas, o volume máximo encontrado e o
        tamanho do bucket usado para acumulação.
    """
    bucket_size = estimate_bucket_size(violin_data)
    max_vol = 1
    violin_shapes: list[tuple[tuple[float, ...], tuple[float, ...]]] = []

    for prices_pct, qtys in violin_data:
        buckets: dict[float, float] = defaultdict(float)
        for p, q in zip(prices_pct, qtys):
            bucket = round(p / bucket_size) * bucket_size
            buckets[bucket] += q
        sorted_buckets = sorted(buckets.items())
        y_vals = tuple(b[0] for b in sorted_buckets)
        vol_vals = tuple(b[1] for b in sorted_buckets)
        if vol_vals:
            max_vol = max(max_vol, max(vol_vals))
        violin_shapes.append((y_vals, vol_vals))

    return FormasViolino(tuple(violin_shapes), max_vol, bucket_size)
