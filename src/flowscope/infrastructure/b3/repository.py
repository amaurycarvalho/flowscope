from collections.abc import Iterable
from datetime import date

from flowscope.application.ports import DataRepository
from flowscope.domain.entities import TradeDay
from flowscope.infrastructure.b3.calendar import fibonacci_dates
from flowscope.infrastructure.b3.client import B3Client
from flowscope.infrastructure.b3.parser import parse_csv, ParseError


class B3DataRepository(DataRepository):
    def __init__(self, client: B3Client | None = None):
        self._client = client or B3Client()

    def get_available_dates(self, ref_date: date) -> list[date]:
        return fibonacci_dates(ref_date)

    def fetch_trades(
        self, date_range: Iterable[date], tickers: list[str] | None = None
    ) -> list[TradeDay]:
        all_trades: list[TradeDay] = []
        for d in date_range:
            try:
                content = self._client.fetch_file(d)
                trades = parse_csv(content)
                if tickers is not None:
                    trades = [
                        t for t in trades if t.ticker.value in tickers
                    ]
                all_trades.extend(trades)
            except ParseError as e:
                print(f"Erro ao processar CSV da data {d}: {e}")
                continue
            except Exception as e:
                print(
                    f"Erro ao baixar dados da data {d}: "
                    f"{e}. Pulando esta data."
                )
                continue
        return all_trades
