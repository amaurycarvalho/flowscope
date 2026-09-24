"""Núcleo de análise de rede de correlação e cointegração em numpy puro.

Transforma séries de preço alinhadas — provenientes das observações
disponíveis na análise corrente — em uma matriz de correlação assinada,
testes de cointegração par-a-par (Engle-Granger + ADF), meia-vida de
reversão do spread e uma rede de papéis com comunidades e centralidade.
O módulo não executa I/O nem desenha.
"""

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from math import floor, isfinite, log

import networkx as nx
import numpy as np

#: Mínimo de observações alinhadas para calcular correlação.
MIN_OBS_CORR = 30

#: Mínimo de observações alinhadas para calcular cointegração.
MIN_OBS_COINT = 40

#: Limiar padrão de |correlação| para criar uma aresta entre dois papéis.
DEFAULT_CORR_THRESHOLD = 0.5

#: Nível de significância padrão do teste de cointegração.
COINT_SIGNIFICANCE = 0.05

#: Número máximo de defasagens consideradas na seleção do ADF.
MAX_LAGS = 4

#: Superfície de resposta de MacKinnon (2010) para cointegração com 2
#: variáveis, constante e sem tendência. Cada tupla traz os coeficientes
#: ``(a0, a1, a2, a3)`` de ``a0 + a1/T + a2/T^2 + a3/T^3``.
_MACKINNON_N2: dict[float, tuple[float, float, float, float]] = {
    0.01: (-3.89644, -10.9519, -33.527, 0.0),
    0.05: (-3.33613, -6.1101, -6.823, 0.0),
    0.10: (-3.04445, -4.2412, -2.720, 0.0),
}

#: Séries de preço por ticker: observações ``(data, preço de fechamento)``.
SeriesMap = Mapping[str, Sequence[tuple[date, object]]]


@dataclass(frozen=True, eq=False)
class AlignedPrices:
    """Séries de preço alinhadas por interseção de datas."""

    tickers: tuple[str, ...]
    dates: tuple[date, ...]
    prices: np.ndarray

    @property
    def n_observations(self: "AlignedPrices") -> int:
        """Número de observações de datas comuns a todos os tickers."""
        return len(self.dates)


@dataclass(frozen=True)
class SamplingDiagnostics:
    """Diagnóstico da esparsidade da amostragem alinhada."""

    n_observations: int
    span_days: int
    gap_min: int
    gap_median: float
    gap_max: int


@dataclass(frozen=True)
class PairResult:
    """Resultado da avaliação de um par de tickers."""

    ticker_a: str
    ticker_b: str
    correlation: float
    cointegrated: bool | None = None
    adf_stat: float | None = None
    half_life_obs: float | None = None
    half_life_days: float | None = None


@dataclass(frozen=True, eq=False)
class NetworkResult:
    """Rede de correlação/cointegração com métricas de topologia."""

    tickers: tuple[str, ...]
    diagnostics: SamplingDiagnostics
    correlation: np.ndarray
    pairs: tuple[PairResult, ...]
    graph: nx.Graph
    communities: dict[str, int]
    centrality: dict[str, float]
    modularity: float
    correlation_available: bool
    cointegration_available: bool


def _to_price(value: object) -> float | None:
    """Valida um preço como float, rejeitando ausentes e não positivos."""
    try:
        price = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if price > 0 and isfinite(price):
        return price
    return None


def _clean_series(observations: Iterable[tuple[date, object]]) -> dict[date, float]:
    """Mapeia datas a preços válidos, mantendo a última ocorrência."""
    cleaned: dict[date, float] = {}
    for data, valor in observations:
        price = _to_price(valor)
        if price is not None:
            cleaned[data] = price
    return cleaned


def align_series(series: SeriesMap) -> AlignedPrices:
    """Alinha as séries por interseção de datas (inner join).

    Tickers sem observações válidas são excluídos. O resultado contém
    apenas as datas presentes em todos os tickers remanescentes.
    """
    cleaned: dict[str, dict[date, float]] = {}
    for ticker, observations in series.items():
        prices = _clean_series(observations)
        if prices:
            cleaned[ticker] = prices
    if not cleaned:
        return AlignedPrices((), (), np.zeros((0, 0)))

    tickers = tuple(sorted(cleaned))
    common = set.intersection(*(set(prices) for prices in cleaned.values()))
    dates = tuple(sorted(common))
    if not dates:
        return AlignedPrices(tickers, (), np.zeros((len(tickers), 0)))

    matrix = np.array(
        [[cleaned[ticker][data] for data in dates] for ticker in tickers],
        dtype=float,
    )
    return AlignedPrices(tickers, dates, matrix)


