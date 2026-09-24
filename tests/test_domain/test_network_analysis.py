"""Testes do núcleo de análise de rede (correlação e cointegração)."""

from datetime import date, timedelta

import numpy as np
import pytest

from flowscope.domain import network_analysis as na

START = date(2025, 1, 6)


def _business_days(n: int) -> list[date]:
    """Gera ``n`` dias úteis consecutivos a partir de uma segunda-feira."""
    dias: list[date] = []
    atual = START
    while len(dias) < n:
        if atual.weekday() < 5:
            dias.append(atual)
        atual += timedelta(days=1)
    return dias


def _random_walk(rng: np.random.Generator, n: int, inicio: float = 50.0) -> np.ndarray:
    return inicio + np.cumsum(rng.normal(size=n))


def _ruido_estacionario(rng: np.random.Generator, n: int, phi: float = 0.5) -> np.ndarray:
    ruido = np.zeros(n)
    for t in range(1, n):
        ruido[t] = phi * ruido[t - 1] + rng.normal(scale=0.3)
    return ruido


def _series(dados: dict[str, np.ndarray], datas: list[date]) -> dict:
    return {
        ticker: list(zip(datas, valores.tolist()))
        for ticker, valores in dados.items()
    }


class TestAlignSeries:
    def test_intersecao_de_datas(self):
        d = _business_days(4)
        series = {
            "AAA3": [(d[0], 1.0), (d[1], 2.0), (d[2], 3.0)],
            "BBB3": [(d[1], 10.0), (d[2], 20.0), (d[3], 30.0)],
        }
        aligned = na.align_series(series)
        assert aligned.dates == (d[1], d[2])
        assert aligned.tickers == ("AAA3", "BBB3")
        assert aligned.prices.tolist() == [[2.0, 3.0], [10.0, 20.0]]

    def test_ticker_sem_dados_excluido(self):
        d = _business_days(3)
        series = {
            "AAA3": [(d[0], 1.0), (d[1], 2.0), (d[2], 3.0)],
            "ZZZ9": [],
        }
        aligned = na.align_series(series)
        assert aligned.tickers == ("AAA3",)
        assert "ZZZ9" not in aligned.tickers

    def test_preco_ausente_ou_nao_positivo_descartado(self):
        d = _business_days(3)
        series = {"AAA3": [(d[0], 1.0), (d[1], 0.0), (d[2], 3.0)]}
        aligned = na.align_series(series)
        assert aligned.dates == (d[0], d[2])

    def test_series_vazia(self):
        aligned = na.align_series({})
        assert aligned.tickers == ()
        assert aligned.dates == ()
        assert aligned.n_observations == 0

    def test_datas_sem_intersecao(self):
        d0 = _business_days(2)
        d1 = [d + timedelta(days=30) for d in d0]
        series = {"AAA3": [(x, 1.0) for x in d0], "BBB3": [(x, 2.0) for x in d1]}
        aligned = na.align_series(series)
        assert aligned.tickers == ("AAA3", "BBB3")
        assert aligned.dates == ()
        assert aligned.prices.shape == (2, 0)


class TestSamplingDiagnostics:
    def test_sem_observacoes(self):
        diag = na.sampling_diagnostics([])
        assert diag.n_observations == 0
        assert diag.span_days == 0

    def test_uma_observacao(self):
        diag = na.sampling_diagnostics([START])
        assert diag.n_observations == 1
        assert diag.span_days == 0
        assert diag.gap_max == 0

    def test_gaps_em_dias_uteis(self):
        dias = _business_days(5)
        diag = na.sampling_diagnostics(dias)
        assert diag.n_observations == 5
        assert diag.gap_min == 1
        assert diag.gap_median == 1.0
        assert diag.gap_max == 1
        assert diag.span_days == (dias[-1] - dias[0]).days

    def test_gap_de_fim_de_semana(self):
        sexta = date(2025, 1, 10)
        segunda = date(2025, 1, 13)
        diag = na.sampling_diagnostics([sexta, segunda])
        assert diag.gap_max == 1


