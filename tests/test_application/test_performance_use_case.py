from datetime import date
from decimal import Decimal

import pytest

from flowscope.application.performance import (
    AnalyzePerformanceUseCase,
    PerformanceBenchmark,
)
from flowscope.domain.fii.dividends import DividendoConsolidado
from flowscope.domain.index_history import IndexClose
from tests.support_calendar import FakeBusinessDayLookup

D1 = date(2026, 1, 5)
D2 = date(2026, 1, 6)
D3 = date(2026, 1, 9)


class FakeIndexHistory:
    def __init__(self, series):
        self._series = series
        self.calls = []

    def get_index_history(self, index, start, end):
        self.calls.append((index, start, end))
        return [
            IndexClose(momento, valor)
            for momento, valor in sorted(self._series.get(index, {}).items())
            if start <= momento <= end
        ]


class FakeDividends:
    def __init__(self, dividends):
        self._dividends = dividends
        self.calls = []

    def obter_dividendos(self, ticker, reference_date):
        self.calls.append((ticker, reference_date))
        return list(self._dividends.get(ticker, []))


def _daily(*pontos):
    return {"daily_data": [{"date": d, "last_price": p} for d, p in pontos]}


@pytest.fixture
def historico():
    return FakeIndexHistory({
        "IBOV": {D1: 100.0, D2: 110.0, D3: 121.0},
        "IFIX": {D1: 100.0, D2: 100.0, D3: 100.0},
        "IDIV": {D1: 100.0, D2: 100.0, D3: 100.0},
    })


@pytest.fixture
def calendario():
    return FakeBusinessDayLookup([])


class TestAnalyzePerformanceUseCase:
    def test_calcula_por_benchmark(self, historico, calendario):
        caso = AnalyzePerformanceUseCase(historico, business_day=calendario)
        resultado = caso.execute(
            {"PETR4": _daily((D1, 10.0), (D2, 11.0), (D3, 13.2))},
            {"PETR4": "ACAO"},
            D3,
        )
        assert set(resultado) == {"IBOV", "IDIV"}
        ibov = resultado["IBOV"]
        assert ibov.tickers[0].excess_pp == pytest.approx(11.0)

    def test_base_total_usa_proventos(self, historico, calendario):
        caso = AnalyzePerformanceUseCase(historico, business_day=calendario)
        resultado = caso.execute(
            {"HGLG11": _daily((D1, 10.0), (D3, 10.0))},
            {"HGLG11": "FII"},
            D3,
            dividends_by_ticker={
                "HGLG11": [
                    DividendoConsolidado(
                        data_base=D1, valor=Decimal("1"), fonte="B3"
                    )
                ]
            },
        )
        assert resultado["IFIX"].tickers[0].ticker_return == pytest.approx(0.1)

    def test_provider_de_dividendos_injetado(self, historico, calendario):
        provider = FakeDividends({
            "HGLG11": [DividendoConsolidado(D1, Decimal("1"), "B3")]
        })
        caso = AnalyzePerformanceUseCase(
            historico, dividends=provider, business_day=calendario
        )
        caso.execute(
            {"HGLG11": _daily((D1, 10.0), (D3, 10.0))},
            {"HGLG11": "FII"},
            D3,
        )
        assert provider.calls == [("HGLG11", D3)]

    def test_menos_de_duas_observacoes_fica_fora(self, historico, calendario):
        caso = AnalyzePerformanceUseCase(historico, business_day=calendario)
        resultado = caso.execute(
            {"PETR4": _daily((D1, 10.0))}, {"PETR4": "ACAO"}, D3
        )
        assert resultado["IBOV"].tickers == ()

    def test_serie_do_indice_indisponivel(self, calendario):
        caso = AnalyzePerformanceUseCase(
            FakeIndexHistory({"IFIX": {}}), business_day=calendario
        )
        resultado = caso.execute(
            {"HGLG11": _daily((D1, 10.0), (D2, 11.0))},
            {"HGLG11": "FII"},
            D3,
        )
        assert resultado["IFIX"] == PerformanceBenchmark(
            "IFIX", (), False, "total"
        )

    def test_sem_tickers_elegiveis(self, historico, calendario):
        caso = AnalyzePerformanceUseCase(historico, business_day=calendario)
        resultado = caso.execute({}, {}, D3)
        assert resultado == {}

    def test_falha_de_um_benchmark_nao_derruba_os_demais(self, calendario):
        class _HistoricoComFalha:
            def get_index_history(self, index, start, end):
                if index == "IBOV":
                    raise RuntimeError("falha na série")
                return [IndexClose(D1, Decimal("100")), IndexClose(D3, Decimal("100"))]

        caso = AnalyzePerformanceUseCase(
            _HistoricoComFalha(), business_day=calendario
        )
        resultado = caso.execute(
            {
                "HGLG11": _daily((D1, 10.0), (D3, 10.0)),
                "PETR4": _daily((D1, 10.0), (D3, 10.0)),
            },
            {"HGLG11": "FII", "PETR4": "ACAO"},
            D3,
            benchmarks=["IBOV", "IFIX"],
        )
        assert resultado["IBOV"].index_available is False
        assert resultado["IBOV"].tickers == ()
        assert resultado["IFIX"].index_available is True
