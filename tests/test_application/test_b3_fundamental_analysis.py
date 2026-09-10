from datetime import date
from decimal import Decimal

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.domain.fii import PrecoObservacao
from flowscope.domain.structured import ISIN, Provento, ValorProvento

REFERENCIA = date(2026, 9, 4)
_ISIN = "BR0000000000"


def _rendimento(data_base: date, valor: str) -> Provento:
    return Provento(
        codigo_isin=ISIN(_ISIN),
        codigo_negociacao="ALZR11",
        tipo="Rendimento",
        data_base=data_base,
        valor_por_unidade=ValorProvento(Decimal(valor)),
        data_pagamento=data_base,
        periodo_referencia="",
        isento_ir=True,
    )


class _Repo:
    def __init__(self, proventos=None, nome=None):
        self._proventos = proventos or []
        self._nome = nome

    def obter_nome(self, ticker):
        return self._nome

    def obter_proventos(self, ticker, reference_date):
        return self._proventos

    def obter_patrimonio(self, ticker, reference_date):
        return None


class _Mercado:
    def __init__(self, preco="18.74"):
        self._preco = Decimal(preco)

    def preco_fechamento(self, ticker, reference_date):
        return PrecoObservacao(
            preco=self._preco, data_preco=reference_date, fonte="B3"
        )


class TestDividendYieldDesacoplado:
    def test_dy_preenchido_sem_nav_e_ffo(self):
        repo = _Repo(
            proventos=[
                _rendimento(date(2026, 1, 15), "0.50"),
                _rendimento(date(2026, 7, 10), "0.55"),
            ],
            nome="Alianza Trust",
        )
        caso = FundamentalAnalysisUseCase(repo, mercado=_Mercado())
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.metricas is not None
        assert resultado.metricas.dividend_yield is not None
        assert resultado.metricas.dividend_yield.quantize(
            Decimal("0.0001")
        ) == Decimal("0.0560")
        assert resultado.metricas.ffo_yield is None
        assert resultado.metricas.p_vp is None
        assert resultado.metricas.p_ffo is None

    def test_dy_na_sem_preco(self):
        repo = _Repo(
            proventos=[_rendimento(date(2026, 7, 10), "0.55")],
        )
        caso = FundamentalAnalysisUseCase(repo)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.metricas is None

    def test_sem_dividendos_nao_calcula_dy(self):
        caso = FundamentalAnalysisUseCase(_Repo(), mercado=_Mercado())
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.metricas is None


class TestIsolamentoB3:
    def test_repositorio_sem_dados_mantem_linha(self):
        caso = FundamentalAnalysisUseCase(_Repo(), mercado=_Mercado())
        resultado = caso.execute(["HGBS11", "HGLG11"], REFERENCIA)
        assert [linha.ticker for linha in resultado] == ["HGBS11", "HGLG11"]
        assert all(linha.erro is None for linha in resultado)

    def test_falha_de_proventos_isola_ticker(self):
        class _RepoComFalha(_Repo):
            def obter_proventos(self, ticker, reference_date):
                if ticker == "HGBS11":
                    raise RuntimeError("falha B3")
                return []

        caso = FundamentalAnalysisUseCase(_RepoComFalha(), mercado=_Mercado())
        resultado = caso.execute(["HGBS11", "HGLG11"], REFERENCIA)
        assert resultado[0].erro is not None
        assert resultado[1].erro is None
