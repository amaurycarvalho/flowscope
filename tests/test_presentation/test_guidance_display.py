"""Testes da exibição do guidance na coluna Informações adicionais."""

from datetime import date
from decimal import Decimal

from flowscope.domain.fii import (
    AnaliseFundamental,
    Guidance,
    TendenciaDividendo,
    UltimoDividendo,
    classificar_ticker,
)
from flowscope.presentation.gui.charts.fundamental_table import (
    montar_csv,
    montar_linhas,
)

_INDICE_INFO = 28


def _analise(ticker: str, guidance: Guidance | None) -> AnaliseFundamental:
    return AnaliseFundamental(
        ticker=ticker,
        nome="Fundo Teste",
        classificacao=classificar_ticker(ticker),
        ultimo_dividendo=UltimoDividendo(
            data_com=None,
            valor=None,
            valor_anterior=None,
            tendencia=TendenciaDividendo.N_A,
        ),
        dividendos_12m_por_cota=None,
        metricas=None,
        guidance=guidance,
    )


def _coluna_info(ticker: str, guidance: Guidance | None) -> str:
    linhas = montar_linhas({ticker: _analise(ticker, guidance)})
    return linhas[0][_INDICE_INFO]


class TestExibicao:
    def test_faixa_com_periodo_e_mes_ano(self):
        guidance = Guidance(
            valor_min=Decimal("0.74"),
            valor_max=Decimal("0.78"),
            periodo="restante do ano de 2026",
            data_relatorio=date(2026, 8, 1),
        )
        assert (
            _coluna_info("HGBS11", guidance)
            == "Guidance R$ 0,74 a R$ 0,78/cota (restante do ano de 2026, ago/26)"
        )

    def test_valor_unico(self):
        guidance = Guidance(
            valor_min=Decimal("0.85"),
            valor_max=Decimal("0.85"),
            periodo="2S26",
            data_relatorio=date(2026, 8, 1),
        )
        assert (
            _coluna_info("HGBS11", guidance)
            == "Guidance R$ 0,85/cota (2S26, ago/26)"
        )

    def test_sem_periodo_exibe_apenas_mes_ano(self):
        guidance = Guidance(
            valor_min=Decimal("0.85"),
            valor_max=Decimal("0.85"),
            periodo="",
            data_relatorio=date(2026, 1, 1),
        )
        assert _coluna_info("HGBS11", guidance) == "Guidance R$ 0,85/cota (jan/26)"

    def test_ausencia_omite_o_item(self):
        assert _coluna_info("HGBS11", None) == "N/A"

    def test_papel_nao_exibe_guidance(self):
        guidance = Guidance(
            valor_min=Decimal("0.85"),
            valor_max=Decimal("0.85"),
            periodo="2S26",
            data_relatorio=date(2026, 8, 1),
        )
        assert "Guidance" not in _coluna_info("PETR4", guidance)


class TestCsv:
    def test_csv_replica_o_texto_exibido(self):
        guidance = Guidance(
            valor_min=Decimal("0.74"),
            valor_max=Decimal("0.78"),
            periodo="restante do ano de 2026",
            data_relatorio=date(2026, 8, 1),
        )
        csv = montar_csv({"HGBS11": _analise("HGBS11", guidance)})
        assert (
            "Guidance R$ 0,74 a R$ 0,78/cota (restante do ano de 2026, ago/26)"
            in csv
        )
