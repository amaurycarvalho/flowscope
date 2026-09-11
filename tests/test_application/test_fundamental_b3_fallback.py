from datetime import date
from decimal import Decimal

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.application.fundamental_ports import (
    CAMPO_CLASSIFICACAO_FII,
    CAMPO_COTACAO,
    CAMPO_DISCRIMINADOR,
    CAMPO_FFO_YIELD,
    CAMPO_GESTAO,
    CAMPO_MAX_52_SEM,
    CAMPO_MIN_52_SEM,
    CAMPO_P_FFO,
    CAMPO_SEGMENTO,
    CAMPO_VP_COTA,
    CampoFundamental,
)
from flowscope.domain.fii import (
    FfoObservacao,
    PatrimonioFii,
)
from flowscope.domain.structured import ISIN, Provento, ValorProvento
from flowscope.infrastructure.fii.b3_price import B3MarketPriceFromResult

REFERENCIA = date(2026, 9, 4)
_ISIN = "BRCYCRCTF004"


def _rendimento(valor: str, data_base: date = date(2026, 8, 10)) -> Provento:
    return Provento(
        codigo_isin=ISIN(_ISIN),
        codigo_negociacao="CYCR11",
        tipo="Rendimento",
        data_base=data_base,
        valor_por_unidade=ValorProvento(Decimal(valor)),
        data_pagamento=data_base,
        periodo_referencia="",
        isento_ir=True,
    )


class _Repo:
    def __init__(self, proventos=None, patrimonio=None):
        self._proventos = proventos or []
        self._patrimonio = patrimonio

    def obter_nome(self, ticker):
        return None

    def obter_proventos(self, ticker, reference_date):
        return self._proventos

    def obter_patrimonio(self, ticker, reference_date):
        return self._patrimonio


class _Fonte:
    def __init__(self, campos):
        self._campos = campos

    def obter(self, ticker, reference_date):
        return self._campos


class _FfoSpy:
    def __init__(self, observacao=None):
        self._observacao = observacao
        self.chamadas = 0

    def obter_ffo(self, ticker, reference_date):
        self.chamadas += 1
        return self._observacao


def _patrimonio() -> PatrimonioFii:
    return PatrimonioFii(
        reference_date=REFERENCIA,
        net_asset_value=Decimal("1000"),
        shares_outstanding=Decimal("100"),
        cotistas=100,
        fonte="B3",
        vp_cota=Decimal("10"),
    )


def _campos_b3(classificacao: str = "Papel") -> dict[str, CampoFundamental]:
    return {
        CAMPO_DISCRIMINADOR: CampoFundamental("fii", "B3"),
        CAMPO_CLASSIFICACAO_FII: CampoFundamental(classificacao, "B3"),
        CAMPO_SEGMENTO: CampoFundamental("Outros", "B3"),
        CAMPO_GESTAO: CampoFundamental("Ativa", "B3"),
        CAMPO_VP_COTA: CampoFundamental(Decimal("9.468986"), "B3"),
    }


def _daily(com_janela: bool = True) -> dict[str, list[dict]]:
    if not com_janela:
        return {"CYCR11": []}
    return {
        "CYCR11": [
            {
                "date": date(2026, 8, 1),
                "min_price": Decimal("9.00"),
                "max_price": Decimal("9.50"),
                "last_price": Decimal("9.20"),
            },
            {
                "date": date(2026, 9, 1),
                "min_price": Decimal("9.10"),
                "max_price": Decimal("9.80"),
                "last_price": Decimal("9.47"),
            },
        ]
    }


def _caso(campos=None, ffo_provider=None, janela: bool = True, repo=None):
    return FundamentalAnalysisUseCase(
        repo or _Repo(proventos=[_rendimento("0.08")], patrimonio=_patrimonio()),
        ffo_provider=ffo_provider,
        mercado=B3MarketPriceFromResult(_daily(janela)),
        fundamental_provider=_Fonte(campos or _campos_b3()),
    )


class TestCotacaoEDataDeReferencia:
    def test_cotacao_preenchida_pelo_fechamento_b3(self):
        resultado = _caso().execute(["CYCR11"], REFERENCIA)[0]
        assert resultado.cotacao == Decimal("9.47")

    def test_data_referencia_usa_ultimo_fechamento(self):
        resultado = _caso().execute(["CYCR11"], REFERENCIA)[0]
        assert resultado.data_referencia == date(2026, 9, 1)

    def test_vp_cota_preenchido_pela_b3(self):
        resultado = _caso().execute(["CYCR11"], REFERENCIA)[0]
        assert resultado.vp_cota == Decimal("9.468986")


class TestClassificacaoExibicaoB3:
    def test_tipo_e_subtipo_para_cycr11(self):
        resultado = _caso().execute(["CYCR11"], REFERENCIA)[0]
        assert resultado.classificacao_exibicao.tipo == "FII"
        assert resultado.classificacao_exibicao.sub_tipo == "Papel: Outros, Ativa"

    def test_classificacao_tijolo_prefixa_tijolo(self):
        campos = _campos_b3("Tijolo")
        resultado = _caso(campos=campos).execute(["CYCR11"], REFERENCIA)[0]
        assert resultado.classificacao_exibicao.sub_tipo == "Tijolo: Outros, Ativa"


