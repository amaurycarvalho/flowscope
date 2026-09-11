from datetime import date
from decimal import Decimal

import pytest

from flowscope.domain.fii import (
    CALCULATION_VERSION,
    FONTE_DERIVADA,
    FiiSnapshot,
    Inconsistencia,
    MetricEvidence,
    Quality,
    TendenciaFfo,
    analisar_snapshot,
    dividend_yield,
    ffo_momentum,
    ffo_payout,
    ffo_yield,
    market_value,
    p_ffo,
    p_l,
    p_vp,
    percentual_preco_tipico,
    preco_tipico,
    verificar_consistencia,
)


def _snapshot_hgbs11() -> FiiSnapshot:
    return FiiSnapshot(
        ticker="HGBS11",
        reference_date=date(2026, 9, 4),
        price=Decimal("18.74"),
        shares_outstanding=Decimal("144355726"),
        net_asset_value=Decimal("2942000000"),
        ffo_12m=Decimal("220777000"),
        ffo_3m=Decimal("63802000"),
        dividends_12m=Decimal("213080000"),
    )


class TestFuncoesPurras:
    def test_market_value(self):
        assert market_value(Decimal("18.74"), Decimal("144355726")) == Decimal(
            "2705226305.24"
        )

    def test_ffo_yield_exemplo(self):
        valor = ffo_yield(Decimal("220777000"), Decimal("2705226305.24"))
        assert valor.quantize(Decimal("0.0001")) == Decimal("0.0816")

    def test_p_ffo_exemplo(self):
        valor = p_ffo(Decimal("2705226305.24"), Decimal("220777000"))
        assert valor.quantize(Decimal("0.01")) == Decimal("12.25")

    def test_p_vp_exemplo(self):
        valor = p_vp(Decimal("2705226305.24"), Decimal("2942000000"))
        assert valor.quantize(Decimal("0.01")) == Decimal("0.92")

    def test_p_l_exemplo(self):
        valor = p_l(Decimal("18.74"), Decimal("0.55"))
        assert valor.quantize(Decimal("0.01")) == Decimal("2.84")

    def test_p_l_dividendo_zero_ou_ausente_retorna_none(self):
        assert p_l(Decimal("18.74"), Decimal(0)) is None
        assert p_l(Decimal("18.74"), None) is None

    def test_p_l_disponivel_na_importacao_publica(self):
        from flowscope.domain.fii import p_l as publico

        assert publico is p_l

    def test_dividend_yield(self):
        valor = dividend_yield(Decimal("213080000"), Decimal("2705226305.24"))
        assert valor.quantize(Decimal("0.0001")) == Decimal("0.0788")

    def test_ffo_momentum_exemplo(self):
        valor = ffo_momentum(Decimal("63802000"), Decimal("220777000"))
        assert valor.quantize(Decimal("0.001")) == Decimal("0.156")

    def test_ffo_payout(self):
        assert ffo_payout(Decimal("213080000"), Decimal("220777000")) == Decimal(
            "213080000"
        ) / Decimal("220777000")

    def test_preco_tipico(self):
        assert preco_tipico(
            Decimal("12"), Decimal("8"), Decimal("10")
        ) == Decimal("10")

    def test_preco_tipico_insumo_ausente(self):
        assert preco_tipico(None, Decimal("8"), Decimal("10")) is None
        assert preco_tipico(Decimal("12"), None, Decimal("10")) is None
        assert preco_tipico(Decimal("12"), Decimal("8"), None) is None

    def test_percentual_preco_tipico(self):
        valor = percentual_preco_tipico(Decimal("9"), Decimal("10"))
        assert valor == Decimal("-0.1")

    def test_percentual_preco_tipico_indisponivel(self):
        assert percentual_preco_tipico(None, Decimal("10")) is None
        assert percentual_preco_tipico(Decimal("9"), None) is None
        assert percentual_preco_tipico(Decimal("9"), Decimal(0)) is None


