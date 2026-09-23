"""Testes do painel de evolução dos fundamentos."""

import os
import re
import tkinter as tk
import warnings
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from matplotlib.dates import date2num

from flowscope.application.fundamental_ports import (
    SCHEMA_VERSION_FUNDAMENTOS,
    ObservacaoFundamental,
)
from flowscope.domain.fii import (
    AnaliseFundamental,
    ClassificacaoAtivo,
    FonteClassificacao,
    MetricasFii,
    MetricasShort,
    Quality,
    TendenciaDividendo,
    TipoAtivo,
    UltimoDividendo,
)
from flowscope.presentation.gui.charts.fundamental_evolution_data import (
    TIPO_INTEIRO,
    TIPO_MONETARIO,
    TIPO_PERCENTUAL,
    TIPO_PERCENTUAL_1,
    TIPO_QUANTIDADE,
    TIPO_RAZAO,
    montar_series,
)
from flowscope.presentation.gui.charts.fundamental_evolution_panel import (
    FundamentalEvolutionPanel,
    formatar_ponto,
    selecionar_ticks,
)

BASE = date(2025, 1, 1)

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


def _metricas() -> MetricasFii:
    return MetricasFii(
        market_value=None,
        ffo_yield=None,
        dividend_yield=Decimal("0.09"),
        p_ffo=None,
        p_vp=Decimal("0.83"),
        ffo_momentum=None,
        ffo_trend=None,
        ffo_trend_change=None,
        ffo_payout=None,
        quality=Quality.COMPLETE,
        warnings=(),
        evidence=(),
    )


def _analise(
    cotacao: str, dividendo: str, shorts: str | None = None
) -> AnaliseFundamental:
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
            valor=Decimal(dividendo),
            valor_anterior=None,
            tendencia=TendenciaDividendo.N_A,
        ),
        dividendos_12m_por_cota=None,
        metricas=_metricas(),
        cotacao=Decimal(cotacao),
        vp_cota=Decimal("12"),
        cotistas=100000,
        cotas=Decimal("144355726"),
        short=(
            MetricasShort(shorts_pct=Decimal(shorts))
            if shorts is not None
            else None
        ),
    )


def _series():
    observacoes = [
        ObservacaoFundamental(
            ticker="HGBS11",
            data=BASE - timedelta(days=10),
            analise=_analise("9", "0.5"),
            schema_version=SCHEMA_VERSION_FUNDAMENTOS,
        ),
        ObservacaoFundamental(
            ticker="HGBS11",
            data=BASE,
            analise=_analise("10", "0.55"),
            schema_version=SCHEMA_VERSION_FUNDAMENTOS,
        ),
    ]
    return montar_series(observacoes)


def _series_com_shorts():
    observacoes = [
        ObservacaoFundamental(
            ticker="HGBS11",
            data=BASE - timedelta(days=10),
            analise=_analise("9", "0.5", shorts="0.05"),
            schema_version=SCHEMA_VERSION_FUNDAMENTOS,
        ),
        ObservacaoFundamental(
            ticker="HGBS11",
            data=BASE,
            analise=_analise("10", "0.55", shorts="0.1"),
            schema_version=SCHEMA_VERSION_FUNDAMENTOS,
        ),
    ]
    return montar_series(observacoes)


class TestFormatarPonto:
    def test_monetario(self):
        assert formatar_ponto(TIPO_MONETARIO, Decimal("10")) == "R$ 10,00"

    def test_percentual(self):
        assert formatar_ponto(TIPO_PERCENTUAL, Decimal("0.09")) == "9,00%"

    def test_percentual_uma_casa(self):
        assert formatar_ponto(TIPO_PERCENTUAL_1, Decimal("0.1")) == "10,0%"

    def test_razao(self):
        assert formatar_ponto(TIPO_RAZAO, Decimal("0.83")) == "0,83x"

    def test_inteiro(self):
        assert formatar_ponto(TIPO_INTEIRO, 100000) == "100.000"

    def test_quantidade(self):
        assert (
            formatar_ponto(TIPO_QUANTIDADE, Decimal("144355726"))
            == "144.355.726"
        )

    def test_tipo_desconhecido_usa_str(self):
        assert formatar_ponto("outro", 42) == "42"


