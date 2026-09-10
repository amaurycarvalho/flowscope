from datetime import date
from decimal import Decimal

from flowscope.domain.fii import (
    TIPO_RENDIMENTO,
    DividendoConsolidado,
    TendenciaDividendo,
    calcular_tendencia,
    calcular_ultimo_dividendo,
    calcular_ultimo_dividendo_consolidado,
    consolidar_dividendos,
    dividendos_12m,
    dividendos_de_proventos,
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


def _dividendo(valor: str, data_base: date | None, fonte: str = "B3") -> DividendoConsolidado:
    return DividendoConsolidado(
        data_base=data_base, valor=Decimal(valor), fonte=fonte
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
    def test_crescimento_quando_ultimo_maior(self):
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "1.00"),
            _provento(TIPO_RENDIMENTO, date(2026, 7, 10), "1.06"),
        ]
        resultado = calcular_ultimo_dividendo(proventos)
        assert resultado.tendencia is TendenciaDividendo.CRESCIMENTO

    def test_crescimento_para_diferenca_minima(self):
        dividendos = [
            _dividendo("1.00", date(2026, 1, 15)),
            _dividendo("1.01", date(2026, 7, 10)),
        ]
        assert calcular_tendencia(dividendos) is TendenciaDividendo.CRESCIMENTO

    def test_reducao_quando_ultimo_menor(self):
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "1.00"),
            _provento(TIPO_RENDIMENTO, date(2026, 7, 10), "0.94"),
        ]
        resultado = calcular_ultimo_dividendo(proventos)
        assert resultado.tendencia is TendenciaDividendo.REDUCAO

    def test_neutro_quando_igual(self):
        dividendos = [
            _dividendo("1.00", date(2026, 1, 15)),
            _dividendo("1.00", date(2026, 7, 10)),
        ]
        assert calcular_tendencia(dividendos) is TendenciaDividendo.NEUTRO

    def test_na_sem_dividendo_anterior(self):
        resultado = calcular_ultimo_dividendo(
            [_provento(TIPO_RENDIMENTO, date(2026, 7, 10), "0.55")]
        )
        assert resultado.tendencia is TendenciaDividendo.N_A


class TestConsolidacao:
    def test_deduplica_por_data_base_e_valor(self):
        b3 = [_dividendo("1.00", date(2026, 1, 15), "B3")]
        cvm = [
            _dividendo("1.00", date(2026, 1, 15), "CVM"),
            _dividendo("0.50", date(2026, 2, 15), "CVM"),
        ]
        consolidados = consolidar_dividendos(b3, cvm)
        assert len(consolidados) == 2
        assert [d.valor for d in consolidados] == [Decimal("1.00"), Decimal("0.50")]

    def test_fonte_ausente_em_b3_preenchida_pela_cvm(self):
        b3: list[DividendoConsolidado] = []
        cvm = [_dividendo("0.50", date(2026, 2, 15), "CVM")]
        consolidados = consolidar_dividendos(b3, cvm)
        assert len(consolidados) == 1
        assert consolidados[0].fonte == "CVM"

    def test_origem_preservada(self):
        b3 = [_dividendo("1.00", date(2026, 1, 15), "B3")]
        cvm = [_dividendo("0.50", date(2026, 2, 15), "CVM")]
        fundamentus = [_dividendo("0.55", date(2026, 3, 15), "FUNDAMENTUS")]
        consolidados = consolidar_dividendos(b3, cvm, fundamentus)
        assert [d.fonte for d in consolidados] == ["B3", "CVM", "FUNDAMENTUS"]

    def test_resultado_ordenado_por_data_base(self):
        cvm = [
            _dividendo("0.55", date(2026, 3, 15), "CVM"),
            _dividendo("0.50", date(2026, 2, 15), "CVM"),
        ]
        consolidados = consolidar_dividendos(cvm)
        assert [d.data_base for d in consolidados] == [
            date(2026, 2, 15),
            date(2026, 3, 15),
        ]

    def test_ultimo_dividendo_consolidado_com_tendencia(self):
        consolidados = consolidar_dividendos(
            [_dividendo("0.50", date(2026, 1, 15), "B3")],
            [_dividendo("0.60", date(2026, 2, 15), "CVM")],
        )
        resultado = calcular_ultimo_dividendo_consolidado(consolidados)
        assert resultado.valor == Decimal("0.60")
        assert resultado.valor_anterior == Decimal("0.50")
        assert resultado.tendencia is TendenciaDividendo.CRESCIMENTO

    def test_dividendos_de_proventos_ignora_amortizacao_e_sem_data(self):
        proventos = [
            _provento(TIPO_RENDIMENTO, date(2026, 1, 15), "0.50"),
            _provento("Amortização", date(2026, 2, 15), "2.00"),
        ]
        dividendos = dividendos_de_proventos(proventos, "B3")
        assert len(dividendos) == 1
        assert dividendos[0].fonte == "B3"


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
