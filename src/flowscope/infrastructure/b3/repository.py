import logging
from collections.abc import Callable, Iterable
from datetime import date

from flowscope.application.ports import DataRepository
from flowscope.domain.entities import TradeDay
from flowscope.domain.sampling import SamplingConfig
from flowscope.infrastructure.b3.calendar import fibonacci_dates, resolve_dates
from flowscope.infrastructure.b3.client import B3Client
from flowscope.infrastructure.b3.parser import parse_csv, ParseError
from flowscope.infrastructure.cache import CacheManager

logger = logging.getLogger(__name__)


class B3DataRepository(DataRepository):
    def __init__(self, client: B3Client | None = None):
        self._client = client or B3Client()

    def get_available_dates(self, ref_date: date,
                            config: SamplingConfig | None = None) -> list[date]:
        if config is None or (config.period_days == 30 and config.method == "fibonacci"):
            return fibonacci_dates(ref_date)
        return resolve_dates(ref_date, config, cache=self._client._cache)

    def get_index_tickers(self, index: str,
                          progress_callback: Callable[[str, bool], None] | None = None) -> list[str]:
        return self._client.fetch_portfolio(index, progress_callback=progress_callback)

    def fetch_trades(
        self, date_range: Iterable[date], tickers: list[str] | None = None,
        progress_callback: Callable[[str, bool], None] | None = None,
        cache_only: bool = False,
    ) -> list[TradeDay]:
        all_trades: list[TradeDay] = []
        for d in date_range:
            try:
                content = self._client.fetch_file(
                    d, progress_callback=progress_callback, cache_only=cache_only,
                )
                if content is None:
                    continue
                trades = parse_csv(content)
                if tickers is not None:
                    trades = [
                        t for t in trades if t.ticker.value in tickers
                    ]
                all_trades.extend(trades)
            except ParseError as e:
                logger.warning("Erro ao processar CSV da data %s: %s", d, e)
                if progress_callback:
                    progress_callback(f"{d} (erro ao processar CSV)", True)
                continue
            except Exception as e:
                logger.warning(
                    "Erro ao baixar dados da data %s: %s. Pulando esta data.", d, e
                )
                if progress_callback:
                    progress_callback(f"{d} (erro ao baixar)", True)
                continue
        return all_trades
