from collections.abc import Iterable
from datetime import date
from decimal import Decimal

from flowscope.application.ports import DataRepository
from flowscope.domain.indicators import (
    calculate_cvd,
    calculate_volume_profile,
    calculate_vwap,
    select_top_tickers,
)


class AnalyzeTickersUseCase:
    def __init__(self, repository: DataRepository):
        self._repository = repository

    def execute(
        self, ref_date: date, tickers: list[str] | None = None
    ) -> dict:
        dates = self._repository.get_available_dates(ref_date)
        trades = self._repository.fetch_trades(dates, tickers)

        if not tickers:
            tickers = select_top_tickers(trades)

        filtered = [t for t in trades if t.ticker.value in tickers]

        vwap = calculate_vwap(filtered)
        cvd = calculate_cvd(filtered)
        vp = calculate_volume_profile(filtered, 0.01)

        daily_data: dict[str, list[dict]] = {}
        for t in filtered:
            ticker = t.ticker.value
            if ticker not in daily_data:
                daily_data[ticker] = []
            daily_data[ticker].append({
                "date": t.date,
                "avg_price": t.avg_price.value,
                "min_price": t.min_price.value,
                "max_price": t.max_price.value,
                "last_price": t.last_price.value,
                "fin_instr_qty": t.fin_instr_qty,
            })

        result = {}
        for ticker in tickers:
            result[ticker] = {
                "vwap": vwap.get(ticker),
                "cvd": cvd.get(ticker),
                "volume_profile": vp.get(ticker, {}),
                "daily_data": daily_data.get(ticker, []),
            }
        return result


class ExportVWAPUseCase:
    def __init__(self, repository: DataRepository):
        self._repository = repository

    def execute(
        self, ref_date: date, tickers: list[str] | None = None,
        ticker_filter: list[str] | None = None,
    ) -> str:
        dates = self._repository.get_available_dates(ref_date)
        trades = self._repository.fetch_trades(dates, tickers)

        if ticker_filter:
            trades = [t for t in trades if t.ticker.value in ticker_filter]

        vwap = calculate_vwap(trades)
        all_dates = sorted({
            d for info in vwap.values()
            for d in info.get("daily_vwap", {})
        })
        date_headers = ";".join(d.isoformat() for d in all_dates)
        lines = [f"Ticker;VWAP_Periodo;{date_headers}"]
        for ticker, data in vwap.items():
            daily = data.get("daily_vwap", {})
            vals = ";".join(
                str(daily.get(d, "")) for d in all_dates
            )
            lines.append(f"{ticker};{data['period_vwap']};{vals}")
        return "\n".join(lines)



