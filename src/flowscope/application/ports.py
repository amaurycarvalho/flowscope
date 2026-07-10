from collections.abc import Callable, Iterable
from datetime import date
from typing import Protocol

from flowscope.domain.entities import TradeDay
from flowscope.domain.sampling import SamplingConfig


class DataRepository(Protocol):
    def fetch_trades(
        self, date_range: Iterable[date], tickers: list[str] | None = None,
        progress_callback: Callable[[str, bool], None] | None = None,
        cache_only: bool = False,
    ) -> list[TradeDay]:
        ...

    def get_available_dates(self, ref_date: date,
                            config: SamplingConfig | None = None) -> list[date]:
        ...

    def get_index_tickers(
        self, index: str,
        progress_callback: Callable[[str, bool], None] | None = None,
    ) -> list[str]:
        ...
