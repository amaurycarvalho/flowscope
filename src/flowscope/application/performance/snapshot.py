"""Montagem e leitura do snapshot estável dos resultados de performance.

O snapshot é a visão auto-descritiva e descobrível do cálculo mais recente. É
compartilhado pela GUI, pelo headless, pelo chat, pela CLI de leitura e pelo
servidor MCP, de modo que todas as superfícies observem o mesmo resultado.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone

from flowscope.application.performance.classificacao import (
    benchmark_padrao,
    tickers_para_benchmark,
)
from flowscope.application.performance.modelos import (
    BASES_RETORNO,
    SCHEMA_VERSION_PERFORMANCE,
    PerformanceBenchmark,
    PerformanceCacheKey,
    benchmark_de_dict,
    benchmark_para_dict,
)

logger = logging.getLogger("flowscope")

#: Versão do schema do snapshot de performance.
SCHEMA_VERSION_SNAPSHOT = SCHEMA_VERSION_PERFORMANCE

#: Origem do snapshot, conforme a superfície que calculou o resultado.
SOURCE_GUI = "gui"
SOURCE_HEADLESS = "headless"


def montar_payload(
    resultados: Mapping[str, PerformanceBenchmark],
    classificacao: Mapping[str, str],
    benchmarks: Sequence[str],
    tickers: Sequence[str],
) -> dict:
    """Monta o payload consumido pelo painel e pelo snapshot."""
    return {
        "benchmarks": list(benchmarks),
        "default": benchmark_padrao(tickers, classificacao),
        "ticker_types": dict(classificacao),
        "results": {
            benchmark: benchmark_para_dict(resultados[benchmark])
            for benchmark in benchmarks
            if benchmark in resultados
        },
    }


def montar_snapshot(
    payload: Mapping[str, object],
    *,
    ref_date: date,
    period_days: int,
    sampling_method: str,
    source: str,
    cached_at: datetime | None = None,
) -> dict:
    """Acrescenta ao payload o contexto auto-descritivo do cálculo."""
    momento = cached_at or datetime.now(timezone.utc)
    return {
        "schema_version": SCHEMA_VERSION_SNAPSHOT,
        "source": source,
        "ref_date": ref_date.isoformat(),
        "period_days": int(period_days),
        "sampling_method": sampling_method,
        "cached_at": momento.isoformat(),
        "benchmarks": list(payload.get("benchmarks", []) or []),
        "default": payload.get("default"),
        "ticker_types": dict(payload.get("ticker_types", {}) or {}),
        "results": dict(payload.get("results", {}) or {}),
    }


def snapshot_de_dict(dados: object) -> dict | None:
    """Valida e devolve o snapshot, ou ``None`` quando ausente/divergente.

    Tolera JSON inválido e ``results`` não-dicionário, tratando ambos como
    ausência de resultado. Não registra log: os adaptadores de I/O acrescentam
    o caminho e o motivo.
    """
    if not _estrutura_valida(dados) or not _contexto_valido(dados):
        return None
    return dados  # type: ignore[return-value]


def _estrutura_valida(dados: object) -> bool:
    """Valida o schema e os blocos estruturais do snapshot."""
    if not isinstance(dados, dict):
        return False
    if dados.get("schema_version") != SCHEMA_VERSION_SNAPSHOT:
        return False
    return (
        isinstance(dados.get("results"), dict)
        and isinstance(dados.get("benchmarks"), list)
        and isinstance(dados.get("ticker_types"), dict)
    )


def _contexto_valido(dados: object) -> bool:
    """Valida a data e os campos de contexto do snapshot."""
    if not isinstance(dados, dict):
        return False
    if not _data_valida(dados.get("ref_date")):
        return False
    periodo = dados.get("period_days")
    if isinstance(periodo, bool) or not isinstance(periodo, int):
        return False
    return isinstance(dados.get("sampling_method"), str) and isinstance(
        dados.get("cached_at"), str
    )


def _data_valida(valor: object) -> bool:
    """Indica se o valor é uma data ISO válida."""
    if not isinstance(valor, str):
        return False
    try:
        date.fromisoformat(valor)
    except ValueError:
        return False
    return True


def chave_cache(
    benchmark: str,
    classificacao: Mapping[str, str],
    ref_date: date,
    period_days: int,
    sampling_method: str,
) -> PerformanceCacheKey:
    """Monta a chave lógica do benchmark com os tickers ordenados."""
    tickers = tuple(sorted(tickers_para_benchmark(classificacao, benchmark)))
    return PerformanceCacheKey(
        schema_version=SCHEMA_VERSION_PERFORMANCE,
        index=benchmark,
        ref_date=ref_date,
        period_days=period_days,
        sampling_method=sampling_method,
        tickers=tickers,
        return_basis=BASES_RETORNO.get(benchmark, "price"),
    )


def ler_cache(
    cache: object,
    benchmarks: Sequence[str],
    classificacao: Mapping[str, str],
    ref_date: date,
    period_days: int,
    sampling_method: str,
) -> dict[str, PerformanceBenchmark]:
    """Lê do cache os benchmarks já calculados com a mesma chave."""
    resultados: dict[str, PerformanceBenchmark] = {}
    for benchmark in benchmarks:
        chave = chave_cache(
            benchmark, classificacao, ref_date, period_days, sampling_method
        )
        bruto = cache.obter(chave)  # type: ignore[attr-defined]
        if bruto is None:
            continue
        resultado = benchmark_de_dict(bruto)
        if resultado is None:
            logger.warning(
                "Performance: cache inválido para %s; recalculando", benchmark
            )
            continue
        resultados[benchmark] = resultado
    return resultados


def gravar_cache(
    cache: object,
    calculados: Mapping[str, PerformanceBenchmark],
    classificacao: Mapping[str, str],
    ref_date: date,
    period_days: int,
    sampling_method: str,
) -> None:
    """Armazena no cache os benchmarks recém-calculados."""
    for benchmark, resultado in calculados.items():
        chave = chave_cache(
            benchmark, classificacao, ref_date, period_days, sampling_method
        )
        cache.registrar(chave, benchmark_para_dict(resultado))  # type: ignore[attr-defined]
