"""Caso de uso do cálculo de performance por ticker e por benchmark."""

import logging
from collections.abc import Mapping, Sequence
from datetime import date

from flowscope.application.calendar.ports import (
    BusinessDayLookup,
    WeekendBusinessDayLookup,
)
from flowscope.application.fundamental_ports import DividendHistoryProvider
from flowscope.application.performance.calculo import (
    montar_ticker,
    proventos_por_data_ex,
)
from flowscope.application.performance.classificacao import (
    benchmarks_disponiveis,
    tickers_para_benchmark,
)
from flowscope.application.performance.modelos import (
    BASES_RETORNO,
    PerformanceBenchmark,
    PerformanceTicker,
)
from flowscope.application.ports import IndexHistoryRepository
from flowscope.domain.fii.dividends import DividendoConsolidado

logger = logging.getLogger("flowscope")


class AnalyzePerformanceUseCase:
    """Compara o retorno dos tickers elegíveis com o do seu benchmark."""

    def __init__(
        self: "AnalyzePerformanceUseCase",
        index_history: IndexHistoryRepository,
        dividends: DividendHistoryProvider | None = None,
        business_day: BusinessDayLookup | None = None,
    ) -> None:
        """Inicializa o caso de uso com a série do índice e os proventos."""
        self._index_history = index_history
        self._dividends = dividends
        self._business_day = business_day or WeekendBusinessDayLookup()

    def execute(
        self: "AnalyzePerformanceUseCase",
        current_data: Mapping[str, object],
        classificacao: Mapping[str, str],
        ref_date: date,
        benchmarks: Sequence[str] | None = None,
        dividends_by_ticker: Mapping[str, Sequence[DividendoConsolidado]] | None = None,
    ) -> dict[str, PerformanceBenchmark]:
        """Calcula o resultado de cada benchmark solicitado."""
        alvos = list(benchmarks) if benchmarks is not None else benchmarks_disponiveis(
            classificacao
        )
        resultados: dict[str, PerformanceBenchmark] = {}
        for benchmark in alvos:
            try:
                resultados[benchmark] = self._calcular_benchmark(
                    benchmark, current_data, classificacao, ref_date,
                    dividends_by_ticker,
                )
            except Exception:  # um benchmark não deve derrubar os demais
                logger.warning(
                    "Performance %s: falha ao calcular o benchmark; "
                    "marcando como indisponível",
                    benchmark,
                    exc_info=True,
                )
                resultados[benchmark] = _benchmark_indisponivel(benchmark)
        return resultados

    def _calcular_benchmark(
        self: "AnalyzePerformanceUseCase",
        benchmark: str,
        current_data: Mapping[str, object],
        classificacao: Mapping[str, str],
        ref_date: date,
        dividends_by_ticker: Mapping[str, Sequence[DividendoConsolidado]] | None,
    ) -> PerformanceBenchmark:
        """Calcula os tickers elegíveis de um benchmark."""
        base = BASES_RETORNO.get(benchmark, "price")
        tickers = tickers_para_benchmark(classificacao, benchmark)
        if not tickers:
            logger.info(
                "Performance %s: nenhum ticker elegível para o benchmark",
                benchmark,
            )
            return PerformanceBenchmark(benchmark, (), True, base)
        series = _series_de_precos(current_data, tickers)
        datas = [data for serie in series.values() for data in serie]
        if not datas:
            logger.info(
                "Performance %s: nenhum preço disponível para os tickers elegíveis",
                benchmark,
            )
            return PerformanceBenchmark(benchmark, (), True, base)
        serie_indice = _serie_do_indice(
            self._index_history, benchmark, min(datas), max(datas)
        )
        if not serie_indice:
            logger.warning(
                "Performance %s: série do índice indisponível entre %s e %s",
                benchmark,
                min(datas),
                max(datas),
            )
            return PerformanceBenchmark(benchmark, (), False, base)
        resultados = _calcular_tickers(
            self, tickers, series, serie_indice, base, ref_date,
            dividends_by_ticker, benchmark,
        )
        return PerformanceBenchmark(benchmark, tuple(resultados), True, base)

    def _calcular_ticker(
        self: "AnalyzePerformanceUseCase",
        ticker: str,
        serie_ticker: Mapping[date, float],
        serie_indice: Mapping[date, float],
        base: str,
        ref_date: date,
        dividends_by_ticker: Mapping[str, Sequence[DividendoConsolidado]] | None,
    ) -> PerformanceTicker | None:
        """Monta o resultado de um ticker, incorporando proventos na base total."""
        proventos = _proventos_do_ticker(
            ticker, dividends_by_ticker, self._dividends, ref_date, self._business_day
        )
        return montar_ticker(ticker, serie_ticker, serie_indice, proventos, base)