class TestPlDerivado:
    def test_p_l_derivado_de_preco_e_dividendo(self):
        resultado = _caso().execute(["CYCR11"], REFERENCIA)[0]
        esperado = Decimal("9.47") / (Decimal("0.08") * Decimal(12))
        assert resultado.p_l.quantize(Decimal("0.01")) == esperado.quantize(
            Decimal("0.01")
        )


class TestPrecoTipicoFallback:
    def test_extremos_da_janela_b3(self):
        resultado = _caso().execute(["CYCR11"], REFERENCIA)[0]
        esperado = (Decimal("9.80") + Decimal("9.00") + Decimal("9.47")) / Decimal(3)
        assert resultado.preco_tipico == esperado
        assert resultado.pct_preco_tipico is not None

    def test_janela_vazia_mantem_na(self):
        resultado = _caso(janela=False).execute(["CYCR11"], REFERENCIA)[0]
        assert resultado.preco_tipico is None
        assert resultado.pct_preco_tipico is None

    def test_extremos_do_fundamentus_tem_prioridade(self):
        campos = _campos_b3()
        campos[CAMPO_COTACAO] = CampoFundamental(Decimal("10"))
        campos[CAMPO_MIN_52_SEM] = CampoFundamental(Decimal("8"))
        campos[CAMPO_MAX_52_SEM] = CampoFundamental(Decimal("12"))
        resultado = _caso(campos=campos).execute(["CYCR11"], REFERENCIA)[0]
        assert resultado.cotacao == Decimal("10")
        assert resultado.preco_tipico == Decimal("10")


class TestElegibilidadeFfo:
    def test_papel_nao_aciona_motor(self):
        spy = _FfoSpy(
            FfoObservacao(ffo_12m=Decimal("100"), ffo_3m=Decimal("25"), fonte="CVM")
        )
        resultado = _caso(ffo_provider=spy).execute(["CYCR11"], REFERENCIA)[0]
        assert spy.chamadas == 0
        assert resultado.metricas is None or resultado.metricas.ffo_yield is None
        assert resultado.metricas is None or resultado.metricas.p_ffo is None
        assert resultado.metricas is None or resultado.metricas.ffo_trend is None

    def test_tijolo_aciona_motor(self):
        spy = _FfoSpy(
            FfoObservacao(ffo_12m=Decimal("100"), ffo_3m=Decimal("25"), fonte="CVM")
        )
        resultado = _caso(
            campos=_campos_b3("Tijolo"), ffo_provider=spy
        ).execute(["CYCR11"], REFERENCIA)[0]
        assert spy.chamadas == 1
        assert resultado.metricas is not None
        assert resultado.metricas.ffo_yield is not None
        assert resultado.metricas.p_ffo is not None

    def test_ffo_reportado_do_fundamentus_permanece_para_papel(self):
        spy = _FfoSpy(None)
        campos = _campos_b3("Papel")
        campos[CAMPO_FFO_YIELD] = CampoFundamental(Decimal("0.05"), "FUNDAMENTUS")
        campos[CAMPO_P_FFO] = CampoFundamental(Decimal("20"), "FUNDAMENTUS")
        resultado = _caso(campos=campos, ffo_provider=spy).execute(
            ["CYCR11"], REFERENCIA
        )[0]
        assert resultado.metricas is not None
        assert resultado.metricas.ffo_yield == Decimal("0.05")
        assert resultado.metricas.p_ffo == Decimal("20")
        assert spy.chamadas == 0


class TestColunasSemFallback:
    def test_colunas_sem_fallback_permanecem_na(self):
        resultado = _caso().execute(["CYCR11"], REFERENCIA)[0]
        assert resultado.lpa is None
        assert resultado.roe is None
        assert resultado.roic is None
        assert resultado.cap_rate is None
        assert resultado.vacancia_media is None
        assert resultado.qtd_imoveis is None
        assert resultado.cotacao is not None
        assert resultado.vp_cota is not None
        assert resultado.classificacao_exibicao.tipo == "FII"

    def test_papel_sem_fundamentus_mantem_derivados_na(self):
        caso = FundamentalAnalysisUseCase(
            _Repo(),
            mercado=B3MarketPriceFromResult(_daily()),
        )
        resultado = caso.execute(["PETR4"], REFERENCIA)[0]
        assert resultado.p_l is None
        assert resultado.ultimo_dividendo.valor is None
        assert resultado.dividendos_12m_por_cota is None
        assert resultado.metricas is None


class TestLinhaDaTabela:
    def test_cycr11_preenchido_e_ffo_na(self):
        from flowscope.presentation.gui.charts.fundamental_table import (
            NA,
            montar_linhas,
        )

        resultados = _caso().execute(["CYCR11"], REFERENCIA)
        linhas = montar_linhas({r.ticker: r for r in resultados})
        linha = linhas[0]
        assert linha[0] == "CYCR11"
        assert linha[2] == "FII"
        assert linha[3] == "Papel: Outros, Ativa"
        assert linha[4] != NA
        assert linha[7] != NA
        assert linha[9] != NA
        assert linha[15] == NA
        assert linha[17] == NA
        assert linha[18] == NA
        assert linha[23] != NA
