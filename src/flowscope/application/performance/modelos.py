"""Modelos e constantes do cálculo de performance versus índice."""

from dataclasses import dataclass
from datetime import date

#: Versão do schema dos resultados de performance em cache.
SCHEMA_VERSION_PERFORMANCE = 1

BENCHMARK_IFIX = "IFIX"
BENCHMARK_IBOV = "IBOV"
BENCHMARK_IDIV = "IDIV"

TIPO_FII = "FII"
TIPO_ACAO = "ACAO"

#: Benchmarks oferecidos por tipo de ativo.
BENCHMARKS_POR_TIPO: dict[str, tuple[str, ...]] = {
    TIPO_FII: (BENCHMARK_IFIX,),
    TIPO_ACAO: (BENCHMARK_IBOV, BENCHMARK_IDIV),
}

#: Ordem de exibição das opções do combobox.
ORDEM_BENCHMARKS: tuple[str, ...] = (
    BENCHMARK_IFIX,
    BENCHMARK_IBOV,
    BENCHMARK_IDIV,
)

#: Bases de retorno possíveis.
BASE_PRECO = "price"
BASE_TOTAL = "total"

#: Base de retorno de cada benchmark.
BASES_RETORNO: dict[str, str] = {
    BENCHMARK_IFIX: BASE_TOTAL,
    BENCHMARK_IBOV: BASE_PRECO,
    BENCHMARK_IDIV: BASE_TOTAL,
}


@dataclass(frozen=True)
class PerformanceTicker:
    """Retorno acumulado de um ticker comparado ao seu índice."""

    ticker: str
    ticker_return: float
    index_return: float
    excess_pp: float
    observations: int
    suspicious_event: bool = False


@dataclass(frozen=True)
class PerformanceBenchmark:
    """Resultado de todos os tickers elegíveis para um benchmark."""

    benchmark: str
    tickers: tuple[PerformanceTicker, ...]
    index_available: bool = True
    return_basis: str = "price"


@dataclass(frozen=True)
class PerformanceCacheKey:
    """Chave lógica do cache pré-calculado de um benchmark."""

    schema_version: int
    index: str
    ref_date: date
    period_days: int
    sampling_method: str
    tickers: tuple[str, ...]
    return_basis: str

    def identidade(self: "PerformanceCacheKey") -> str:
        """Serializa a chave de forma estável para compor o nome do arquivo."""
        return "|".join(
            (
                str(self.schema_version),
                self.index,
                self.ref_date.isoformat(),
                str(self.period_days),
                self.sampling_method,
                ",".join(self.tickers),
                self.return_basis,
            )
        )


def benchmark_para_dict(resultado: PerformanceBenchmark) -> dict:
    """Devolve o resultado de um benchmark em estrutura serializável."""
    return {
        "benchmark": resultado.benchmark,
        "index_available": resultado.index_available,
        "return_basis": resultado.return_basis,
        "tickers": [
            {
                "ticker": item.ticker,
                "ticker_return": item.ticker_return,
                "index_return": item.index_return,
                "excess_pp": item.excess_pp,
                "observations": item.observations,
                "suspicious_event": item.suspicious_event,
            }
            for item in resultado.tickers
        ],
    }


def benchmark_de_dict(dados: object) -> PerformanceBenchmark | None:
    """Reconstrói o resultado de um benchmark, tolerando dados corrompidos."""
    if not isinstance(dados, dict):
        return None
    benchmark = dados.get("benchmark")
    tickers = dados.get("tickers")
    if not isinstance(benchmark, str) or not isinstance(tickers, list):
        return None
    itens: list[PerformanceTicker] = []
    for item in tickers:
        convertido = _ticker_de_dict(item)
        if convertido is not None:
            itens.append(convertido)
    return PerformanceBenchmark(
        benchmark=benchmark,
        tickers=tuple(itens),
        index_available=bool(dados.get("index_available", True)),
        return_basis=str(dados.get("return_basis", "price")),
    )


def _ticker_de_dict(item: object) -> PerformanceTicker | None:
    """Reconstrói um item de ticker, rejeitando registros inválidos."""
    if not isinstance(item, dict):
        return None
    try:
        return PerformanceTicker(
            ticker=str(item["ticker"]),
            ticker_return=float(item["ticker_return"]),
            index_return=float(item["index_return"]),
            excess_pp=float(item["excess_pp"]),
            observations=int(item["observations"]),
            suspicious_event=bool(item.get("suspicious_event", False)),
        )
    except (KeyError, TypeError, ValueError):
        return None
