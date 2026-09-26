"""Testes puros da preparação de dados do gráfico de VWAP."""

from datetime import date

from flowscope.application.vwap import (
    DadosVwap,
    collect_ticker_data,
    compute_violin_shapes,
    estimate_bucket_size,
    to_pct,
)

D1 = date(2025, 1, 1)
D2 = date(2025, 1, 2)


def _dia(
    dt: date,
    avg: float,
    minimo: float,
    maximo: float,
    ultimo: float,
    qty: int,
) -> dict:
    return {
        "date": dt,
        "avg_price": avg,
        "min_price": minimo,
        "max_price": maximo,
        "last_price": ultimo,
        "fin_instr_qty": qty,
    }


class TestToPct:
    def test_acima_e_abaixo_do_vwap(self):
        assert to_pct(105.0, 100.0) == 5.0
        assert to_pct(95.0, 100.0) == -5.0


class TestCollectTickerData:
    def test_series_e_marcos_por_ativo(self):
        data = {
            "PETR4": {
                "vwap": {"period_vwap": 100},
                "daily_data": [
                    _dia(D1, 105.0, 100.0, 110.0, 108.0, 10),
                    _dia(D2, 95.0, 90.0, 100.0, 92.0, 20),
                ],
            }
        }
        dados = collect_ticker_data(data)
        assert isinstance(dados, DadosVwap)
        assert dados.tickers == ("PETR4",)
        assert dados.vwap_values_abs == (100.0,)
        assert dados.violin_data == (((5.0, -5.0), (10, 20)),)
        assert dados.min_prices_pct == (-10.0,)
        assert dados.max_prices_pct == (10.0,)
        assert dados.last_prices_pct == (-8.0,)

    def test_ignora_ticker_sem_dados_diarios(self):
        dados = collect_ticker_data(
            {"X": {"vwap": {"period_vwap": 100}, "daily_data": []}}
        )
        assert dados.tickers == ()

    def test_ignora_vwap_ausente_ou_zero(self):
        dia = _dia(D1, 105.0, 100.0, 110.0, 108.0, 10)
        assert collect_ticker_data(
            {"X": {"daily_data": [dia]}}
        ).tickers == ()
        assert collect_ticker_data(
            {"X": {"vwap": None, "daily_data": [dia]}}
        ).tickers == ()
        assert collect_ticker_data(
            {"X": {"vwap": {"period_vwap": 0}, "daily_data": [dia]}}
        ).tickers == ()

    def test_sem_dados_retorna_vazio(self):
        assert collect_ticker_data({}).tickers == ()


class TestEstimateBucketSize:
    def test_vazio(self):
        assert estimate_bucket_size([]) == 0.01

    def test_faixas_de_intervalo(self):
        assert estimate_bucket_size([((0.0, 0.3), (1, 1))]) == 0.01
        assert estimate_bucket_size([((0.0, 1.0), (1, 1))]) == 0.05
        assert estimate_bucket_size([((0.0, 5.0), (1, 1))]) == 0.25
        assert estimate_bucket_size([((0.0, 20.0), (1, 1))]) == 0.50


class TestComputeViolinShapes:
    def test_acumula_volumes_por_bucket(self):
        formas = compute_violin_shapes([((0.0, 0.0, 0.05, 0.05), (10, 5, 3, 7))])
        assert formas.bucket_size == 0.01
        assert formas.max_vol == 15.0
        assert formas.shapes == (((0.0, 0.05), (15.0, 10.0)),)

    def test_sem_dados_retorna_vazio(self):
        formas = compute_violin_shapes([])
        assert formas.shapes == ()
        assert formas.max_vol == 1
        assert formas.bucket_size == 0.01