def sampling_diagnostics(dates: Sequence[date]) -> SamplingDiagnostics:
    """Reporta n de observações, span e gaps (dias úteis) entre observações."""
    ordered = sorted(dates)
    total = len(ordered)
    if total == 0:
        return SamplingDiagnostics(0, 0, 0, 0.0, 0)
    span = (ordered[-1] - ordered[0]).days
    if total == 1:
        return SamplingDiagnostics(1, span, 0, 0.0, 0)
    gaps = [
        int(np.busday_count(ordered[i], ordered[i + 1]))
        for i in range(total - 1)
    ]
    return SamplingDiagnostics(
        total, span, min(gaps), float(np.median(gaps)), max(gaps),
    )


def compute_returns(prices: np.ndarray) -> np.ndarray:
    """Calcula retornos entre observações consecutivas da grade alinhada.

    Preços ausentes ou não positivos geram ``nan`` para a observação, sem
    interromper o cálculo dos demais tickers.
    """
    matrix = np.asarray(prices, dtype=float)
    n_tickers, n_obs = matrix.shape
    if n_obs < 2:
        return np.zeros((n_tickers, 0))
    prev = matrix[:, :-1]
    curr = matrix[:, 1:]
    valid = (prev > 0) & (curr > 0) & np.isfinite(prev) & np.isfinite(curr)
    returns = np.full((n_tickers, n_obs - 1), np.nan)
    returns[valid] = curr[valid] / prev[valid] - 1.0
    return returns


def correlation_matrix(returns: np.ndarray) -> np.ndarray:
    """Produz a matriz de correlação assinada, simétrica e de diagonal 1.

    Colunas com qualquer retorno inválido são descartadas para preservar a
    comparabilidade entre os pares. Coeficientes indefinidos viram zero.
    """
    matrix = np.asarray(returns, dtype=float)
    n_tickers = matrix.shape[0]
    if n_tickers == 0:
        return np.zeros((0, 0))
    if n_tickers == 1 or matrix.shape[1] < 2:
        return np.eye(n_tickers)
    valid = ~np.isnan(matrix).any(axis=0)
    data = matrix[:, valid]
    if data.shape[1] < 2:
        return np.eye(n_tickers)
    with np.errstate(all="ignore"):
        corr = np.corrcoef(data)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    corr = np.clip(corr, -1.0, 1.0)
    np.fill_diagonal(corr, 1.0)
    return corr


def mackinnon_critical(
    nobs: int, significance: float = COINT_SIGNIFICANCE
) -> float:
    """Valor crítico de MacKinnon (constante, 2 variáveis) para o ADF.

    Aplica a correção de amostra finita da superfície de resposta sobre os
    valores assintóticos.
    """
    coeffs = _MACKINNON_N2.get(significance)
    if coeffs is None:
        raise ValueError(f"significância não suportada: {significance}")
    inv = 1.0 / max(int(nobs), 1)
    a0, a1, a2, a3 = coeffs
    return a0 + a1 * inv + a2 * inv**2 + a3 * inv**3


def _max_lags(n_obs: int) -> int:
    """Número máximo de defasagens do ADF conforme a amostra."""
    if n_obs <= 0:
        return 0
    return min(MAX_LAGS, floor(12 * (n_obs / 100.0) ** 0.25))


def _design_matrix(
    spread: np.ndarray, diffs: np.ndarray, lag: int
) -> tuple[np.ndarray, np.ndarray]:
    """Monta a regressão do ADF para a defasagem informada."""
    n_obs = len(spread)
    dependent = diffs[lag:]
    columns = [np.ones(len(dependent)), spread[lag : n_obs - 1]]
    for i in range(1, lag + 1):
        columns.append(diffs[lag - i : n_obs - 1 - i])
    return np.column_stack(columns), dependent


