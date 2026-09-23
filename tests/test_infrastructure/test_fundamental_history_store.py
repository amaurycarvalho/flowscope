"""Testes do codec e do store histórico de resultados fundamentalistas."""

import json
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from flowscope.application.fundamental_ports import (
    SCHEMA_VERSION_FUNDAMENTOS,
    ObservacaoFundamental,
)
from flowscope.domain.fii import (
    AnaliseFundamental,
    ClasseCotistas,
    ClassePatrimonio,
    ClasseRiscoFechamento,
    ClasseShorts,
    ClassificacaoAtivo,
    ClassificacaoExibicao,
    FonteClassificacao,
    MargensFii,
    MetricasFii,
    MetricasShort,
    MetricEvidence,
    MotivoMargem,
    Quality,
    ResultadoMargem,
    SubTipoFii,
    TendenciaDividendo,
    TendenciaFfo,
    TipoAtivo,
    UltimoDividendo,
)
from flowscope.infrastructure.fii.fundamental_analysis_codec import (
    analise_de_dict,
    analise_para_dict,
)
from flowscope.infrastructure.fii.fundamental_history_store import (
    JsonFundamentalHistoryStore,
)

REFERENCIA = date(2026, 9, 4)
AGORA = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


def _classificacao() -> ClassificacaoAtivo:
    return ClassificacaoAtivo(
        ticker="HGBS11",
        tipo=TipoAtivo.FII,
        sub_tipo=SubTipoFii.TIJOLO,
        fonte=FonteClassificacao.TAXONOMIA_FII,
    )


def _evidencia() -> MetricEvidence:
    return MetricEvidence(
        metric="MARKET_VALUE",
        value=Decimal("2705.23"),
        formula="price * shares_outstanding",
        inputs={"price": Decimal("18.74"), "fonte": "B3"},
        sources=("FUNDAMENTUS", "B3"),
        reference_date=REFERENCIA,
        calculation_version="FII_ANALYSIS_V1",
    )


def _metricas() -> MetricasFii:
    return MetricasFii(
        market_value=Decimal(2705230000),
        ffo_yield=Decimal("0.0816"),
        dividend_yield=Decimal("0.03"),
        p_ffo=Decimal("12.25"),
        p_vp=Decimal("0.92"),
        ffo_momentum=Decimal("0.05"),
        ffo_trend=TendenciaFfo.ALTA,
        ffo_trend_change=Decimal("0.05"),
        ffo_payout=Decimal("0.4"),
        quality=Quality.COMPLETE,
        warnings=("HIGH_DISTRIBUTION_VS_FFO",),
        evidence=(_evidencia(),),
    )


def _margens() -> MargensFii:
    return MargensFii(
        ffo_receita_12m=ResultadoMargem(Decimal("0.5")),
        ffo_receita_3m=ResultadoMargem(None, MotivoMargem.FFO_NEGATIVO),
        dividendos_receita_12m=ResultadoMargem(Decimal("0.2")),
        dividendos_receita_3m=ResultadoMargem(None, MotivoMargem.RECEITA_NEGATIVA),
        dividendos_ffo_12m=ResultadoMargem(Decimal("0.8")),
        dividendos_ffo_3m=ResultadoMargem(None),
        ffo_trend=TendenciaFfo.ESTAVEL,
    )


def _analise_completa() -> AnaliseFundamental:
    return AnaliseFundamental(
        ticker="HGBS11",
        nome="CSHG Renda Urbana",
        classificacao=_classificacao(),
        ultimo_dividendo=UltimoDividendo(
            data_com=date(2026, 8, 1),
            valor=Decimal("0.55"),
            valor_anterior=Decimal("0.50"),
            tendencia=TendenciaDividendo.ALTA,
        ),
        dividendos_12m_por_cota=Decimal("1.05"),
        metricas=_metricas(),
        margens=_margens(),
        short=MetricasShort(
            shorts_pct=Decimal("0.1"),
            volume_shorts=ClasseShorts.BAIXO,
            sir=Decimal("5"),
            risco_fechamento=ClasseRiscoFechamento.ALTO,
        ),
        cotacao=Decimal("104.13"),
        vp_cota=Decimal("115.82"),
        p_l=Decimal("2.84"),
        classificacao_exibicao=ClassificacaoExibicao("FII", "Tijolo: Logística"),
        cotas=Decimal(144355726),
        cotistas=100000,
        patrimonio=Decimal(2942000000),
        classe_cotistas=ClasseCotistas.MUITO_GRANDE,
        classe_patrimonio=ClassePatrimonio.GIGANTE,
        data_referencia=REFERENCIA,
        lpa=Decimal("1.2"),
        roe=Decimal("0.1"),
        roic=Decimal("0.09"),
        cap_rate=Decimal("0.08"),
        vacancia_media=Decimal("0.05"),
        qtd_imoveis=12,
        preco_tipico=Decimal(100),
        pct_preco_tipico=Decimal("0.04"),
        indexadores={"IPCA": Decimal("0.22"), "INCC": Decimal("0.05")},
        cnpj="12.345.678/0001-90",
        nome_administrador="ADM",
        cnpj_administrador="11",
        nome_gestor="GES",
        cnpj_gestor="22",
        avisos=("FFO_NOT_AVAILABLE",),
        erro=None,
    )