class TestComputeReturns:
    def test_retornos_consecutivos(self):
        prices = np.array([[100.0, 110.0, 99.0]])
        returns = na.compute_returns(prices)
        assert returns.shape == (1, 2)
        assert returns[0, 0] == pytest.approx(0.10)
        assert returns[0, 1] == pytest.approx(-0.10)

    def test_preco_ausente_gera_nan(self):
        prices = np.array([[100.0, 0.0, 120.0]])
        returns = na.compute_returns(prices)
        assert np.isnan(returns[0, 0])
        assert np.isnan(returns[0, 1])

    def test_grade_curta(self):
        returns = na.compute_returns(np.array([[100.0]]))
        assert returns.shape == (1, 0)


class TestCorrelationMatrix:
    def test_simetrica_e_diagonal_unitaria(self):
        rng = np.random.default_rng(1)
        data = rng.normal(size=(4, 50))
        corr = na.correlation_matrix(data)
        assert np.allclose(corr, corr.T)
        assert np.allclose(np.diag(corr), 1.0)
        assert corr.min() >= -1.0 and corr.max() <= 1.0

    def test_sinal_preservado(self):
        base = np.arange(50, dtype=float)
        data = np.vstack([base, -base, base[::-1]])
        corr = na.correlation_matrix(data)
        assert corr[0, 1] < 0
        assert corr[0, 2] < 0
        assert corr[1, 2] > 0

    def test_coluna_com_nan_descartada(self):
        base = np.arange(50, dtype=float)
        data = np.vstack([base, base * 2.0])
        data[0, 5] = np.nan
        corr = na.correlation_matrix(data)
        assert not np.isnan(corr).any()
        assert np.allclose(np.diag(corr), 1.0)

    def test_colunas_validas_insuficientes(self):
        data = np.ones((2, 5))
        data[0, :4] = np.nan
        corr = na.correlation_matrix(data)
        assert np.allclose(corr, np.eye(2))

    def test_ticker_unico(self):
        corr = na.correlation_matrix(np.zeros((1, 10)))
        assert corr.shape == (1, 1)
        assert corr[0, 0] == 1.0

    def test_sem_tickers(self):
        corr = na.correlation_matrix(np.zeros((0, 0)))
        assert corr.shape == (0, 0)


class TestHelpers:
    def test_to_price_rejeita_invalidos(self):
        assert na._to_price("abc") is None
        assert na._to_price(None) is None
        assert na._to_price(0) is None
        assert na._to_price(float("inf")) is None
        assert na._to_price("10.5") == 10.5

    def test_max_lags(self):
        assert na._max_lags(0) == 0
        assert na._max_lags(-5) == 0
        assert na._max_lags(1000) == na.MAX_LAGS

    def test_tstat_dof_nao_positivo(self):
        design = np.ones((2, 3))
        assert na._tstat(np.zeros(3), np.zeros(2), design) is None

    def test_tstat_variancia_nula(self):
        design = np.column_stack([np.ones(10), np.arange(10.0)])
        assert na._tstat(np.array([0.0, 1.0]), np.zeros(10), design) is None

    def test_bic_sse_zero(self):
        assert na._bic(np.zeros(5), 2) == float("-inf")

    def test_adf_curto(self):
        assert na._adf_tstat(np.array([1.0, 2.0, 3.0])) is None

    def test_adf_spread_constante(self):
        assert na._adf_tstat(np.full(50, 5.0)) is None

    def test_correlation_todas_nan(self):
        corr = na.correlation_matrix(np.full((2, 10), np.nan))
        assert np.allclose(corr, np.eye(2))


