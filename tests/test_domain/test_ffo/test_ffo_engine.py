from datetime import date
from decimal import Decimal

from flowscope.domain.ffo import (
    ComponentProvenance,
    FFOComponent,
    FFOComponentType,
    FFOQuality,
    calculate_ffo,
    calcular_ffo,
    classificar_componente,
    media_ponderada_cotas,
)

REFERENCIA = date(2026, 12, 31)


def _componente(descricao, valor, tipo=FFOComponentType.RECURRING, mes=None):
    proveniencia = (
        ComponentProvenance(reference_date=date(2026, mes, 28)) if mes else None
    )
    return FFOComponent(
        description=descricao,
        value=Decimal(valor),
        classification=tipo,
        provenance=proveniencia,
    )


def _serie_12_meses(valor="100"):
    return [
        _componente("receita de aluguel", valor, mes=mes)
        for mes in range(1, 13)
    ]


class TestComponentes:
    def test_recorrente_incluido(self):
        componente = _componente("receita de aluguel", "100")
        assert componente.included_in_ffo is True

    def test_nao_recorrente_excluido(self):
        componente = _componente(
            "ajuste ao valor justo", "100", FFOComponentType.FAIR_VALUE
        )
        assert componente.included_in_ffo is False


class TestClassificacao:
    def test_recorrente(self):
        assert (
            classificar_componente("Receita de aluguel")
            is FFOComponentType.RECURRING
        )
        assert (
            classificar_componente("Juros de CRI") is FFOComponentType.RECURRING
        )

    def test_fair_value(self):
        assert (
            classificar_componente("Ajuste ao valor justo de imóveis")
            is FFOComponentType.FAIR_VALUE
        )
        assert (
            classificar_componente("Marcação a mercado de CRI")
            is FFOComponentType.FAIR_VALUE
        )

    def test_alienacao(self):
        assert (
            classificar_componente("Ganho na venda de imóveis")
            is FFOComponentType.DISPOSAL
        )

    def test_nao_recorrente(self):
        assert (
            classificar_componente("Resultado não recorrente")
            is FFOComponentType.NON_RECURRING
        )

    def test_unknown(self):
        assert (
            classificar_componente("Outras receitas") is FFOComponentType.UNKNOWN
        )
        assert classificar_componente("") is FFOComponentType.UNKNOWN


class TestCalculateFfo:
    def test_soma_apenas_recorrentes(self):
        componentes = [
            _componente("receita", "10000000", FFOComponentType.RECURRING),
            _componente("despesa", "-2000000", FFOComponentType.RECURRING),
            _componente("valor justo", "5000000", FFOComponentType.FAIR_VALUE),
            _componente("alienação", "3000000", FFOComponentType.DISPOSAL),
        ]
        assert calculate_ffo(componentes) == Decimal("8000000")

    def test_unknown_excluido(self):
        componentes = [
            _componente("receita", "1000", FFOComponentType.RECURRING),
            _componente("outras", "999", FFOComponentType.UNKNOWN),
        ]
        assert calculate_ffo(componentes) == Decimal("1000")


class TestFfoMensalE12m:
    def test_janela_completa(self):
        resultado = calcular_ffo(_serie_12_meses(), REFERENCIA)
        assert resultado.ffo_12m == Decimal("1200")
        assert resultado.ffo_3m == Decimal("300")
        assert resultado.ffo_month == Decimal("100")
        assert resultado.warnings == ()

    def test_base_insuficiente(self):
        componentes = _serie_12_meses()[:-1]
        resultado = calcular_ffo(componentes, REFERENCIA)
        assert resultado.ffo_12m is None
        assert "INSUFFICIENT_BASE" in resultado.warnings

    def test_ignora_meses_fora_da_janela(self):
        componentes = _serie_12_meses() + [_componente("aluguel", "50", mes=None)]
        resultado = calcular_ffo(componentes, REFERENCIA)
        assert resultado.ffo_12m == Decimal("1200")


class TestFfoPorCota:
    def test_media_ponderada(self):
        assert media_ponderada_cotas(
            [(Decimal("100"), 30), (Decimal("200"), 30)]
        ) == Decimal("150")

    def test_ffo_por_cota(self):
        resultado = calcular_ffo(
            _serie_12_meses(), REFERENCIA, weighted_average_shares=Decimal("100")
        )
        assert resultado.ffo_per_share == Decimal("12")


class TestYieldEPFfo:
    def test_relacao_inversa(self):
        resultado = calcular_ffo(
            _serie_12_meses(),
            REFERENCIA,
            weighted_average_shares=Decimal("100"),
            market_price=Decimal("120"),
            market_price_date=date(2026, 12, 30),
        )
        assert resultado.ffo_yield == Decimal("0.1")
        assert resultado.p_ffo == Decimal("10")
        assert resultado.p_ffo * resultado.ffo_yield == Decimal("1")
        assert resultado.market_price_date == date(2026, 12, 30)

    def test_sem_preco_sem_yield(self):
        resultado = calcular_ffo(
            _serie_12_meses(), REFERENCIA, weighted_average_shares=Decimal("100")
        )
        assert resultado.ffo_yield is None
        assert resultado.p_ffo is None


class TestQualidade:
    def _com_unknown(self, valor_unknown):
        return [
            _componente("receita de aluguel", "1000", mes=12),
            _componente(
                "outras receitas", valor_unknown, FFOComponentType.UNKNOWN
            ),
        ]

    def test_alta(self):
        resultado = calcular_ffo(self._com_unknown("5"), REFERENCIA)
        assert resultado.quality is FFOQuality.HIGH

    def test_media(self):
        resultado = calcular_ffo(self._com_unknown("30"), REFERENCIA)
        assert resultado.quality is FFOQuality.MEDIUM

    def test_baixa(self):
        resultado = calcular_ffo(self._com_unknown("200"), REFERENCIA)
        assert resultado.quality is FFOQuality.LOW


class TestReconciliacao:
    def test_divergencia_acima_do_limite(self):
        resultado = calcular_ffo(
            _serie_12_meses(), REFERENCIA, reported=Decimal("1100")
        )
        assert "RECONCILIATION_DIVERGENCE" in resultado.warnings

    def test_dentro_do_limite(self):
        resultado = calcular_ffo(
            _serie_12_meses(), REFERENCIA, reported=Decimal("1205")
        )
        assert "RECONCILIATION_DIVERGENCE" not in resultado.warnings


class TestDeterminismo:
    def test_reproducao(self):
        componentes = _serie_12_meses()
        primeiro = calcular_ffo(componentes, REFERENCIA)
        segundo = calcular_ffo(componentes, REFERENCIA)
        assert primeiro == segundo
        assert primeiro.calculation_version == "FFO_V1"
