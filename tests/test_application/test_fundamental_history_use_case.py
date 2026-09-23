"""Testes do read-through do histórico no caso de uso fundamentalista."""

from datetime import date, datetime, timezone
from decimal import Decimal

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.application.fundamental_ports import (
    CAMPO_COTACAO,
    CampoFundamental,
)
from flowscope.domain.fii import (
    AnaliseFundamental,
    TendenciaDividendo,
    UltimoDividendo,
    classificar_ticker,
)
from flowscope.infrastructure.fii.fundamental_history_store import (
    JsonFundamentalHistoryStore,
)

REF = date(2026, 9, 4)
OUTRA_DATA = date(2026, 9, 5)
AGORA = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


class FakeRepo:
    """Repositório mínimo, com falha opcional de proventos."""

    def __init__(self, nome=None, falhar_proventos=False):
        self.nome = nome
        self.falhar_proventos = falhar_proventos

    def obter_nome(self, ticker):
        return self.nome

    def obter_proventos(self, ticker, reference_date):
        if self.falhar_proventos:
            raise RuntimeError("falha ao obter proventos")
        return []

    def obter_patrimonio(self, ticker, reference_date):
        return None


class SpyFonte:
    """Fonte fundamentalista que conta quantas vezes foi consultada."""

    def __init__(self, campos=None):
        self.campos = campos or {}
        self.chamadas = 0

    def obter(self, ticker, reference_date):
        self.chamadas += 1
        return self.campos


def _store(tmp_path):
    return JsonFundamentalHistoryStore(cache_dir=tmp_path, now=lambda: AGORA)


def _analise(ticker, nome=None, cotacao=None):
    return AnaliseFundamental(
        ticker=ticker,
        nome=nome,
        classificacao=classificar_ticker(ticker),
        ultimo_dividendo=UltimoDividendo(
            data_com=None,
            valor=None,
            valor_anterior=None,
            tendencia=TendenciaDividendo.N_A,
        ),
        dividendos_12m_por_cota=None,
        metricas=None,
        cotacao=cotacao,
    )


def _caso(store, fonte, repo=None):
    return FundamentalAnalysisUseCase(
        repo or FakeRepo(),
        fundamental_provider=fonte,
        historico_store=store,
    )


def _fonte_cotacao(valor):
    return SpyFonte({CAMPO_COTACAO: CampoFundamental(Decimal(valor))})


class TestReadThrough:
    def test_hit_evita_aquisicao(self, tmp_path):
        store = _store(tmp_path)
        primeira = _caso(store, _fonte_cotacao("10"))
        primeira.execute(["HGBS11"], REF)

        fonte = _fonte_cotacao("99")
        caso = _caso(store, fonte)
        resultado = caso.execute(["HGBS11"], REF)

        assert fonte.chamadas == 0
        assert resultado[0].cotacao == Decimal("10")

    def test_ausencia_executa_e_registra(self, tmp_path):
        store = _store(tmp_path)
        fonte = _fonte_cotacao("10")
        _caso(store, fonte).execute(["HGBS11"], REF)
        assert fonte.chamadas == 1
        assert store.obter("HGBS11", REF).cotacao == Decimal("10")

    def test_erro_nao_registra(self, tmp_path):
        store = _store(tmp_path)
        caso = _caso(store, SpyFonte(), repo=FakeRepo(falhar_proventos=True))
        resultado = caso.execute(["HGBS11"], REF)
        assert resultado[0].erro is not None
        assert store.obter("HGBS11", REF) is None


class TestParcialidade:
    def test_parcial_e_recomputada_e_sobrescrita(self, tmp_path):
        store = _store(tmp_path)
        store.registrar("HGBS11", REF, _analise("HGBS11"))
        fonte = _fonte_cotacao("10")
        _caso(store, fonte).execute(["HGBS11"], REF)
        assert fonte.chamadas == 1
        assert store.obter("HGBS11", REF).cotacao == Decimal("10")

    def test_completa_e_imutavel_no_dia(self, tmp_path):
        store = _store(tmp_path)
        store.registrar("HGBS11", REF, _analise("HGBS11", cotacao=Decimal("999")))
        fonte = _fonte_cotacao("10")
        _caso(store, fonte).execute(["HGBS11"], REF)
        assert fonte.chamadas == 0
        assert store.obter("HGBS11", REF).cotacao == Decimal("999")


class TestBypass:
    def test_force_refresh_sobrescreve_completa(self, tmp_path):
        store = _store(tmp_path)
        store.registrar("HGBS11", REF, _analise("HGBS11", cotacao=Decimal("999")))
        fonte = _fonte_cotacao("10")
        _caso(store, fonte).execute(["HGBS11"], REF, force_refresh=True)
        assert fonte.chamadas == 1
        assert store.obter("HGBS11", REF).cotacao == Decimal("10")

    def test_force_refresh_com_erro_serve_observacao_completa(self, tmp_path):
        store = _store(tmp_path)
        store.registrar("HGBS11", REF, _analise("HGBS11", cotacao=Decimal("999")))
        caso = _caso(store, SpyFonte(), repo=FakeRepo(falhar_proventos=True))
        resultado = caso.execute(["HGBS11"], REF, force_refresh=True)
        assert resultado[0].erro is None
        assert resultado[0].cotacao == Decimal("999")
        assert store.obter("HGBS11", REF).cotacao == Decimal("999")


class TestTrocaDeData:
    def test_nao_vaza_entre_datas(self, tmp_path):
        store = _store(tmp_path)
        store.registrar("HGBS11", REF, _analise("HGBS11", cotacao=Decimal("999")))
        fonte = _fonte_cotacao("10")
        resultado = _caso(store, fonte).execute(["HGBS11"], OUTRA_DATA)
        assert resultado[0].cotacao == Decimal("10")
        assert store.obter("HGBS11", REF).cotacao == Decimal("999")
        assert store.obter("HGBS11", OUTRA_DATA).cotacao == Decimal("10")