def _benchmark_indisponivel(benchmark: str) -> PerformanceBenchmark:
    """Monta o resultado de um benchmark que falhou ao ser calculado."""
    return PerformanceBenchmark(
        benchmark, (), False, BASES_RETORNO.get(benchmark, "price")
    )


def _calcular_tickers(
    caso: AnalyzePerformanceUseCase,
    tickers: Sequence[str],
    series: Mapping[str, Mapping[date, float]],
    serie_indice: Mapping[date, float],
    base: str,
    ref_date: date,
    dividends_by_ticker: Mapping[str, Sequence[DividendoConsolidado]] | None,
    benchmark: str,
) -> list[PerformanceTicker]:
    """Calcula cada ticker elegível, registrando os que ficam de fora."""
    resultados: list[PerformanceTicker] = []
    for ticker in tickers:
        if ticker not in series:
            logger.warning(
                "Performance %s: ticker %s sem dados de preço",
                benchmark,
                ticker,
            )
            continue
        item = caso._calcular_ticker(
            ticker, series[ticker], serie_indice, base, ref_date,
            dividends_by_ticker,
        )
        if item is None:
            logger.warning(
                "Performance %s: ticker %s com menos de 2 observações "
                "alinhadas ao índice",
                benchmark,
                ticker,
            )
            continue
        resultados.append(item)
    return resultados


def _series_de_precos(
    current_data: Mapping[str, object], tickers: Sequence[str]
) -> dict[str, dict[date, float]]:
    """Extrai as séries ``(data, fechamento)`` dos tickers informados."""
    series: dict[str, dict[date, float]] = {}
    for ticker in tickers:
        info = current_data.get(ticker)
        if not isinstance(info, Mapping):
            continue
        serie = _serie_de_info(info)
        if serie:
            series[ticker] = serie
    return series


def _serie_de_info(info: Mapping[str, object]) -> dict[date, float]:
    """Devolve ``daily_data`` convertido em um mapa data → último preço válido."""
    serie: dict[date, float] = {}
    for dia in info.get("daily_data", []) or []:
        if not isinstance(dia, Mapping):
            continue
        momento = dia.get("date")
        preco = _preco_valido(dia.get("last_price"))
        if isinstance(momento, date) and preco is not None:
            serie[momento] = preco
    return serie


def _preco_valido(valor: object) -> float | None:
    """Devolve o preço como float positivo, ou ``None``."""
    try:
        preco = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return preco if preco > 0 else None


def _serie_do_indice(
    index_history: IndexHistoryRepository, index: str, inicio: date, fim: date
) -> dict[date, float]:
    """Obtém a série do índice no intervalo e a converte em mapa."""
    serie: dict[date, float] = {}
    for fechamento in index_history.get_index_history(index, inicio, fim):
        valor = _preco_valido(fechamento.close)
        if valor is not None:
            serie[fechamento.date] = valor
    return serie


def _proventos_do_ticker(
    ticker: str,
    dividends_by_ticker: Mapping[str, Sequence[DividendoConsolidado]] | None,
    provider: DividendHistoryProvider | None,
    ref_date: date,
    business_day: BusinessDayLookup,
) -> dict[date, float]:
    """Obtém e converte os proventos do ticker em mapa por data ex."""
    dividendos: Sequence[DividendoConsolidado] = ()
    if dividends_by_ticker is not None and ticker in dividends_by_ticker:
        dividendos = dividends_by_ticker[ticker]
    elif provider is not None:
        try:
            dividendos = provider.obter_dividendos(ticker, ref_date)
        except Exception:  # falha de provento não deve derrubar o benchmark
            logger.warning(
                "Performance: falha ao obter proventos de %s; "
                "seguindo sem proventos",
                ticker,
                exc_info=True,
            )
            dividendos = ()
    return proventos_por_data_ex(dividendos, business_day)