class TestSelecionarTicks:
    def test_uma_data(self):
        assert selecionar_ticks([BASE]) == [BASE]

    def test_poucas_datas_retorna_todas(self):
        datas = [date(2025, 1, 1), date(2025, 1, 2)]
        assert selecionar_ticks(datas) == datas

    def test_limita_quantidade_e_inclui_extremos(self):
        datas = [date(2025, 1, 1) + timedelta(days=i) for i in range(10)]
        ticks = selecionar_ticks(datas, maximo=4)
        assert len(ticks) == 4
        assert ticks[0] == datas[0]
        assert ticks[-1] == datas[-1]
        assert ticks == sorted(set(ticks))


class TestFundamentalEvolutionPanel:
    @needs_display
    def test_update_monta_small_multiples_sem_erro(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            painel.update(_series(), ticker="HGBS11")
            assert painel._empty_label.get_visible() is False
            titulos = [ax.get_title() for ax in painel._axes]
            assert "Cotação (R$)" in titulos
            assert "Nº de cotas" in titulos
        finally:
            root.destroy()

    @needs_display
    def test_titulos_trazem_unidade_por_campo(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            painel.update(_series(), ticker="HGBS11")
            titulos = [ax.get_title() for ax in painel._axes]
            assert "Cotação (R$)" in titulos
            assert "VP (VP/Cota) (R$)" in titulos
            assert "P/VP" in titulos
            assert "Dividend Yield" in titulos
            assert "Último dividendo (R$)" in titulos
            assert "Nº de cotistas" in titulos
        finally:
            root.destroy()

    @needs_display
    def test_oito_paineis_incluindo_shorts(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            painel.update(_series(), ticker="HGBS11")
            assert len(painel._axes) == 8
            titulos = [ax.get_title() for ax in painel._axes]
            assert titulos[-1] == "Shorts%"
        finally:
            root.destroy()

    @needs_display
    def test_rotulos_de_data_com_dia_mes_e_ano(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            painel.update(_series(), ticker="HGBS11")
            for indice in (5, 6):
                textos = [
                    t.get_text()
                    for t in painel._axes[indice].get_xticklabels()
                ]
                assert textos
                assert all(
                    re.fullmatch(r"\d{2}/\d{2}/\d{2}", t) for t in textos
                )
            assert painel._axes[7].get_xticklabels() == []
        finally:
            root.destroy()

    @needs_display
    def test_rotulos_vao_para_o_ultimo_painel_com_dado(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            painel.update(_series_com_shorts(), ticker="HGBS11")
            textos = [t.get_text() for t in painel._axes[7].get_xticklabels()]
            assert textos
            assert all(re.fullmatch(r"\d{2}/\d{2}/\d{2}", t) for t in textos)
            assert painel._axes[5].get_xticklabels() == []
        finally:
            root.destroy()

    @needs_display
    def test_tooltip_dispara_redesenho_ao_aparecer(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            series = _series()
            painel.update(series, ticker="HGBS11")
            painel._canvas.draw_idle = MagicMock()
            ax = painel._axes[0]
            ponto = series[0].pontos[-1]
            x, y = ax.transData.transform(
                (date2num(ponto.data), float(ponto.valor))
            )
            painel._on_motion(SimpleNamespace(inaxes=ax, x=x, y=y))
            painel._canvas.draw_idle.assert_called()
        finally:
            root.destroy()

    @needs_display
    def test_tooltip_mostra_data_e_valor_e_some_distante(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            series = _series()
            painel.update(series, ticker="HGBS11")
            ax = painel._axes[0]
            ponto = series[0].pontos[-1]
            x, y = ax.transData.transform(
                (date2num(ponto.data), float(ponto.valor))
            )
            painel._on_motion(SimpleNamespace(inaxes=ax, x=x, y=y))
            anotacao = painel._anotacoes[0]
            assert anotacao.get_visible() is True
            texto = anotacao.get_text()
            assert "Data:" in texto
            assert "Valor: R$ 10,00" in texto
            painel._on_motion(
                SimpleNamespace(inaxes=ax, x=x - 500.0, y=y - 500.0)
            )
            assert anotacao.get_visible() is False
        finally:
            root.destroy()

    @needs_display
    def test_tooltip_oculto_fora_dos_eixos(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            painel.update(_series(), ticker="HGBS11")
            ax = painel._axes[0]
            x, y = ax.transData.transform((date2num(BASE), 10.0))
            painel._on_motion(SimpleNamespace(inaxes=ax, x=x, y=y))
            assert painel._anotacoes[0].get_visible() is True
            painel._on_motion(SimpleNamespace(inaxes=None, x=x, y=y))
            assert painel._anotacoes[0].get_visible() is False
        finally:
            root.destroy()

    @needs_display
    def test_anotacoes_zeradas_no_estado_vazio(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            painel.update(_series(), ticker="HGBS11")
            painel.update((), ticker="HGBS11")
            assert painel._anotacoes == [None] * len(painel._axes)
            assert painel._series_plot == [None] * len(painel._axes)
        finally:
            root.destroy()

    @needs_display
    def test_tooltip_sem_serie_nao_falha(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            painel.update(_series(), ticker="HGBS11")
            ax = painel._axes[7]
            assert painel._anotacoes[7] is None
            painel._on_motion(SimpleNamespace(inaxes=ax, x=10.0, y=10.0))
            assert painel._anotacoes[7] is None
        finally:
            root.destroy()

    @needs_display
    def test_motion_ignora_eixo_externo(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            painel.update(_series(), ticker="HGBS11")
            externo = painel._figure.add_axes([0.0, 0.0, 0.1, 0.1])
            assert painel._indice_do_eixo(externo) is None
            painel._on_motion(
                SimpleNamespace(inaxes=externo, x=1.0, y=1.0)
            )
            assert painel._indice_do_eixo(None) is None
        finally:
            root.destroy()

    @needs_display
    def test_estado_vazio_aparece_sem_historico(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            painel.update((), ticker="HGBS11")
            assert painel._empty_label.get_visible() is True
            assert "HGBS11" in painel._empty_label.get_text()
        finally:
            root.destroy()

    @needs_display
    def test_estado_vazio_some_com_historico(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            painel.update((), ticker="HGBS11")
            painel.update(_series(), ticker="HGBS11")
            assert painel._empty_label.get_visible() is False
        finally:
            root.destroy()

    @needs_display
    def test_reset_exibe_estado_vazio(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            painel.update(_series(), ticker="HGBS11")
            painel.reset()
            assert painel._empty_label.get_visible() is True
        finally:
            root.destroy()

    @needs_display
    def test_sem_aviso_do_autodatelocator_com_uma_data(self):
        root = tk.Tk()
        try:
            painel = FundamentalEvolutionPanel(root)
            series = montar_series(
                [
                    ObservacaoFundamental(
                        ticker="HGBS11",
                        data=BASE,
                        analise=_analise("10", "0.55"),
                        schema_version=SCHEMA_VERSION_FUNDAMENTOS,
                    )
                ]
            )
            with warnings.catch_warnings():
                warnings.filterwarnings("error", message=".*AutoDateLocator.*")
                painel.update(series, ticker="HGBS11")
        finally:
            root.destroy()

    @needs_display
    def test_toolbar_copia_grafico(self):
        root = tk.Tk()
        try:
            copiados = []
            painel = FundamentalEvolutionPanel(
                root, copy_chart_callback=copiados.append
            )
            painel._toolbar.copy_chart()
            assert copiados == [painel.get_figure()]
        finally:
            root.destroy()
