from datetime import date
from decimal import Decimal

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.application.fundamental_fallback import CompositeFundamentalProvider
from flowscope.application.fundamental_ports import (
    CAMPO_DIVIDEND_YIELD,
    CAMPO_FFO_TREND,
    CAMPO_FFO_YIELD,
    CAMPO_NOME,
    CAMPO_P_FFO,
    CAMPO_P_VP,
    CampoFundamental,
)

REFERENCIA = date(2026, 9, 4)


class _Repo:
    def __init__(self, nomes=None):
        self._nomes = nomes or {}

    def obter_nome(self, ticker):
        return self._nomes.get(ticker)

    def obter_proventos(self, ticker, reference_date):
        return []

    def obter_patrimonio(self, ticker, reference_date):
        return None


class _Fonte:
    def __init__(self, campos=None, falhar=False):
        self._campos = campos or {}
        self._falhar = falhar

    def obter(self, ticker, reference_date):
        if self._falhar:
            raise RuntimeError("fundamentus indisponível")
        return self._campos


def _campos_fundamentus():
    return {
        CAMPO_NOME: CampoFundamental("CSHG Renda Urbana", "FUNDAMENTUS"),
        CAMPO_FFO_YIELD: CampoFundamental(Decimal("0.0816"), "FUNDAMENTUS"),
        CAMPO_DIVIDEND_YIELD: CampoFundamental(Decimal("0.079"), "FUNDAMENTUS"),
        CAMPO_P_VP: CampoFundamental(Decimal("0.92"), "FUNDAMENTUS"),
        CAMPO_P_FFO: CampoFundamental(Decimal("12.25"), "FUNDAMENTUS"),
        CAMPO_FFO_TREND: CampoFundamental(Decimal("0.15"), "FUNDAMENTUS"),
    }


class TestIntegracaoProviderPrimario:
    def test_metricas_preenchidas_pelo_fundamentus(self):
        caso = FundamentalAnalysisUseCase(
            _Repo(), fundamental_provider=_Fonte(_campos_fundamentus())
        )
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.nome == "CSHG Renda Urbana"
        assert resultado.metricas is not None
        assert resultado.metricas.ffo_yield == Decimal("0.0816")
        assert resultado.metricas.dividend_yield == Decimal("0.079")
        assert resultado.metricas.p_vp == Decimal("0.92")
        assert resultado.metricas.p_ffo == Decimal("12.25")
        assert resultado.metricas.ffo_trend is not None
        assert resultado.erro is None

    def test_nome_cai_para_repositorio_quando_provider_nao_fornece(self):
        caso = FundamentalAnalysisUseCase(
            _Repo({"HGBS11": "Nome do repositório"}),
            fundamental_provider=_Fonte({CAMPO_P_VP: CampoFundamental(Decimal("0.9"))}),
        )
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.nome == "Nome do repositório"

    def test_acao_nao_recebe_metricas_de_ffo(self):
        caso = FundamentalAnalysisUseCase(
            _Repo(), fundamental_provider=_Fonte(_campos_fundamentus())
        )
        resultado = caso.execute(["PETR4"], REFERENCIA)[0]
        assert resultado.metricas is None

    def test_fundamentus_indisponivel_cai_para_fallback(self):
        primario = _Fonte(falhar=True)
        fallback = _Fonte({CAMPO_P_VP: CampoFundamental(Decimal("0.92"), "CVM")})
        composto = CompositeFundamentalProvider([primario, fallback])
        caso = FundamentalAnalysisUseCase(_Repo(), fundamental_provider=composto)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.erro is None
        assert resultado.metricas is not None
        assert resultado.metricas.p_vp == Decimal("0.92")

    def test_fundamentus_indisponivel_mantem_linha_do_ticker(self):
        caso = FundamentalAnalysisUseCase(
            _Repo(), fundamental_provider=_Fonte(falhar=True)
        )
        resultado = caso.execute(["HGBS11"], REFERENCIA)
        assert len(resultado) == 1
        assert resultado[0].ticker == "HGBS11"
        assert resultado[0].erro is None

    def test_falha_de_um_ticker_nao_interrompe_os_demais(self):
        class _FontePorTicker:
            def obter(self, ticker, reference_date):
                if ticker == "HGBS11":
                    raise RuntimeError("falha no ticker")
                return {CAMPO_P_VP: CampoFundamental(Decimal("0.92"), "FUNDAMENTUS")}

        caso = FundamentalAnalysisUseCase(
            _Repo(), fundamental_provider=_FontePorTicker()
        )
        resultado = caso.execute(["HGBS11", "HGLG11"], REFERENCIA)
        assert [linha.ticker for linha in resultado] == ["HGBS11", "HGLG11"]
        assert resultado[0].erro is None
        assert resultado[1].metricas is not None
        assert resultado[1].metricas.p_vp == Decimal("0.92")
