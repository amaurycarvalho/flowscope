"""Repositório de dados da B3 que combina o cliente HTTP e o cache local."""

import logging
from collections.abc import Callable, Iterable
from datetime import date

from flowscope.application.ports import DataRepository
from flowscope.domain.entities import TradeDay
from flowscope.domain.sampling import SamplingConfig
from flowscope.infrastructure.b3.calendar import fibonacci_dates, resolve_dates
from flowscope.infrastructure.b3.client import B3Client
from flowscope.infrastructure.b3.parser import ParseError, parse_csv

logger = logging.getLogger(__name__)


class B3DataRepository(DataRepository):
    """Implementa o port DataRepository buscando dados na B3 com cache local."""

    def __init__(self: "B3DataRepository", client: B3Client | None = None) -> None:
        """Inicializa o repositório com o cliente B3 informado ou um novo padrão."""
        self._client = client or B3Client()

    def get_available_dates(self: "B3DataRepository", ref_date: date,
                            config: SamplingConfig | None = None) -> list[date]:
        """Calcula as datas de amostragem disponíveis a partir da data de referência e da configuração."""
        _SAMPLING_METHODS = frozenset({
            "fibonacci", "fibonacci_reverse", "fibonacci_double",
            "monte_carlo", "monte_carlo_double",
        })

        if config is None:
            return fibonacci_dates(ref_date)

        has_data = self._has_data if config.method in _SAMPLING_METHODS else None

        if config.period_days == 30 and config.method == "fibonacci":
            return fibonacci_dates(ref_date, has_data=has_data)

        return resolve_dates(ref_date, config, has_data=has_data)

    def _has_data(self: "B3DataRepository", d: date) -> bool:
        content = self._client._cache.get(d)
        if content is None:
            return True
        lines = content.splitlines()
        if not lines:
            return False
        data_start = 1 if not lines[0].startswith("RptDt") else 0
        return len(lines) > data_start + 1

    def get_index_tickers(self: "B3DataRepository", index: str,
                          progress_callback: Callable[[str, bool], None] | None = None) -> list[str]:
        """Retorna a lista de tickers do índice, informando o progresso via callback."""
        return self._client.fetch_portfolio(index, progress_callback=progress_callback)

    def fetch_trades(
        self: "B3DataRepository", date_range: Iterable[date], tickers: list[str] | None = None,
        progress_callback: Callable[[str, bool], None] | None = None,
        cache_only: bool = False,
    ) -> list[TradeDay]:
        """Baixa e combina as negociações das datas informadas, filtrando por tickers quando indicado."""
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
