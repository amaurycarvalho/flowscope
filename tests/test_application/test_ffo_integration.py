from datetime import date
from decimal import Decimal

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.application.fundamental_fallback import CompositeFfoProvider
from flowscope.domain.cvm import FundIdentity
from flowscope.domain.fii import FfoObservacao, PatrimonioFii, PrecoObservacao
from flowscope.domain.ffo import (
    ComponentProvenance,
    FFOComponent,
    FFOComponentType,
)
from flowscope.domain.structured import ISIN, Provento, ValorProvento
from flowscope.infrastructure.fii.ffo_engine_provider import FFOEngineProvider

REFERENCIA = date(2026, 12, 31)
CNPJ = "28737771000185"
_ISIN = "BR0000000000"


def _componentes_12_meses(valor="100000"):
    return [
        FFOComponent(
            description="Receita de aluguel",
            value=Decimal(valor),
            classification=FFOComponentType.RECURRING,
            provenance=ComponentProvenance(reference_date=date(2026, mes, 28)),
        )
        for mes in range(1, 13)
    ]


class _Quarterly:
    def __init__(self, componentes=None):
        self._componentes = componentes

    def get_components(self, cnpj, reference_date, ticker=""):
        return self._componentes or []


class _Resolver:
    def __call__(self, ticker):
        return FundIdentity(
            ticker=ticker, cnpj_fundo_classe=CNPJ, id_fnet="20294"
        )


def _rendimento(valor, mes):
    return Provento(
        codigo_isin=ISIN(_ISIN),
        codigo_negociacao="HGBS11",
        tipo="Rendimento",
        data_base=date(2026, mes, 10),
        valor_por_unidade=ValorProvento(Decimal(valor)),
        data_pagamento=date(2026, mes, 20),
        periodo_referencia="",
        isento_ir=True,
    )


class _Repo:
    def obter_nome(self, ticker):
        return "CSHG Renda Urbana"

    def obter_proventos(self, ticker, reference_date):
        return [_rendimento("0.50", 1), _rendimento("0.55", 7)]

    def obter_patrimonio(self, ticker, reference_date):
        return PatrimonioFii(
            reference_date=REFERENCIA,
            net_asset_value=Decimal("2942000000"),
            shares_outstanding=Decimal("144355726"),
            cotistas=100000,
            fonte="CVM",
        )


class _Mercado:
    def preco_fechamento(self, ticker, reference_date):
        return PrecoObservacao(
            preco=Decimal("18.74"), data_preco=reference_date, fonte="B3"
        )


def _engine(componentes=None):
    return FFOEngineProvider(
        quarterly_repository=_Quarterly(componentes), resolver=_Resolver()
    )


class TestMotorIntegrado:
    def test_metricas_de_ffo_preenchidas(self):
        caso = FundamentalAnalysisUseCase(
            _Repo(), ffo_provider=_engine(_componentes_12_meses()), mercado=_Mercado()
        )
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.metricas is not None
        assert resultado.metricas.ffo_yield is not None
        assert resultado.metricas.p_ffo is not None
        assert resultado.metricas.ffo_trend is not None

    def test_sem_componentes_ffo_na(self):
        caso = FundamentalAnalysisUseCase(
            _Repo(), ffo_provider=_engine([]), mercado=_Mercado()
        )
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.metricas is None or resultado.metricas.ffo_yield is None

    def test_engine_provider_direto(self):
        ffo = _engine(_componentes_12_meses()).obter_ffo("HGBS11", REFERENCIA)
        assert isinstance(ffo, FfoObservacao)
        assert ffo.ffo_12m == Decimal("1200000")
        assert ffo.ffo_3m == Decimal("300000")
        assert ffo.metodologia == "FLOWSCOPE_DERIVED"


class _FonteFalha:
    def obter_ffo(self, ticker, reference_date):
        raise RuntimeError("fundamentus fora do ar")


class _FonteFundamentus:
    def __init__(self):
        self.chamadas = 0

    def obter_ffo(self, ticker, reference_date):
        self.chamadas += 1
        return FfoObservacao(
            ffo_12m=Decimal("500000"),
            ffo_3m=Decimal("125000"),
            fonte="FUNDAMENTUS",
        )


class _FonteSpy:
    def __init__(self, resultado=None):
        self.chamadas = 0
        self._resultado = resultado

    def obter_ffo(self, ticker, reference_date):
        self.chamadas += 1
        return self._resultado


class TestComposicaoFfo:
    def test_usa_motor_quando_fundamentus_falha(self):
        engine = _engine(_componentes_12_meses())
        composto = CompositeFfoProvider([_FonteFalha(), engine])
        ffo = composto.obter_ffo("HGBS11", REFERENCIA)
        assert ffo is not None
        assert ffo.fonte == "CVM"

    def test_fundamentus_primario_nao_consulta_motor(self):
        fundamentus = _FonteFundamentus()
        engine = _FonteSpy()
        composto = CompositeFfoProvider([fundamentus, engine])
        ffo = composto.obter_ffo("HGBS11", REFERENCIA)
        assert ffo.fonte == "FUNDAMENTUS"
        assert engine.chamadas == 0

    def test_motor_usado_quando_fundamentus_sem_dado(self):
        fundamentus = _FonteSpy(resultado=None)
        engine = _engine(_componentes_12_meses())
        composto = CompositeFfoProvider([fundamentus, engine])
        ffo = composto.obter_ffo("HGBS11", REFERENCIA)
        assert ffo is not None
        assert ffo.fonte == "CVM"
        assert fundamentus.chamadas == 1