def _analise_parcial() -> AnaliseFundamental:
    return AnaliseFundamental(
        ticker="HGBS11",
        nome=None,
        classificacao=_classificacao(),
        ultimo_dividendo=UltimoDividendo(
            data_com=None,
            valor=None,
            valor_anterior=None,
            tendencia=TendenciaDividendo.N_A,
        ),
        dividendos_12m_por_cota=None,
        metricas=None,
        cotacao=None,
        cotistas=100000,
    )


def _store(tmp_path, schema_version=SCHEMA_VERSION_FUNDAMENTOS, now=None):
    return JsonFundamentalHistoryStore(
        cache_dir=tmp_path,
        schema_version=schema_version,
        now=now or (lambda: AGORA),
    )


class TestCodec:
    def test_round_trip_completo(self):
        analise = _analise_completa()
        assert analise_de_dict(analise_para_dict(analise)) == analise

    def test_round_trip_parcial(self):
        analise = _analise_parcial()
        assert analise_de_dict(analise_para_dict(analise)) == analise

    def test_round_trip_preserva_tipos(self):
        restaurada = analise_de_dict(analise_para_dict(_analise_completa()))
        assert isinstance(restaurada.cotacao, Decimal)
        assert isinstance(restaurada.data_referencia, date)
        assert isinstance(restaurada.classificacao.tipo, TipoAtivo)
        assert isinstance(restaurada.metricas.ffo_trend, TendenciaFfo)
        assert isinstance(restaurada.metricas.evidence[0].inputs["price"], Decimal)
        assert isinstance(restaurada.metricas.evidence[0].inputs["fonte"], str)
        assert restaurada.indexadores == {"IPCA": Decimal("0.22"), "INCC": Decimal("0.05")}

    def test_dict_inclui_data_referencia(self):
        dados = analise_para_dict(_analise_completa())
        assert dados["data_referencia"] == "2026-09-04"

    def test_dict_inclui_short_interest(self):
        dados = analise_para_dict(_analise_completa())
        assert dados["short"] == {
            "shorts_pct": "0.1",
            "volume_shorts": "BAIXO",
            "sir": "5",
            "risco_fechamento": "ALTO",
        }

    def test_round_trip_preserva_short_interest(self):
        restaurada = analise_de_dict(analise_para_dict(_analise_completa()))
        assert restaurada.short == _analise_completa().short
        assert isinstance(restaurada.short.shorts_pct, Decimal)
        assert isinstance(restaurada.short.volume_shorts, ClasseShorts)
        assert isinstance(restaurada.short.risco_fechamento, ClasseRiscoFechamento)

    def test_round_trip_preserva_campos_de_bdr(self):
        analise = replace(
            _analise_completa(),
            bdr_nivel="Nível I Não Patrocinado",
            bdr_observacao="O valor informado já está deduzido de IR",
            nome_depositario="Banco B3 S.A.",
            nome_empresa_bdr="Exxon Mobil Corporation",
            isin="BREXXOBDR006",
        )
        restaurada = analise_de_dict(analise_para_dict(analise))
        assert restaurada.bdr_nivel == "Nível I Não Patrocinado"
        assert restaurada.bdr_observacao == (
            "O valor informado já está deduzido de IR"
        )
        assert restaurada.nome_depositario == "Banco B3 S.A."
        assert restaurada.nome_empresa_bdr == "Exxon Mobil Corporation"
        assert restaurada.isin == "BREXXOBDR006"


class TestStoreBasico:
    def test_registrar_e_obter(self, tmp_path):
        store = _store(tmp_path)
        analise = _analise_completa()
        store.registrar("HGBS11", REFERENCIA, analise)
        assert store.obter("HGBS11", REFERENCIA) == analise

    def test_obter_ausente_retorna_none(self, tmp_path):
        assert _store(tmp_path).obter("HGBS11", REFERENCIA) is None

    def test_versao_gravada_por_observacao(self, tmp_path):
        store = _store(tmp_path)
        store.registrar("HGBS11", REFERENCIA, _analise_completa())
        caminho = tmp_path / "fundamentos" / "HGBS11.json"
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        registro = dados["observacoes"][REFERENCIA.isoformat()]
        assert registro["schema_version"] == SCHEMA_VERSION_FUNDAMENTOS
        assert registro["analise"]["data_referencia"] == "2026-09-04"

    def test_escrita_atomica_sem_temporario(self, tmp_path):
        store = _store(tmp_path)
        store.registrar("HGBS11", REFERENCIA, _analise_completa())
        assert not list((tmp_path / "fundamentos").glob("*.tmp"))

    def test_armazenamento_corrompido_e_ignorado(self, tmp_path):
        destino = tmp_path / "fundamentos"
        destino.mkdir(parents=True)
        (destino / "HGBS11.json").write_text("{invalido", encoding="utf-8")
        store = _store(tmp_path)
        assert store.obter("HGBS11", REFERENCIA) is None
        assert store.datas("HGBS11") == []


