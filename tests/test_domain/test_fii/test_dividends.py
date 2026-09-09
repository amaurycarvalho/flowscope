from datetime import date
from decimal import Decimal

from flowscope.domain.fii import (
    BANDA_PADRAO,
    TIPO_RENDIMENTO,
    TendenciaDividendo,
    calcular_tendencia,
    calcular_ultimo_dividendo,
    dividendos_12m,
)
from flowscope.domain.structured import ISIN, Provento, ValorProvento

_ISIN = "BR0000000000"


def _provento(
    tipo: str,
    data_base: date,
    valor: str,
    data_pagamento: date | None = None,
) -> Provento:
    return Provento(
        codigo_isin=ISIN(_ISIN),
        codigo_negociacao="KNRI11",
        tipo=tipo,
        data_base=data_base,
        valor_por_unidade=ValorProvento(Decimal(valor)),
        data_pagamento=data_pagamento or data_base,
        periodo_referencia="",
        isento_ir=True,
    )


class TestUltimaDataCom:
    def test_data_base_do_rendimento_mais_recente(self):
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "0.50"),
            _provento(TIPO_RENDIMENTO, date(2026, 7, 10), "0.55"),
        ]
        resultado = calcular_ultimo_dividendo(proventos)
        assert resultado.data_com == date(2026, 7, 10)

    def test_sem_rendimento_data_com_na(self):
        resultado = calcular_ultimo_dividendo([])
        assert resultado.data_com is None
        assert resultado.valor is None
        assert resultado.tendencia is TendenciaDividendo.N_A


class TestUltimoDividendo:
    def test_ignora_amortizacao_mais_recente(self):
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "0.50"),
            _provento("Amortização", date(2026, 6, 20), "1.00"),
            _provento(TIPO_RENDIMENTO, date(2026, 7, 10), "0.55"),
        ]
        resultado = calcular_ultimo_dividendo(proventos)
        assert resultado.valor == Decimal("0.55")
        assert resultado.data_com == date(2026, 7, 10)

    def test_apenas_amortizacao_resulta_na(self):
        proventos = [
            _provento("Amortização", date(2026, 6, 20), "1.00"),
            _provento("Amortização", date(2026, 7, 20), "0.40"),
        ]
        resultado = calcular_ultimo_dividendo(proventos)
        assert resultado.valor is None
        assert resultado.data_com is None

    def test_respeita_data_de_referencia(self):
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "0.50"),
            _provento(TIPO_RENDIMENTO, date(2026, 9, 10), "0.60"),
        ]
        resultado = calcular_ultimo_dividendo(proventos, reference_date=date(2026, 8, 1))
        assert resultado.valor == Decimal("0.50")

    def test_amortizacao_intermediaria_nao_influencia_anterior(self):
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "0.50"),
            _provento(TIPO_RENDIMENTO, date(2026, 5, 10), "0.40"),
            _provento("Amortização", date(2026, 6, 20), "2.00"),
            _provento(TIPO_RENDIMENTO, date(2026, 8, 10), "0.60"),
        ]
        resultado = calcular_ultimo_dividendo(proventos)
        assert resultado.valor == Decimal("0.60")
        assert resultado.valor_anterior == Decimal("0.40")


class TestTendenciaDividendo:
    def test_subindo_acima_da_banda(self):
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "1.00"),
            _provento(TIPO_RENDIMENTO, date(2026, 7, 10), "1.06"),
        ]
        resultado = calcular_ultimo_dividendo(proventos)
        assert resultado.tendencia is TendenciaDividendo.SUBINDO

    def test_subindo_no_limite_superior(self):
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "1.00"),
            _provento(TIPO_RENDIMENTO, date(2026, 7, 10), "1.05"),
        ]
        assert calcular_tendencia(proventos) is TendenciaDividendo.SUBINDO

    def test_caindo_abaixo_da_banda(self):
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "1.00"),
            _provento(TIPO_RENDIMENTO, date(2026, 7, 10), "0.94"),
        ]
        resultado = calcular_ultimo_dividendo(proventos)
        assert resultado.tendencia is TendenciaDividendo.CAINDO

    def test_manteve_dentro_da_banda(self):
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "1.00"),
            _provento(TIPO_RENDIMENTO, date(2026, 7, 10), "1.02"),
        ]
        resultado = calcular_ultimo_dividendo(proventos)
        assert resultado.tendencia is TendenciaDividendo.MANTEVE

    def test_na_sem_dividendo_anterior(self):
        resultado = calcular_ultimo_dividendo(
            [_provento(TIPO_RENDIMENTO, date(2026, 7, 10), "0.55")]
        )
        assert resultado.tendencia is TendenciaDividendo.N_A

    def test_banda_configuravel(self):
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "1.00"),
            _provento(TIPO_RENDIMENTO, date(2026, 7, 10), "1.10"),
        ]
        assert BANDA_PADRAO == Decimal("0.05")
        assert calcular_tendencia(proventos, banda=Decimal("0.20")) is TendenciaDividendo.MANTEVE
        assert calcular_tendencia(proventos, banda=Decimal("0.05")) is TendenciaDividendo.SUBINDO


class TestDividendos12m:
    def test_soma_rendimentos_dentro_da_janela(self):
        reference_date = date(2026, 9, 1)
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "0.50", date(2026, 2, 1)),
            _provento(TIPO_RENDIMENTO, date(2026, 7, 10), "0.55", date(2026, 8, 1)),
            _provento(TIPO_RENDIMENTO, date(2025, 8, 1), "0.30", date(2025, 9, 1)),
            _provento("Amortização", date(2026, 6, 20), "2.00", date(2026, 7, 1)),
        ]
        assert dividendos_12m(proventos, reference_date) == Decimal("1.05")

    def test_exclui_pagamento_fora_da_janela(self):
        reference_date = date(2026, 9, 1)
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2025, 8, 1), "0.30", date(2025, 8, 20)),
        ]
        assert dividendos_12m(proventos, reference_date) == Decimal("0")