def _ols_fit(
    design: np.ndarray, dependent: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Estima por mínimos quadrados e devolve coeficientes e resíduos."""
    beta, *_ = np.linalg.lstsq(design, dependent, rcond=None)
    return beta, dependent - design @ beta


def _tstat(beta: np.ndarray, resid: np.ndarray, design: np.ndarray) -> float | None:
    """t-stat do segundo coeficiente da regressão, se estimável."""
    dof = len(resid) - design.shape[1]
    if dof <= 0:
        return None
    sigma2 = float(resid @ resid) / dof
    xtx_inv = np.linalg.pinv(design.T @ design)
    variance = sigma2 * xtx_inv[1, 1]
    if not isfinite(variance) or variance <= 0:
        return None
    return float(beta[1] / np.sqrt(variance))


def _bic(resid: np.ndarray, n_params: int) -> float:
    """Critério de informação bayesiano da regressão."""
    n_obs = len(resid)
    sse = float(resid @ resid)
    if sse <= 0 or n_obs <= 0:
        return float("-inf")
    return n_obs * log(sse / n_obs) + n_params * log(n_obs)


def _adf_tstat(spread: np.ndarray) -> float | None:
    """t-stat do ADF com defasagem escolhida por BIC."""
    n_obs = len(spread)
    if n_obs < 4:
        return None
    diffs = np.diff(spread)
    best: tuple[float, float] | None = None
    for lag in range(_max_lags(n_obs) + 1):
        if n_obs - 1 - lag < lag + 3:
            continue
        design, dependent = _design_matrix(spread, diffs, lag)
        beta, resid = _ols_fit(design, dependent)
        tstat = _tstat(beta, resid, design)
        if tstat is None:
            continue
        bic = _bic(resid, design.shape[1])
        if best is None or bic < best[0]:
            best = (bic, tstat)
    return None if best is None else best[1]


def _half_life(spread: np.ndarray) -> float | None:
    """Meia-vida de reversão à média do spread, em número de observações."""
    diffs = np.diff(spread)
    lag = spread[:-1]
    if len(diffs) < 2:
        return None
    design = np.column_stack([np.ones(len(lag)), lag])
    beta, _ = _ols_fit(design, diffs)
    phi = 1.0 + float(beta[1])
    if 0.0 < phi < 1.0:
        return -log(2.0) / log(phi)
    return None


def engle_granger(
    dependent: Sequence[float], independent: Sequence[float]
) -> tuple[float | None, float | None]:
    """Testa cointegração de um par via Engle-Granger + ADF.

    Retorna a estatística do ADF e a meia-vida do spread. A direção da
    regressão é fixada pelo chamador. O resultado é um indício sob
    espaçamento irregular.
    """
    y = np.asarray(dependent, dtype=float)
    x = np.asarray(independent, dtype=float)
    if y.shape != x.shape or len(y) < 4:
        return None, None
    design = np.column_stack([np.ones(len(x)), x])
    beta, _ = _ols_fit(design, y)
    spread = y - design @ beta
    return _adf_tstat(spread), _half_life(spread)


def _index_pairs(n_tickers: int) -> Iterator[tuple[int, int]]:
    """Itera os pares de índices ``(i, j)`` com ``i < j``."""
    for i in range(n_tickers):
        for j in range(i + 1, n_tickers):
            yield i, j


def _pair_result(
    aligned: AlignedPrices,
    i: int,
    j: int,
    correlation: float,
    cointegration_available: bool,
    diagnostics: SamplingDiagnostics,
    significance: float,
) -> PairResult:
    """Avalia um par: correlação, cointegração e meia-vida."""
    adf_stat, half_life = engle_granger(aligned.prices[i], aligned.prices[j])
    cointegrated: bool | None = None
    if cointegration_available and adf_stat is not None:
        critical = mackinnon_critical(len(aligned.dates) - 1, significance)
        cointegrated = adf_stat < critical
    half_life_days: float | None = None
    if half_life is not None and diagnostics.gap_median > 0:
        half_life_days = half_life * diagnostics.gap_median
    return PairResult(
        ticker_a=aligned.tickers[i],
        ticker_b=aligned.tickers[j],
        correlation=float(correlation),
        cointegrated=cointegrated,
        adf_stat=adf_stat,
        half_life_obs=half_life,
        half_life_days=half_life_days,
    )


def _build_pairs(
    aligned: AlignedPrices,
    corr: np.ndarray,
    cointegration_available: bool,
    diagnostics: SamplingDiagnostics,
    significance: float,
) -> tuple[PairResult, ...]:
    """Avalia todos os pares de tickers alinhados."""
    return tuple(
        _pair_result(
            aligned, i, j, corr[i, j],
            cointegration_available, diagnostics, significance,
        )
        for i, j in _index_pairs(len(aligned.tickers))
    )


def _build_graph(
    tickers: Sequence[str], pairs: Sequence[PairResult], threshold: float
) -> nx.Graph:
    """Constrói o grafo com arestas filtradas por correlação ou cointegração."""
    graph = nx.Graph()
    graph.add_nodes_from(tickers)
    for pair in pairs:
        if abs(pair.correlation) > threshold or pair.cointegrated is True:
            graph.add_edge(
                pair.ticker_a,
                pair.ticker_b,
                correlation=pair.correlation,
                cointegrated=bool(pair.cointegrated),
            )
    return graph


def _communities(graph: nx.Graph) -> tuple[dict[str, int], float]:
    """Detecta comunidades e calcula a modularidade da partição."""
    if graph.number_of_edges() == 0:
        nodes = sorted(graph.nodes())
        return {node: indice for indice, node in enumerate(nodes)}, 0.0
    partitions = sorted(
        nx.community.greedy_modularity_communities(graph), key=min
    )
    mapping = {
        node: indice
        for indice, partition in enumerate(partitions)
        for node in partition
    }
    modularity = float(nx.community.modularity(graph, partitions))
    return mapping, modularity


def _analyze_pairs(
    aligned: AlignedPrices,
    correlation_available: bool,
    cointegration_available: bool,
    diagnostics: SamplingDiagnostics,
    significance: float,
) -> tuple[np.ndarray, tuple[PairResult, ...]]:
    """Calcula a matriz de correlação e os resultados de par, se possível."""
    n_tickers = len(aligned.tickers)
    if not correlation_available:
        corr = np.eye(n_tickers) if n_tickers else np.zeros((0, 0))
        return corr, ()
    corr = correlation_matrix(compute_returns(aligned.prices))
    pairs = _build_pairs(
        aligned, corr, cointegration_available, diagnostics, significance,
    )
    return corr, pairs


def analyze_network(
    series: SeriesMap,
    *,
    corr_threshold: float = DEFAULT_CORR_THRESHOLD,
    min_obs_corr: int = MIN_OBS_CORR,
    min_obs_coint: int = MIN_OBS_COINT,
    significance: float = COINT_SIGNIFICANCE,
) -> NetworkResult:
    """Analisa a rede de correlação/cointegração das séries informadas.

    Aplica os gates de densidade sem levantar erro: abaixo de ``min_obs_corr``
    a correlação fica indisponível; abaixo de ``min_obs_coint``, somente a
    cointegração fica indisponível.
    """
    aligned = align_series(series)
    diagnostics = sampling_diagnostics(aligned.dates)
    n_tickers = len(aligned.tickers)
    has_pair = n_tickers >= 2
    correlation_available = has_pair and diagnostics.n_observations >= min_obs_corr
    cointegration_available = has_pair and diagnostics.n_observations >= min_obs_coint

    corr, pairs = _analyze_pairs(
        aligned, correlation_available, cointegration_available,
        diagnostics, significance,
    )
    graph = _build_graph(aligned.tickers, pairs, corr_threshold)
    communities, modularity = _communities(graph)
    centrality = {
        node: float(valor)
        for node, valor in nx.degree_centrality(graph).items()
    }
    return NetworkResult(
        tickers=aligned.tickers,
        diagnostics=diagnostics,
        correlation=corr,
        pairs=pairs,
        graph=graph,
        communities=communities,
        centrality=centrality,
        modularity=modularity,
        correlation_available=correlation_available,
        cointegration_available=cointegration_available,
    )
