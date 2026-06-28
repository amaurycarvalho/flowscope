from collections.abc import Iterable
from datetime import date

from flowscope.application.ports import DataRepository
from flowscope.domain.engine import IndicatorEngine
from flowscope.domain.indicators import default_engine


class AnalyzeTickersUseCase:
    def __init__(
        self,
        repository: DataRepository,
        engine: IndicatorEngine | None = None,
    ):
        self._repository = repository
        self._engine = engine if engine is not None else default_engine()

    def execute(
        self, ref_date: date, tickers: list[str] | None = None
    ) -> dict:
        dates = self._repository.get_available_dates(ref_date)
        trades = self._repository.fetch_trades(dates, tickers)

        if not tickers:
            top = self._engine.execute(trades)
            tickers = top.get("top_tickers", {}).get("_all", [])

        filtered = [t for t in trades if t.ticker.value in tickers]

        results = self._engine.execute(filtered)

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
                "vwap": results.get("vwap", {}).get(ticker),
                "volume_profile": results.get("volume_profile", {}).get(ticker, {}),
                "daily_data": daily_data.get(ticker, []),
                "money_flow_volume": results.get("money_flow_volume", {}).get(ticker),
                "all_indicators": {
                    k: v.get(ticker) for k, v in results.items()
                    if k not in ("vwap", "volume_profile", "top_tickers")
                },
            }
        return result


class ExportVWAPUseCase:
    def __init__(
        self,
        repository: DataRepository,
        engine: IndicatorEngine | None = None,
    ):
        self._repository = repository
        self._engine = engine if engine is not None else default_engine()

    def execute(
        self, ref_date: date, tickers: list[str] | None = None,
        ticker_filter: list[str] | None = None,
    ) -> str:
        dates = self._repository.get_available_dates(ref_date)
        trades = self._repository.fetch_trades(dates, tickers)

        if ticker_filter:
            trades = [t for t in trades if t.ticker.value in ticker_filter]

        results = self._engine.execute(trades)
        vwap = results.get("vwap", {})
        all_dates = sorted({
            d for info in vwap.values()
            if info
            for d in info.get("daily_vwap", {})
        })
        date_headers = ";".join(d.isoformat() for d in all_dates)
        lines = [f"Ticker;VWAP_Periodo;{date_headers}"]
        for ticker, data in vwap.items():
            if data is None:
                continue
            daily = data.get("daily_vwap", {})
            vals = ";".join(
                str(daily.get(d, "")) for d in all_dates
            )
            lines.append(f"{ticker};{data.get('period_vwap', '')};{vals}")
        return "\n".join(lines)
