"""Testes da amostragem Fibonacci e da montagem de séries da evolução."""

from datetime import date, timedelta
from decimal import Decimal

from flowscope.application.fundamental_ports import (
    SCHEMA_VERSION_FUNDAMENTOS,
    ObservacaoFundamental,
)
from flowscope.domain.fii import (
    AnaliseFundamental,
    ClassificacaoAtivo,
    ClassificacaoExibicao,
    FonteClassificacao,
    MetricasFii,
    MetricasShort,
    Quality,
    TendenciaDividendo,
    TipoAtivo,
    UltimoDividendo,
)
from flowscope.presentation.gui.charts.fundamental_evolution_data import (
    CAMPOS_EVOLUCAO,
    TIPO_INTEIRO,
    TIPO_MONETARIO,
    TIPO_PERCENTUAL,
    TIPO_PERCENTUAL_1,
    TIPO_QUANTIDADE,
    TIPO_RAZAO,
    montar_series,
    selecionar_datas_fibonacci,
)

BASE = date(2025, 1, 1)


def _metricas(p_vp: str | None, dy: str | None) -> MetricasFii:
    return MetricasFii(
        market_value=None,
        ffo_yield=None,
        dividend_yield=None if dy is None else Decimal(dy),
        p_ffo=None,
        p_vp=None if p_vp is None else Decimal(p_vp),
        ffo_momentum=None,
        ffo_trend=None,
        ffo_trend_change=None,
        ffo_payout=None,
        quality=Quality.COMPLETE,
        warnings=(),
        evidence=(),
    )


def _analise(
    cotacao: str | None = None,
    vp_cota: str | None = None,
    p_vp: str | None = None,
    dy: str | None = None,
    dividendo: str | None = None,
    cotistas: int | None = None,
    cotas: str | None = None,
    shorts: MetricasShort | None = None,
) -> AnaliseFundamental:
    tem_metricas = p_vp is not None or dy is not None
    return AnaliseFundamental(
        ticker="HGBS11",
        nome="CSHG Renda Urbana",
        classificacao=ClassificacaoAtivo(
            ticker="HGBS11",
            tipo=TipoAtivo.FII,
            sub_tipo=None,
            fonte=FonteClassificacao.TAXONOMIA_FII,
        ),
        ultimo_dividendo=UltimoDividendo(
            data_com=None,
            valor=None if dividendo is None else Decimal(dividendo),
            valor_anterior=None,
            tendencia=TendenciaDividendo.N_A,
        ),
        dividendos_12m_por_cota=None,
        metricas=_metricas(p_vp, dy) if tem_metricas else None,
        classificacao_exibicao=ClassificacaoExibicao("FII", "Tijolo"),
        cotacao=None if cotacao is None else Decimal(cotacao),
        vp_cota=None if vp_cota is None else Decimal(vp_cota),
        cotistas=cotistas,
        cotas=None if cotas is None else Decimal(cotas),
        short=shorts,
    )


def _observacao(data: date, analise: AnaliseFundamental) -> ObservacaoFundamental:
    return ObservacaoFundamental(
        ticker="HGBS11",
        data=data,
        analise=analise,
        schema_version=SCHEMA_VERSION_FUNDAMENTOS,
    )


class TestSelecionarDatasFibonacci:
    def test_sem_datas(self):
        assert selecionar_datas_fibonacci([]) == []

    def test_uma_data(self):
        assert selecionar_datas_fibonacci([BASE]) == [BASE]

    def test_duas_datas_preservadas(self):
        datas = [BASE - timedelta(days=10), BASE]
        assert selecionar_datas_fibonacci(datas) == datas

    def test_duplicatas_sao_removidas(self):
        datas = [BASE, BASE, BASE - timedelta(days=5)]
        assert selecionar_datas_fibonacci(datas) == [
            BASE - timedelta(days=5),
            BASE,
        ]

    def test_cache_com_gaps_exatos_de_fibonacci(self):
        offsets = [0, 1, 3, 6, 11, 19, 32, 53, 87, 142, 231, 375]
        datas = sorted(BASE - timedelta(days=o) for o in offsets)
        assert selecionar_datas_fibonacci(datas) == datas

    def test_extremos_presentes_em_cache_esparso(self):
        offsets = [0, 4, 9, 20, 40, 90, 200]
        datas = sorted(BASE - timedelta(days=o) for o in offsets)
        selecionadas = selecionar_datas_fibonacci(datas)
        assert selecionadas == sorted(set(selecionadas))
        assert selecionadas[0] == BASE - timedelta(days=200)
        assert selecionadas[-1] == BASE
        assert len(selecionadas) >= 4

    def test_gaps_crescem_rumo_ao_passado(self):
        offsets = list(range(0, 400))
        datas = sorted(BASE - timedelta(days=o) for o in offsets)
        selecionadas = selecionar_datas_fibonacci(datas)
        gaps = [
            (selecionadas[i + 1] - selecionadas[i]).days
            for i in range(len(selecionadas) - 1)
        ]
        assert gaps[-1] == 1
        assert gaps[0] >= 8
        assert {2, 3, 5, 8}.issubset(set(gaps))