class TestRecuperacaoHistorica:
    def test_datas_disponiveis_em_ordem(self, tmp_path):
        store = _store(tmp_path)
        store.registrar("HGBS11", date(2026, 9, 4), _analise_completa())
        store.registrar("HGBS11", date(2026, 9, 2), _analise_completa())
        assert store.datas("HGBS11") == [date(2026, 9, 2), date(2026, 9, 4)]

    def test_historico_no_intervalo(self, tmp_path):
        store = _store(tmp_path)
        for dia in (date(2026, 8, 1), date(2026, 9, 1), date(2026, 9, 10)):
            store.registrar("HGBS11", dia, _analise_completa())
        historico = store.historico("HGBS11", date(2026, 8, 15), date(2026, 9, 5))
        assert [observacao.data for observacao in historico] == [date(2026, 9, 1)]

    def test_historico_inclui_versao(self, tmp_path):
        _store(tmp_path, schema_version=1).registrar(
            "HGBS11", REFERENCIA, _analise_completa()
        )
        store_v2 = _store(tmp_path, schema_version=2)
        historico = store_v2.historico("HGBS11", REFERENCIA, REFERENCIA)
        assert historico == [
            ObservacaoFundamental(
                ticker="HGBS11",
                data=REFERENCIA,
                analise=_analise_completa(),
                schema_version=1,
            )
        ]


class TestVersionamento:
    def test_obter_exige_versao_atual(self, tmp_path):
        _store(tmp_path, schema_version=1).registrar(
            "HGBS11", REFERENCIA, _analise_completa()
        )
        assert _store(tmp_path, schema_version=2).obter("HGBS11", REFERENCIA) is None

    def test_recomputo_sobrescreve_versao_antiga(self, tmp_path):
        _store(tmp_path, schema_version=1).registrar(
            "HGBS11", REFERENCIA, _analise_completa()
        )
        store_v2 = _store(tmp_path, schema_version=2)
        nova = _analise_completa()
        store_v2.registrar("HGBS11", REFERENCIA, nova)
        assert store_v2.obter("HGBS11", REFERENCIA) == nova


class TestRetencao:
    def test_observacao_dentro_do_limite_permanece(self, tmp_path):
        store = _store(tmp_path)
        store.registrar("HGBS11", date(2026, 1, 1), _analise_completa())
        assert store.obter("HGBS11", date(2026, 1, 1)) is not None

    def test_observacao_expirada_nao_e_servida(self, tmp_path):
        _store(tmp_path).registrar("HGBS11", date(2026, 1, 1), _analise_completa())
        futuro = datetime(2027, 6, 1, tzinfo=timezone.utc)
        store = _store(tmp_path, now=lambda: futuro)
        assert store.obter("HGBS11", date(2026, 1, 1)) is None
        assert store.datas("HGBS11") == []

    def test_prune_remove_expiradas_ao_gravar(self, tmp_path):
        _store(tmp_path).registrar("HGBS11", date(2026, 1, 1), _analise_completa())
        futuro = datetime(2027, 6, 1, tzinfo=timezone.utc)
        store = _store(tmp_path, now=lambda: futuro)
        store.registrar("HGBS11", futuro.date(), _analise_completa())
        assert store.datas("HGBS11") == [futuro.date()]

    def test_limite_e_365_dias(self, tmp_path):
        store = _store(tmp_path)
        dentro = AGORA.date() - timedelta(days=364)
        store.registrar("HGBS11", dentro, _analise_completa())
        assert store.obter("HGBS11", dentro) is not None


class TestPoliticaParcialidade:
    def test_parcial_sobrescrita_por_completa(self, tmp_path):
        store = _store(tmp_path)
        store.registrar("HGBS11", REFERENCIA, _analise_parcial())
        completa = _analise_completa()
        store.registrar("HGBS11", REFERENCIA, completa)
        assert store.obter("HGBS11", REFERENCIA) == completa

    def test_completa_imutavel_no_mesmo_dia(self, tmp_path):
        store = _store(tmp_path)
        original = _analise_completa()
        store.registrar("HGBS11", REFERENCIA, original)
        outra = replace(original, cotacao=Decimal(1))
        store.registrar("HGBS11", REFERENCIA, outra)
        assert store.obter("HGBS11", REFERENCIA) == original

    def test_force_sobrescreve_completa(self, tmp_path):
        store = _store(tmp_path)
        store.registrar("HGBS11", REFERENCIA, _analise_completa())
        nova = replace(_analise_completa(), cotacao=Decimal(1))
        store.registrar("HGBS11", REFERENCIA, nova, force=True)
        assert store.obter("HGBS11", REFERENCIA) == nova