class TestMackinnonCritical:
    def test_valor_assintotico_aproximado(self):
        assert na.mackinnon_critical(1_000_000) == pytest.approx(-3.3361, abs=1e-3)

    def test_correcao_de_amostra_finita(self):
        pequeno = na.mackinnon_critical(40)
        grande = na.mackinnon_critical(10_000)
        assert pequeno < grande < -3.3

    def test_significancias_disponiveis(self):
        assert na.mackinnon_critical(100, 0.01) < na.mackinnon_critical(100, 0.05)
        assert na.mackinnon_critical(100, 0.05) < na.mackinnon_critical(100, 0.10)

    def test_significancia_nao_suportada(self):
        with pytest.raises(ValueError):
            na.mackinnon_critical(100, 0.02)


class TestEngleGranger:
    def test_par_cointegrado(self):
        rng = np.random.default_rng(7)
        n = 80
        x = _random_walk(rng, n)
        y = 2.0 * x + _ruido_estacionario(rng, n)
        adf, half_life = na.engle_granger(y, x)
        assert adf is not None
        assert adf < na.mackinnon_critical(n - 1)
        assert half_life is not None and half_life > 0

    def test_par_independente(self):
        rng = np.random.default_rng(11)
        n = 80
        x = _random_walk(rng, n)
        y = _random_walk(rng, n)
        adf, _ = na.engle_granger(y, x)
        assert adf is None or adf > na.mackinnon_critical(n - 1)

    def test_serie_curta_retorna_none(self):
        adf, half_life = na.engle_granger([1.0, 2.0], [1.0, 2.0])
        assert adf is None
        assert half_life is None

    def test_dimensoes_diferentes_retorna_none(self):
        adf, half_life = na.engle_granger([1.0, 2.0, 3.0], [1.0, 2.0])
        assert adf is None
        assert half_life is None

    def test_direcao_e_deterministica(self):
        rng = np.random.default_rng(3)
        n = 60
        x = _random_walk(rng, n)
        y = 1.5 * x + _ruido_estacionario(rng, n)
        assert na.engle_granger(y, x) == na.engle_granger(y, x)


class TestHalfLife:
    def test_spread_com_reversao(self):
        t = np.arange(60)
        spread = 0.6**t
        half_life = na._half_life(spread)
        assert half_life is not None
        assert half_life == pytest.approx(np.log(2) / -np.log(0.6), rel=1e-6)

    def test_spread_sem_reversao_explosivo(self):
        spread = 1.05 ** np.arange(40)
        assert na._half_life(spread) is None

    def test_spread_muito_curto(self):
        assert na._half_life(np.array([1.0, 2.0])) is None


class TestEdgeFilter:
    def test_aresta_por_correlacao(self):
        graph = na._build_graph(
            ("AAA3", "BBB3"),
            (na.PairResult("AAA3", "BBB3", 0.8, False),),
            threshold=0.5,
        )
        assert graph.has_edge("AAA3", "BBB3")

    def test_aresta_por_cointegracao_abaixo_do_limiar(self):
        graph = na._build_graph(
            ("AAA3", "BBB3"),
            (na.PairResult("AAA3", "BBB3", 0.1, True),),
            threshold=0.5,
        )
        assert graph.has_edge("AAA3", "BBB3")
        assert graph["AAA3"]["BBB3"]["cointegrated"] is True

    def test_sem_aresta_abaixo_do_limiar(self):
        graph = na._build_graph(
            ("AAA3", "BBB3"),
            (na.PairResult("AAA3", "BBB3", 0.2, False),),
            threshold=0.5,
        )
        assert not graph.has_edge("AAA3", "BBB3")
        assert set(graph.nodes()) == {"AAA3", "BBB3"}


