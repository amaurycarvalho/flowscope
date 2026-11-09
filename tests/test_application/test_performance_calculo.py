from datetime import date
from decimal import Decimal

import pytest

from flowscope.application.performance.calculo import (
    alinhar_datas,
    derivar_data_ex,
    detectar_evento_societario,
    montar_ticker,
    proventos_por_data_ex,
    retorno_preco,
    retorno_total,
)
from flowscope.domain.fii.dividends import DividendoConsolidado
from tests.support_calendar import FakeBusinessDayLookup

D1 = date(2026, 1, 5)
D2 = date(2026, 1, 6)
D3 = date(2026, 1, 9)


@pytest.fixture
def calendario() -> FakeBusinessDayLookup:
    return FakeBusinessDayLookup([date(2026, 1, 7), date(2026, 1, 8)])


class TestRetornoPreco:
    def test_duas_observacoes(self):
        assert retorno_preco({D1: 10.0, D2: 11.0}, [D1, D2]) == pytest.approx(0.1)

    def test_observacoes_insuficientes(self):
        assert retorno_preco({D1: 10.0}, [D1]) is None

    def test_preco_inicial_invalido(self):
        assert retorno_preco({D1: 0.0, D2: 1.0}, [D1, D2]) is None


class TestAlinhamento:
    def test_intersecao_ordenada(self):
        ticker = {D1: 1.0, D2: 2.0, D3: 3.0}
        indice = {D2: 1.0, D3: 1.0, date(2026, 1, 12): 1.0}
        assert alinhar_datas(ticker, indice) == [D2, D3]

    def test_sem_datas_comuns(self):
        assert alinhar_datas({D1: 1.0}, {D2: 1.0}) == []


class TestDataEx:
    def test_proximo_dia_util(self, calendario):
        assert derivar_data_ex(D1, calendario) == D2

    def test_pula_fim_de_semana(self):
        calendario = FakeBusinessDayLookup([])
        assert derivar_data_ex(date(2026, 1, 2), calendario) == date(2026, 1, 5)

    def test_pula_feriado(self, calendario):
        assert derivar_data_ex(D2, calendario) == D3


class TestRetornoTotal:
    def test_provento_dentro_do_periodo(self, calendario):
        proventos = proventos_por_data_ex(
            [DividendoConsolidado(data_base=D1, valor=Decimal("1"), fonte="B3")],
            calendario,
        )
        resultado = retorno_total({D1: 10.0, D2: 10.0, D3: 11.0}, [D1, D2, D3], proventos)
        assert resultado == pytest.approx(0.21)

    def test_provento_atribuido_a_observacao_seguinte(self, calendario):
        proventos = proventos_por_data_ex(
            [DividendoConsolidado(data_base=D2, valor=Decimal("1"), fonte="B3")],
            calendario,
        )
        resultado = retorno_total({D1: 10.0, D2: 10.0, D3: 11.0}, [D1, D2, D3], proventos)
        assert resultado == pytest.approx(0.2)

    def test_provento_fora_do_periodo(self, calendario):
        proventos = proventos_por_data_ex(
            [DividendoConsolidado(data_base=D3, valor=Decimal("1"), fonte="B3")],
            calendario,
        )
        resultado = retorno_total({D1: 10.0, D2: 10.0, D3: 11.0}, [D1, D2, D3], proventos)
        assert resultado == pytest.approx(0.1)

    def test_multiplos_proventos_no_mesmo_dia(self, calendario):
        proventos = proventos_por_data_ex(
            [
                DividendoConsolidado(data_base=D1, valor=Decimal("1"), fonte="B3"),
                DividendoConsolidado(data_base=D1, valor=Decimal("0.5"), fonte="CVM"),
            ],
            calendario,
        )
        resultado = retorno_total({D1: 10.0, D2: 10.0}, [D1, D2], proventos)
        assert resultado == pytest.approx(0.15)

    def test_sem_provento_coincide_com_preco(self, calendario):
        resultado = retorno_total({D1: 10.0, D2: 11.0}, [D1, D2], {})
        assert resultado == pytest.approx(0.1)


class TestEventoSocietario:
    @pytest.mark.parametrize(
        ("preco_final", "esperado"),
        [
            (5.0, True),   # split 1:2
            (20.0, True),  # grupamento 2:1
            (10.5, False),  # movimento normal
            (10.6, False),
        ],
    )
    def test_salto(self, preco_final, esperado):
        ticker = {D1: 10.0, D2: 10.0, D3: preco_final}
        indice = {D1: 100.0, D2: 100.0, D3: 100.0}
        assert detectar_evento_societario(ticker, indice, [D1, D2, D3]) is esperado

    def test_preco_anterior_invalido_nao_sinaliza(self):
        ticker = {D1: 0.0, D2: 10.0}
        indice = {D1: 100.0, D2: 100.0}
        assert detectar_evento_societario(ticker, indice, [D1, D2]) is False


class TestMontarTicker:
    def test_excesso_em_pontos_percentuais(self):
        ticker = {D1: 10.0, D2: 12.0}
        indice = {D1: 100.0, D2: 110.0}
        resultado = montar_ticker("PETR4", ticker, indice, {}, "price")
        assert resultado is not None
        assert resultado.ticker_return == pytest.approx(0.2)
        assert resultado.index_return == pytest.approx(0.1)
        assert resultado.excess_pp == pytest.approx(10.0)
        assert resultado.observations == 2

    def test_menos_de_duas_datas_retorna_none(self):
        assert montar_ticker("PETR4", {D1: 10.0}, {D1: 100.0}, {}, "price") is None

    def test_base_total_incorpora_proventos(self, calendario):
        proventos = proventos_por_data_ex(
            [DividendoConsolidado(data_base=D1, valor=Decimal("1"), fonte="B3")],
            calendario,
        )
        resultado = montar_ticker(
            "HGLG11", {D1: 10.0, D2: 10.0}, {D1: 100.0, D2: 100.0}, proventos, "total"
        )
        assert resultado is not None
        assert resultado.ticker_return == pytest.approx(0.1)
