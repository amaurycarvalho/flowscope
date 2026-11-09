"""Cálculo de performance versus índice e seleção dos benchmarks."""

from flowscope.application.performance.calculo import (
    alinhar_datas,
    derivar_data_ex,
    detectar_evento_societario,
    montar_ticker,
    proventos_por_data_ex,
    retorno_preco,
    retorno_total,
)
from flowscope.application.performance.caso_de_uso import (
    AnalyzePerformanceUseCase,
)
from flowscope.application.performance.classificacao import (
    benchmark_padrao,
    benchmarks_disponiveis,
    classificar_elegiveis,
    tickers_para_benchmark,
)
from flowscope.application.performance.modelos import (
    BASE_PRECO,
    BASE_TOTAL,
    BASES_RETORNO,
    BENCHMARK_IBOV,
    BENCHMARK_IDIV,
    BENCHMARK_IFIX,
    BENCHMARKS_POR_TIPO,
    ORDEM_BENCHMARKS,
    SCHEMA_VERSION_PERFORMANCE,
    TIPO_ACAO,
    TIPO_FII,
    PerformanceBenchmark,
    PerformanceCacheKey,
    PerformanceTicker,
    benchmark_de_dict,
    benchmark_para_dict,
)
from flowscope.application.performance.ports import PerformanceCache

__all__ = [
    "BASES_RETORNO",
    "BASE_PRECO",
    "BASE_TOTAL",
    "BENCHMARKS_POR_TIPO",
    "BENCHMARK_IBOV",
    "BENCHMARK_IDIV",
    "BENCHMARK_IFIX",
    "ORDEM_BENCHMARKS",
    "SCHEMA_VERSION_PERFORMANCE",
    "TIPO_ACAO",
    "TIPO_FII",
    "AnalyzePerformanceUseCase",
    "PerformanceBenchmark",
    "PerformanceCache",
    "PerformanceCacheKey",
    "PerformanceTicker",
    "alinhar_datas",
    "benchmark_de_dict",
    "benchmark_padrao",
    "benchmark_para_dict",
    "benchmarks_disponiveis",
    "classificar_elegiveis",
    "derivar_data_ex",
    "detectar_evento_societario",
    "montar_ticker",
    "proventos_por_data_ex",
    "retorno_preco",
    "retorno_total",
    "tickers_para_benchmark",
]