class TestAnalyzeNetworkDensidade:
    def test_menos_de_30_observacoes(self):
        rng = np.random.default_rng(5)
        datas = _business_days(20)
        resultado = na.analyze_network(
            _series({"AAA3": _random_walk(rng, 20), "BBB3": _random_walk(rng, 20)}, datas)
        )
        assert resultado.correlation_available is False
        assert resultado.cointegration_available is False
        assert resultado.pairs == ()
        assert resultado.graph.number_of_edges() == 0

    def test_entre_30_e_39_apenas_correlacao(self):
        rng = np.random.default_rng(5)
        datas = _business_days(35)
        resultado = na.analyze_network(
            _series({"AAA3": _random_walk(rng, 35), "BBB3": _random_walk(rng, 35)}, datas)
        )
        assert resultado.correlation_available is True
        assert resultado.cointegration_available is False
        assert len(resultado.pairs) == 1
        assert resultado.pairs[0].cointegrated is None
        assert resultado.pairs[0].adf_stat is not None

    def test_40_ou_mais_ambos_disponiveis(self):
        rng = np.random.default_rng(5)
        datas = _business_days(45)
        resultado = na.analyze_network(
            _series({"AAA3": _random_walk(rng, 45), "BBB3": _random_walk(rng, 45)}, datas)
        )
        assert resultado.correlation_available is True
        assert resultado.cointegration_available is True
        assert resultado.pairs[0].cointegrated in (True, False)

    def test_gates_customizados(self):
        rng = np.random.default_rng(5)
        datas = _business_days(10)
        resultado = na.analyze_network(
            _series({"AAA3": _random_walk(rng, 10), "BBB3": _random_walk(rng, 10)}, datas),
            min_obs_corr=5,
            min_obs_coint=8,
        )
        assert resultado.correlation_available is True
        assert resultado.cointegration_available is True


class TestAnalyzeNetworkGrafo:
    def _dados(self) -> dict:
        rng = np.random.default_rng(21)
        n = 60
        datas = _business_days(n)
        base = _random_walk(rng, n)
        series = {}
        for indice, ticker in enumerate(["AAA3", "BBB3", "CCC3", "DDD3"]):
            if indice < 2:
                valores = base + _ruido_estacionario(rng, n)
            else:
                valores = _random_walk(rng, n)
            series[ticker] = list(zip(datas, valores.tolist()))
        return series

    def test_nos_e_arestas(self):
        resultado = na.analyze_network(self._dados())
        assert set(resultado.graph.nodes()) == {"AAA3", "BBB3", "CCC3", "DDD3"}
        for origem, destino, attrs in resultado.graph.edges(data=True):
            assert "correlation" in attrs
            assert "cointegrated" in attrs
            assert (
                abs(attrs["correlation"]) > na.DEFAULT_CORR_THRESHOLD
                or attrs["cointegrated"]
            )

    def test_comunidades_centralidade_modularidade(self):
        resultado = na.analyze_network(self._dados())
        assert set(resultado.communities) == set(resultado.graph.nodes())
        assert set(resultado.centrality) == set(resultado.graph.nodes())
        assert isinstance(resultado.modularity, float)

    def test_determinismo(self):
        series = self._dados()
        primeiro = na.analyze_network(series)
        segundo = na.analyze_network(series)
        assert primeiro.communities == segundo.communities
        assert primeiro.modularity == segundo.modularity
        assert primeiro.pairs == segundo.pairs
        assert list(primeiro.graph.edges()) == list(segundo.graph.edges())

    def test_grafo_sem_arestas_tem_comunidades_unitarias(self):
        import networkx as nx

        grafo = nx.Graph()
        grafo.add_nodes_from(["BBB3", "AAA3"])
        comunidades, modularidade = na._communities(grafo)
        assert comunidades == {"AAA3": 0, "BBB3": 1}
        assert modularidade == 0.0

    def test_ticker_unico_nao_gera_par(self):
        datas = _business_days(40)
        series = {"AAA3": list(zip(datas, np.arange(40, dtype=float).tolist()))}
        resultado = na.analyze_network(series)
        assert resultado.correlation_available is False
        assert resultado.tickers == ("AAA3",)
        assert resultado.pairs == ()