class TestAnaliseSnapshot:
    def test_metricas_do_cenario_hgbs11(self):
        metricas = analisar_snapshot(_snapshot_hgbs11())
        assert metricas.market_value == Decimal("2705226305.24")
        assert metricas.ffo_yield.quantize(Decimal("0.0001")) == Decimal("0.0816")
        assert metricas.p_ffo.quantize(Decimal("0.01")) == Decimal("12.25")
        assert metricas.p_vp.quantize(Decimal("0.01")) == Decimal("0.92")
        assert metricas.dividend_yield.quantize(Decimal("0.0001")) == Decimal("0.0788")
        assert metricas.ffo_momentum.quantize(Decimal("0.001")) == Decimal("0.156")
        assert metricas.ffo_trend is TendenciaFfo.ALTA
        assert metricas.quality is Quality.COMPLETE
        assert metricas.warnings == ()

    def test_invariante_p_ffo_vezes_ffo_yield(self):
        metricas = analisar_snapshot(_snapshot_hgbs11())
        produto = metricas.p_ffo * metricas.ffo_yield
        assert abs(produto - Decimal(1)) <= Decimal("0.000001")

    def test_invariante_market_value_por_cotas(self):
        snapshot = _snapshot_hgbs11()
        assert (
            market_value(snapshot.price, snapshot.shares_outstanding)
            / snapshot.shares_outstanding
        ) == snapshot.price

    def test_ffo_nao_positivo_gera_na(self):
        snapshot = FiiSnapshot(
            ticker="HGBS11",
            reference_date=date(2026, 9, 4),
            price=Decimal("18.74"),
            shares_outstanding=Decimal("144355726"),
            net_asset_value=Decimal("2942000000"),
            ffo_12m=Decimal("-5000000"),
            ffo_3m=Decimal("1000000"),
            dividends_12m=Decimal("1000000"),
        )
        metricas = analisar_snapshot(snapshot)
        assert metricas.ffo_yield is None
        assert metricas.p_ffo is None
        assert metricas.ffo_momentum is None
        assert metricas.ffo_trend is None
        assert metricas.p_vp is not None
        assert Inconsistencia.NEGATIVE_FFO.value in metricas.warnings
        assert metricas.quality is Quality.PARTIAL

    def test_patrimonio_nao_positivo_gera_p_vp_na(self):
        snapshot = FiiSnapshot(
            ticker="HGBS11",
            reference_date=date(2026, 9, 4),
            price=Decimal("18.74"),
            shares_outstanding=Decimal("144355726"),
            net_asset_value=Decimal("-1000"),
            ffo_12m=Decimal("220777000"),
            ffo_3m=Decimal("63802000"),
            dividends_12m=Decimal("213080000"),
        )
        metricas = analisar_snapshot(snapshot)
        assert metricas.p_vp is None
        assert metricas.ffo_yield is not None
        assert metricas.quality is Quality.PARTIAL

    def test_valor_de_mercado_invalido(self):
        snapshot = FiiSnapshot(
            ticker="HGBS11",
            reference_date=date(2026, 9, 4),
            price=Decimal("0"),
            shares_outstanding=Decimal("144355726"),
            net_asset_value=Decimal("2942000000"),
            ffo_12m=Decimal("220777000"),
            ffo_3m=Decimal("63802000"),
            dividends_12m=Decimal("213080000"),
        )
        metricas = analisar_snapshot(snapshot)
        assert metricas.market_value is None
        assert metricas.quality is Quality.INVALID
        assert Inconsistencia.MARKET_VALUE_INVALID.value in metricas.warnings

    def test_alerta_distribuicao_acima_do_ffo(self):
        snapshot = FiiSnapshot(
            ticker="HGBS11",
            reference_date=date(2026, 9, 4),
            price=Decimal("18.74"),
            shares_outstanding=Decimal("144355726"),
            net_asset_value=Decimal("2942000000"),
            ffo_12m=Decimal("220777000"),
            ffo_3m=Decimal("63802000"),
            dividends_12m=Decimal("1200000000"),
        )
        metricas = analisar_snapshot(snapshot)
        assert Inconsistencia.HIGH_DISTRIBUTION_VS_FFO.value in metricas.warnings


class TestEvidencia:
    def test_evidencia_do_ffo_yield(self):
        metricas = analisar_snapshot(_snapshot_hgbs11())
        evidencias = {evidencia.metric: evidencia for evidencia in metricas.evidence}
        evidencia = evidencias["FFO_YIELD"]
        assert isinstance(evidencia, MetricEvidence)
        assert evidencia.formula == "ffo_12m / market_value"
        assert evidencia.inputs["ffo_12m"] == Decimal("220777000")
        assert "market_value" in evidencia.inputs
        assert FONTE_DERIVADA in evidencia.sources
        assert evidencia.reference_date == date(2026, 9, 4)
        assert evidencia.calculation_version == CALCULATION_VERSION

    def test_todas_as_metricas_possuem_evidencia(self):
        metricas = analisar_snapshot(_snapshot_hgbs11())
        nomes = {evidencia.metric for evidencia in metricas.evidence}
        assert {
            "MARKET_VALUE",
            "FFO_YIELD",
            "P_FFO",
            "P_VP",
            "DIVIDEND_YIELD",
            "FFO_MOMENTUM",
        } <= nomes


class TestConsistencia:
    def test_consistencia_mantida(self):
        assert verificar_consistencia(Decimal("12.25"), Decimal("0.0816")) is True

    def test_consistencia_violada(self):
        assert verificar_consistencia(Decimal("20"), Decimal("0.08")) is False

    def test_sem_dados_nao_gera_inconsistencia(self):
        assert verificar_consistencia(None, None) is True
