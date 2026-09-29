"""Portas (interfaces) da camada de aplicação para acesso a dados."""

from collections.abc import Callable, Iterable
from datetime import date
from typing import Protocol

from flowscope.application.cancellation import CancellationToken
from flowscope.domain.entities import TradeDay
from flowscope.domain.sampling import SamplingConfig


class DataRepository(Protocol):
    """Define o contrato para obtenção de dados de negociação e carteiras."""

    def fetch_trades(
        self: "DataRepository", date_range: Iterable[date], tickers: list[str] | None = None,
        progress_callback: Callable[[str, bool], None] | None = None,
        cache_only: bool = False,
        cancel_token: CancellationToken | None = None,
    ) -> list[TradeDay]:
        """Retorna as negociações das datas informadas, filtrando por tickers quando indicado."""
        ...

    def get_available_dates(self: "DataRepository", ref_date: date,
                            config: SamplingConfig | None = None) -> list[date]:
        """Retorna as datas de amostragem disponíveis a partir da data de referência."""
        ...

    def get_index_tickers(
        self: "DataRepository", index: str,
        progress_callback: Callable[[str, bool], None] | None = None,
        cancel_token: CancellationToken | None = None,
    ) -> list[str]:
        """Retorna a lista de tickers do índice informado."""
        ...
