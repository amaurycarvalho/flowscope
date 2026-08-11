"""Casos de uso da camada de aplicação do FlowScope."""

from collections.abc import Callable
from datetime import date, timedelta

from flowscope.application.ports import DataRepository
from flowscope.domain.engine import IndicatorEngine
from flowscope.domain.entities import TradeDay
from flowscope.domain.indicators import default_engine
from flowscope.domain.sampling import SamplingConfig


class AnalyzeTickersUseCase:
    """Analisa o fluxo de ordens de um conjunto de tickers em uma janela de datas."""

    def __init__(
        self: "AnalyzeTickersUseCase",
        repository: DataRepository,
        engine: IndicatorEngine | None = None,
    ) -> None:
        """Inicializa o caso de uso com o repositório e o motor de indicadores."""
        self._repository = repository
        self._engine = engine if engine is not None else default_engine()

    def execute(
        self: "AnalyzeTickersUseCase", ref_date: date, tickers: list[str] | None = None,
        progress_callback: Callable[[str, bool], None] | None = None,
        config: SamplingConfig | None = None,
    ) -> dict:
        """Executa a análise, agregando resultados e dados diários por ticker."""
        dates = self._repository.get_available_dates(ref_date, config=config)
        cache_only = (config.period_days > 30) if config else False
        trades = self._repository.fetch_trades(dates, tickers,
                                               progress_callback=progress_callback,
                                               cache_only=cache_only)

        if not tickers:
            tickers = _derive_tickers(self._engine, trades)

        filtered = [t for t in trades if t.ticker.value in tickers]
        sampling_dates, filtered = _resolve_sampling_dates(
            dates, filtered, set(tickers), self._repository, cache_only, ref_date
        )
        results = self._engine.execute(filtered, progress_callback=progress_callback)
        daily_data = _build_daily_data(filtered)
        return _build_result(tickers, results, daily_data, sampling_dates)


def _derive_tickers(engine: IndicatorEngine, trades: list[TradeDay]) -> list[str]:
    """Deriva a lista de tickers analisados a partir dos resultados do motor."""
    top = engine.execute(trades, progress_callback=None)
    return top.get("top_tickers", {}).get("_all", [])


def _find_replacement_date(
    d: date,
    seen: set[date],
    ticker_set: set[str],
    repository: DataRepository,
    cache_only: bool,
    ref_date: date,
) -> tuple[date | None, list[TradeDay]]:
    """Procura uma data próxima com negociações para substituir uma data sem dados.

    A busca nunca ultrapassa a data de referência, evitando que datas
    futuras sejam consultadas na B3.
    """
    for delta in range(1, 8):
        for sign in (-1, 1):
            candidate = d + timedelta(days=delta * sign)
            if candidate > ref_date or candidate in seen or candidate.weekday() >= 5:
                continue
            new_trades = repository.fetch_trades(
                [candidate], list(ticker_set),
                progress_callback=None, cache_only=cache_only,
            )
            if new_trades:
                return candidate, new_trades
    return None, []


def _resolve_sampling_dates(
    dates: list[date],
    filtered: list[TradeDay],
    ticker_set: set[str],
    repository: DataRepository,
    cache_only: bool,
    ref_date: date,
) -> tuple[list[date], list[TradeDay]]:
    """Substitui datas de amostragem sem negociações por datas próximas com dados."""
    dates_with_trades = {t.date for t in filtered}
    sampling_dates = list(dates)
    seen = set(dates)

    for i, d in enumerate(sampling_dates):
        if d in dates_with_trades:
            continue
        replacement, new_trades = _find_replacement_date(
            d, seen, ticker_set, repository, cache_only, ref_date
        )
        if replacement:
            filtered.extend(new_trades)
            sampling_dates[i] = replacement
            seen.add(replacement)
            seen.discard(d)
            dates_with_trades.add(replacement)
    return sampling_dates, filtered


def _build_daily_data(filtered: list[TradeDay]) -> dict[str, list[dict]]:
    """Monta o mapa de dados diários agregados por ticker."""
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
            "fin_vol": t.fin_vol,
            "fin_instr_qty": t.fin_instr_qty,
            "segment": t.segment,
            "trades_qty": t.trades_qty.value,
        })
    return daily_data


def _build_result(
    tickers: list[str],
    results: dict,
    daily_data: dict[str, list[dict]],
    sampling_dates: list[date],
) -> dict:
    """Monta o resultado final com indicadores, dados diários e datas de amostragem."""
    result: dict = {"_sampling_dates": sampling_dates}
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
    """Exporta os valores de VWAP por ticker em formato CSV."""

    def __init__(
        self: "ExportVWAPUseCase",
        repository: DataRepository,
        engine: IndicatorEngine | None = None,
    ) -> None:
        """Inicializa o caso de uso com o repositório e o motor de indicadores."""
        self._repository = repository
        self._engine = engine if engine is not None else default_engine()

    def execute(
        self: "ExportVWAPUseCase", ref_date: date, tickers: list[str] | None = None,
        ticker_filter: list[str] | None = None,
    ) -> str:
        """Gera o texto CSV com o VWAP do período e diário de cada ticker."""
        dates = self._repository.get_available_dates(ref_date)
        trades = self._repository.fetch_trades(dates, tickers)

        if ticker_filter:
            trades = [t for t in trades if t.ticker.value in ticker_filter]

        results = self._engine.execute(trades)
        vwap = results.get("vwap", {})
        all_dates = _collect_vwap_dates(vwap)
        lines = _format_vwap_rows(vwap, all_dates)
        return "\n".join(lines)


def _collect_vwap_dates(vwap: dict) -> list[date]:
    """Coleta todas as datas diárias presentes nos dados de VWAP."""
    return sorted({
        d for info in vwap.values()
        if info
        for d in info.get("daily_vwap", {})
    })


def _format_vwap_rows(vwap: dict, all_dates: list[date]) -> list[str]:
    """Formata as linhas do CSV de VWAP por ticker."""
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
    return lines
