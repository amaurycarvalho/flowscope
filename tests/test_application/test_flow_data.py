"""Testes puros das métricas e do resumo do fluxo financeiro."""

from decimal import Decimal

from flowscope.application.flow import (
    build_session_metrics,
    close_position_part,
    conviction_part,
    dominance_part,
    flow_intensity_part,
    generate_summary,
)
from flowscope.domain.strategies.classifiers import MoneyFlowClassification


def _classification(score: int) -> MoneyFlowClassification:
    return MoneyFlowClassification("Rótulo", "Curto", "#000000", score)


class TestBuildSessionMetrics:
    def test_extrai_metricas_do_ultimo_pregao(self):
        daily = [
            {"date": "d1", "fin_vol": 1_000_000},
            {"date": "d2", "fin_vol": 2_500_000},
        ]
        all_inds = {
            "clv": {"d1": 0.1, "d2": 0.4},
            "daily_money_flow": {"d1": 10, "d2": 20},
            "buying_pressure": {"d2": 0.7},
            "selling_pressure": {"d2": 0.3},
            "range_percentual": {"d2": 5.5},
        }
        info = {"money_flow_volume": Decimal(12345678)}

        metrics = build_session_metrics(daily, all_inds, info)

        assert metrics.last_date == "d2"
        assert metrics.clv == 0.4
        assert metrics.dmf == 20.0
        assert metrics.bp == 0.7
        assert metrics.sp == 0.3
        assert metrics.rp == 5.5
        assert metrics.fin_vol == 2_500_000.0
        assert metrics.fin_vol_millions == 2.5
        assert metrics.accumulated_mfv == 12345678.0

    def test_valores_ausentes_viram_zero(self):
        metrics = build_session_metrics([{"date": "d1"}], {}, {})

        assert metrics.clv == 0.0
        assert metrics.dmf == 0.0
        assert metrics.bp == 0.0
        assert metrics.sp == 0.0
        assert metrics.rp == 0.0
        assert metrics.fin_vol == 0.0
        assert metrics.fin_vol_millions == 0.0
        assert metrics.accumulated_mfv is None

    def test_mfv_acumulado_zero_permanece_zero(self):
        metrics = build_session_metrics(
            [{"date": "d1"}], {}, {"money_flow_volume": 0}
        )
        assert metrics.accumulated_mfv == 0.0

    def test_indicadores_nulos_do_pregao_viram_zero(self):
        all_inds = {"clv": {"d1": None}, "daily_money_flow": {"d1": None}}
        metrics = build_session_metrics([{"date": "d1"}], all_inds, {})
        assert metrics.clv == 0.0
        assert metrics.dmf == 0.0


class TestFlowIntensityPart:
    def test_comprador_forte(self):
        assert flow_intensity_part(1.0, _classification(3)) == (
            "O ativo fechou com forte fluxo financeiro comprador"
        )

    def test_comprador_moderado(self):
        assert flow_intensity_part(1.0, _classification(1)) == (
            "O ativo fechou com fluxo comprador moderado"
        )

    def test_comprador_leve(self):
        assert flow_intensity_part(1.0, _classification(0)) == (
            "O ativo fechou com leve fluxo comprador"
        )

    def test_vendedor_forte(self):
        assert flow_intensity_part(-1.0, _classification(-3)) == (
            "O ativo fechou com forte fluxo financeiro vendedor"
        )

    def test_vendedor_moderado(self):
        assert flow_intensity_part(-1.0, _classification(-1)) == (
            "O ativo fechou com fluxo vendedor moderado"
        )

    def test_vendedor_leve(self):
        assert flow_intensity_part(-1.0, _classification(0)) == (
            "O ativo fechou com leve fluxo vendedor"
        )

    def test_neutro(self):
        assert flow_intensity_part(0.0, _classification(0)) == (
            "O fluxo financeiro foi neutro"
        )


class TestClosePositionPart:
    def test_proximo_da_maxima(self):
        assert close_position_part(0.4) == (
            " e o fechamento ocorreu próximo da máxima"
        )

    def test_proximo_da_minima(self):
        assert close_position_part(-0.4) == (
            " e o fechamento ocorreu próximo da mínima"
        )

    def test_regiao_central(self):
        assert close_position_part(0.0) == (
            " e o fechamento ocorreu na região central do range"
        )

    def test_limite_nao_e_proximo_da_maxima(self):
        assert close_position_part(0.3) == (
            " e o fechamento ocorreu na região central do range"
        )


class TestDominancePart:
    def test_dominancia_compradora(self):
        assert dominance_part(0.7, 0.2) == (
            ", com ampla dominância compradora no range."
        )

    def test_dominancia_vendedora(self):
        assert dominance_part(0.2, 0.7) == (
            ", com ampla dominância vendedora no range."
        )

    def test_disputa_equilibrada(self):
        assert dominance_part(0.5, 0.5) == (
            ", com disputa equilibrada no range."
        )

    def test_limite_nao_e_dominancia(self):
        assert dominance_part(0.65, 0.3) == (
            ", com disputa equilibrada no range."
        )


class TestConvictionPart:
    def test_elevada(self):
        assert conviction_part(3) == "elevada"
        assert conviction_part(-3) == "elevada"

    def test_moderada(self):
        assert conviction_part(1) == "moderada"
        assert conviction_part(-1) == "moderada"

    def test_baixa(self):
        assert conviction_part(0) == "baixa"


class TestGenerateSummary:
    def test_compõe_a_frase_de_analise(self):
        summary = generate_summary(1.0, _classification(3), 0.5, 0.7, 0.3)
        assert summary == (
            "O ativo fechou com forte fluxo financeiro comprador"
            " e o fechamento ocorreu próximo da máxima"
            ", com ampla dominância compradora no range."
            " Convicção financeira elevada."
        )

    def test_fluxo_neutro(self):
        summary = generate_summary(0.0, _classification(0), 0.0, 0.0, 0.0)
        assert summary == (
            "O fluxo financeiro foi neutro"
            " e o fechamento ocorreu na região central do range"
            ", com disputa equilibrada no range."
            " Convicção financeira baixa."
        )
