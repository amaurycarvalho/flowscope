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

        result = {}
        for ticker in tickers:
            result[ticker] = {
                "vwap": vwap.get(ticker),
                "cvd": cvd.get(ticker),
                "volume_profile": vp.get(ticker, {}),
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


class ExportCVDUseCase:
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

        cvd = calculate_cvd(trades)
        all_dates = sorted({
            d for info in cvd.values()
            for d in info.get("daily_cvd", {})
        })
        date_headers = ";".join(d.isoformat() for d in all_dates)
        lines = [f"Ticker;CVD_Acumulado;{date_headers}"]
        for ticker, data in cvd.items():
            daily = data.get("daily_cvd", {})
            vals = ";".join(
                str(daily.get(d, "")) for d in all_dates
            )
            lines.append(f"{ticker};{data['accumulated_cvd']};{vals}")
        return "\n".join(lines)