class TestMontarSeries:
    def test_sempre_oito_series(self):
        series = montar_series([])
        assert len(series) == 8
        assert [serie.campo for serie in series] == [
            campo.campo for campo in CAMPOS_EVOLUCAO
        ]

    def test_tipos_dos_campos(self):
        tipos = {serie.campo: serie.tipo for serie in montar_series([])}
        assert tipos["cotacao"] == TIPO_MONETARIO
        assert tipos["vp_cota"] == TIPO_MONETARIO
        assert tipos["p_vp"] == TIPO_RAZAO
        assert tipos["dividend_yield"] == TIPO_PERCENTUAL
        assert tipos["ultimo_dividendo"] == TIPO_MONETARIO
        assert tipos["cotistas"] == TIPO_INTEIRO
        assert tipos["cotas"] == TIPO_QUANTIDADE
        assert tipos["shorts_pct"] == TIPO_PERCENTUAL_1

    def test_shorts_pct_extraido(self):
        observacoes = [
            _observacao(
                BASE,
                _analise(shorts=MetricasShort(shorts_pct=Decimal("0.1"))),
            )
        ]
        series = {serie.campo: serie for serie in montar_series(observacoes)}
        assert series["shorts_pct"].pontos[0].valor == Decimal("0.1")

    def test_shorts_pct_ausente_fica_vazio(self):
        observacoes = [_observacao(BASE, _analise(cotacao="10"))]
        series = {serie.campo: serie for serie in montar_series(observacoes)}
        assert series["shorts_pct"].vazia

    def test_valores_extraidos(self):
        observacoes = [
            _observacao(
                BASE,
                _analise(
                    cotacao="10",
                    vp_cota="12",
                    p_vp="0.83",
                    dy="0.09",
                    dividendo="0.55",
                    cotistas=100000,
                    cotas="144355726",
                ),
            )
        ]
        series = {serie.campo: serie for serie in montar_series(observacoes)}
        assert series["cotacao"].pontos[0].valor == Decimal("10")
        assert series["vp_cota"].pontos[0].valor == Decimal("12")
        assert series["p_vp"].pontos[0].valor == Decimal("0.83")
        assert series["dividend_yield"].pontos[0].valor == Decimal("0.09")
        assert series["ultimo_dividendo"].pontos[0].valor == Decimal("0.55")
        assert series["cotistas"].pontos[0].valor == 100000
        assert series["cotas"].pontos[0].valor == Decimal("144355726")

    def test_campo_parcialmente_ausente_gera_lacuna(self):
        observacoes = [
            _observacao(BASE - timedelta(days=1), _analise(cotacao="9")),
            _observacao(BASE, _analise(cotacao=None, vp_cota="12")),
        ]
        series = {serie.campo: serie for serie in montar_series(observacoes)}
        cotacao = series["cotacao"]
        assert len(cotacao.pontos) == 1
        assert cotacao.pontos[0].data == BASE - timedelta(days=1)

    def test_campo_totalmente_ausente_fica_vazio(self):
        observacoes = [
            _observacao(BASE - timedelta(days=1), _analise(cotacao="9")),
            _observacao(BASE, _analise(cotacao="10")),
        ]
        series = {serie.campo: serie for serie in montar_series(observacoes)}
        assert series["p_vp"].vazia
        assert series["dividend_yield"].vazia
        assert series["cotistas"].vazia
        assert not series["cotacao"].vazia

    def test_serie_ordena_datas_crescentes(self):
        observacoes = [
            _observacao(BASE, _analise(cotacao="10")),
            _observacao(BASE - timedelta(days=5), _analise(cotacao="9")),
            _observacao(BASE - timedelta(days=2), _analise(cotacao="9.5")),
        ]
        series = {serie.campo: serie for serie in montar_series(observacoes)}
        datas = series["cotacao"].datas
        assert list(datas) == sorted(datas)

    def test_montagem_nao_faz_io(self, monkeypatch):
        def _sem_io(*args, **kwargs):
            raise AssertionError("montar_series não deve acessar arquivos")

        monkeypatch.setattr("builtins.open", _sem_io)
        series = montar_series([_observacao(BASE, _analise(cotacao="10"))])
        assert len(series) == 8
