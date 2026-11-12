"""Testes da leitura do guidance pela análise fundamentalista, sem cálculo."""

from datetime import date, datetime, timezone
from decimal import Decimal

from flowscope.application.avaliar_guidance import PROMPT_VERSION
from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.domain.fii import (
    METODO_DETERMINISTICO,
    METODO_IA,
    AnaliseFundamental,
    AvaliacaoGuidance,
    ClassificacaoExibicao,
    Guidance,
    UltimoDividendo,
    classificar_exibicao,
    classificar_ticker,
)
from flowscope.infrastructure.guidance_store import JsonGuidanceStore

REFERENCIA = date(2026, 9, 4)
GUIDANCE = Guidance(
    valor_min=Decimal("0.74"),
    valor_max=Decimal("0.78"),
    periodo="restante do ano de 2026",
    data_relatorio=date(2026, 8, 1),
)


class _RepoFake:
    def obter_nome(self, ticker):
        return None

    def obter_proventos(self, ticker, reference_date):
        return []

    def obter_patrimonio(self, ticker, reference_date):
        return None


class _StoreEspiao:
    def __init__(self, guidance: Guidance | None = None) -> None:
        self.guidance = guidance
        self.consultas: list[str] = []

    def obter(self, ticker):
        self.consultas.append(ticker)
        return self.guidance

    def salvar(self, ticker, guidance):  # pragma: no cover - não usado aqui
        raise AssertionError("a análise não deve gravar guidance")


def _analise_sem_guidance() -> AnaliseFundamental:
    classificacao = classificar_ticker("HGBS11")
    exibicao = classificar_exibicao(discriminador=None, fallback=classificacao)
    return AnaliseFundamental(
        ticker="HGBS11",
        nome="CSHG Renda Urbana",
        classificacao=classificacao,
        ultimo_dividendo=UltimoDividendo(
            data_com=None, valor=None, valor_anterior=None, tendencia=None
        ),
        dividendos_12m_por_cota=None,
        metricas=None,
        classificacao_exibicao=exibicao,
    )


class _HistoricoFake:
    def __init__(self, analise: AnaliseFundamental) -> None:
        self._analise = analise

    def obter(self, ticker, reference_date):
        return self._analise if ticker == self._analise.ticker else None

    def registrar(self, ticker, reference_date, resultado, force=False):
        raise AssertionError("não deve recomputar com acerto completo no cache")


class TestLeitura:
    def test_fii_com_cache_recebe_guidance(self):
        store = _StoreEspiao(GUIDANCE)
        caso = FundamentalAnalysisUseCase(_RepoFake(), guidance_store=store)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.guidance == GUIDANCE
        assert store.consultas == ["HGBS11"]

    def test_cache_vazio_nao_expoe_nem_calcula(self):
        store = _StoreEspiao(None)
        caso = FundamentalAnalysisUseCase(_RepoFake(), guidance_store=store)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.guidance is None
        assert store.consultas == ["HGBS11"]

    def test_papel_nao_consulta_guidance(self):
        store = _StoreEspiao(GUIDANCE)
        caso = FundamentalAnalysisUseCase(_RepoFake(), guidance_store=store)
        resultado = caso.execute(["PETR4"], REFERENCIA)[0]
        assert resultado.guidance is None
        assert store.consultas == []

    def test_cache_hit_reaplica_a_leitura_do_guidance(self):
        store = _StoreEspiao(GUIDANCE)
        historico = _HistoricoFake(_analise_sem_guidance())
        caso = FundamentalAnalysisUseCase(
            _RepoFake(), guidance_store=store, historico_store=historico
        )
        resultado, de_cache = caso._analisar_ou_cache(
            "HGBS11", REFERENCIA, force_refresh=False
        )
        assert de_cache is True
        assert resultado.guidance == GUIDANCE

    def test_sem_store_nao_expoe_guidance(self):
        caso = FundamentalAnalysisUseCase(_RepoFake())
        assert caso.execute(["HGBS11"], REFERENCIA)[0].guidance is None


class TestClassificacaoExibicao:
    def test_hgbs11_e_fii(self):
        exibicao = classificar_exibicao(
            discriminador=None, fallback=classificar_ticker("HGBS11")
        )
        assert isinstance(exibicao, ClassificacaoExibicao)
        assert exibicao.tipo == "FII"


class TestDerivacaoIntegrada:
    def test_ledger_sintetico_expoe_guidance_da_ia(self, tmp_path):
        store = JsonGuidanceStore(cache_dir=tmp_path)
        data_relatorio = date(2026, 8, 1)
        deterministica = AvaliacaoGuidance(
            metodo=METODO_DETERMINISTICO,
            data_relatorio=data_relatorio,
            guidance=Guidance(
                valor_min=Decimal("1.05"),
                valor_max=Decimal("1.05"),
                periodo="",
                data_relatorio=data_relatorio,
            ),
            avaliado_em=datetime(2026, 11, 1, tzinfo=timezone.utc),
        )
        por_ia = AvaliacaoGuidance(
            metodo=METODO_IA,
            data_relatorio=data_relatorio,
            guidance=Guidance(
                valor_min=Decimal("1.00"),
                valor_max=Decimal("1.10"),
                periodo="próximo trimestre",
                data_relatorio=data_relatorio,
            ),
            avaliado_em=datetime(2026, 10, 1, tzinfo=timezone.utc),
            prompt_version=PROMPT_VERSION,
        )
        store.salvar_avaliacao("HGBS11", "det", deterministica)
        store.salvar_avaliacao("HGBS11", "ia", por_ia)

        caso = FundamentalAnalysisUseCase(_RepoFake(), guidance_store=store)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]

        assert resultado.guidance is not None
        assert resultado.guidance.valor_min == Decimal("1.00")
        assert resultado.guidance.valor_max == Decimal("1.10")
        assert resultado.guidance.periodo == "próximo trimestre"
