"""Testes de integração da sub-aba de evolução dos fundamentos."""

import os
import tkinter as tk
from datetime import date
from decimal import Decimal
from tkinter import ttk
from unittest.mock import MagicMock

import pytest

from flowscope.application.fundamental_ports import (
    SCHEMA_VERSION_FUNDAMENTOS,
    ObservacaoFundamental,
)
from flowscope.domain.fii import (
    AnaliseFundamental,
    ClassificacaoAtivo,
    FonteClassificacao,
    TendenciaDividendo,
    TipoAtivo,
    UltimoDividendo,
)
from flowscope.presentation.gui.app_actions import ActionsMixin
from flowscope.presentation.gui.app_tab_actions import TabActionsMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.app_tabs import (
    ENABLED_TABS,
    TAB_CONFIGS,
    TAB_CONTENT,
)
from flowscope.presentation.gui.charts.fundamental_table import FundamentalTablePanel

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


class _Host(TabActionsMixin, TabsLayoutMixin):
    """Combina os mixins usados na construção e navegação das abas."""


def _analise(ticker: str) -> AnaliseFundamental:
    return AnaliseFundamental(
        ticker=ticker,
        nome=None,
        classificacao=ClassificacaoAtivo(
            ticker=ticker,
            tipo=TipoAtivo.FII,
            sub_tipo=None,
            fonte=FonteClassificacao.TAXONOMIA_FII,
        ),
        ultimo_dividendo=UltimoDividendo(
            data_com=None,
            valor=Decimal("0.55"),
            valor_anterior=None,
            tendencia=TendenciaDividendo.N_A,
        ),
        dividendos_12m_por_cota=None,
        metricas=None,
        cotacao=Decimal("10"),
    )


class _FakeStore:
    def __init__(self):
        self._obs = [
            ObservacaoFundamental(
                ticker="HGBS11",
                data=date(2025, 1, 1),
                analise=_analise("HGBS11"),
                schema_version=SCHEMA_VERSION_FUNDAMENTOS,
            )
        ]

    def datas(self, ticker):
        return [o.data for o in self._obs]

    def historico(self, ticker, inicio, fim):
        return list(self._obs)


class TestWiringSubAba:
    def test_evolucao_registrada_em_tab_configs(self):
        nomes = [config[0] for config in TAB_CONFIGS]
        assert "Evolução dos Fundamentos" in nomes
        assert "Evolução dos Fundamentos" in ENABLED_TABS

    @needs_display
    def test_sub_aba_evolucao_aparece_na_analise_do_ticker(self):
        root = tk.Tk()
        try:
            host = _Host()
            host._main_notebook = ttk.Notebook(root)
            host._copy_chart = lambda _figure: None
            host._build_ticker_tabs()
            abas = [
                host._ticker_notebook.tab(indice, "text")
                for indice in range(host._ticker_notebook.index("end"))
            ]
            assert "Evolução dos Fundamentos" in abas
            assert hasattr(host, "_fundamental_evolution_panel")
        finally:
            root.destroy()


class TestOrdemSubAbas:
    def test_configs_ordenam_implementadas_primeiro(self):
        nomes = [config[0] for config in TAB_CONFIGS]
        implementadas = [nome for nome in nomes if nome in ENABLED_TABS]
        assert implementadas == [
            "Evolução dos Fundamentos",
            "Evolução da Dominância",
            "Amplitude de Preço",
            "Fluxo Financeiro",
            "Documentos",
        ]

    @needs_display
    def test_sub_abas_visiveis_e_ordem(self):
        root = tk.Tk()
        try:
            host = _Host()
            host._main_notebook = ttk.Notebook(root)
            host._copy_chart = lambda _figure: None
            host._build_ticker_tabs()
            abas = [
                host._ticker_notebook.tab(indice, "text")
                for indice in range(host._ticker_notebook.index("end"))
            ]
            assert abas == [
                "Evolução dos Fundamentos",
                "Evolução da Dominância",
                "Amplitude de Preço",
                "Fluxo Financeiro",
                "Documentos",
            ]
            for oculta in (
                "Participação Institucional",
                "Eficiência do Movimento",
                "Resumo Geral",
            ):
                assert oculta not in abas
        finally:
            root.destroy()


class TestDoubleClickTabela:
    @needs_display
    def test_callback_recebe_ticker_da_linha(self):
        root = tk.Tk()
        try:
            registros = []
            painel = FundamentalTablePanel(root, on_row_activated=registros.append)
            painel.update({"HGBS11": _analise("HGBS11")})
            painel._tree_fixo.selection_set("HGBS11")

            class _Evento:
                widget = painel._tree_fixo

            assert painel._on_row_double_click(_Evento()) == "break"
            assert registros == ["HGBS11"]
        finally:
            root.destroy()

    @needs_display
    def test_callback_no_painel_rolavel(self):
        root = tk.Tk()
        try:
            registros = []
            painel = FundamentalTablePanel(root, on_row_activated=registros.append)
            painel.update({"PETR4": _analise("PETR4")})
            painel._tree_rolavel.selection_set("PETR4")

            class _Evento:
                widget = painel._tree_rolavel

            painel._on_row_double_click(_Evento())
            assert registros == ["PETR4"]
        finally:
            root.destroy()

    @needs_display
    def test_sem_callback_nao_falha(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.update({"HGBS11": _analise("HGBS11")})
            painel._tree_fixo.selection_set("HGBS11")

            class _Evento:
                widget = painel._tree_fixo

            assert painel._on_row_double_click(_Evento()) == "break"
        finally:
            root.destroy()


class TestHandlerDuploClique:
    @needs_display
    def test_fixa_ticker_e_ativa_sub_aba(self):
        root = tk.Tk()
        try:
            host = _Host()
            host._main_notebook = ttk.Notebook(root)
            host._main_notebook.add(ttk.Frame(root), text="Análise Geral")
            host._main_notebook.add(ttk.Frame(root), text="Análise do Ticker")
            host._ticker_notebook = ttk.Notebook(root)
            host._ticker_notebook.add(ttk.Frame(root), text="Evolução da Dominância")
            host._ticker_notebook.add(
                ttk.Frame(root), text="Evolução dos Fundamentos"
            )

            host._on_fundamental_row_activated("HGBS11")

            assert host._ticker_selecionado == "HGBS11"
            assert host._main_notebook.tab(
                host._main_notebook.select(), "text"
            ) == "Análise do Ticker"
            assert host._ticker_notebook.tab(
                host._ticker_notebook.select(), "text"
            ) == "Evolução dos Fundamentos"
        finally:
            root.destroy()

    def test_ticker_vazio_ignorado(self):
        host = _Host()
        host._main_notebook = MagicMock()
        host._on_fundamental_row_activated("")
        host._main_notebook.select.assert_not_called()


class TestUpdateFundamentalEvolution:
    def test_preenche_a_partir_do_store(self):
        host = ActionsMixin()
        host._fundamental_evolution_panel = MagicMock()
        host._ticker_selecionado = "HGBS11"
        host._fundamental_history_store = _FakeStore()

        host._update_fundamental_evolution()

        series, kwargs = host._fundamental_evolution_panel.update.call_args
        assert kwargs["ticker"] == "HGBS11"
        assert len(series[0]) == 7

    def test_sem_historico_usa_estado_vazio(self):
        host = ActionsMixin()
        host._fundamental_evolution_panel = MagicMock()
        host._ticker_selecionado = "HGBS11"

        class _Vazio:
            def datas(self, ticker):
                return []

            def historico(self, ticker, inicio, fim):
                return []

        host._fundamental_history_store = _Vazio()
        host._update_fundamental_evolution()

        host._fundamental_evolution_panel.update.assert_called_once_with(
            (), ticker="HGBS11"
        )

    def test_sem_store_usa_estado_vazio(self):
        host = ActionsMixin()
        host._fundamental_evolution_panel = MagicMock()
        host._ticker_selecionado = "HGBS11"

        host._update_fundamental_evolution()

        host._fundamental_evolution_panel.update.assert_called_once_with(
            (), ticker="HGBS11"
        )

    def test_sem_ticker_selecionado_nao_usa_fallback_da_lista(self):
        host = ActionsMixin()
        host._fundamental_evolution_panel = MagicMock()
        host._ticker_selecionado = None
        host._ticker_list = MagicMock()
        host._ticker_list.get_tickers.return_value = ["PETR4"]
        host._fundamental_history_store = _FakeStore()

        host._update_fundamental_evolution()

        _args, kwargs = host._fundamental_evolution_panel.update.call_args
        assert kwargs["ticker"] is None

    def test_do_update_despacha_para_evolucao(self):
        host = ActionsMixin()
        host._ticker_list = MagicMock()
        host._ticker_list.get_tickers.return_value = []
        host._current_data = {}
        host._ticker_charts = set()
        host._fundamental_evolution_panel = MagicMock()
        host._fundamental_evolution_panel.update = MagicMock()
        host._ticker_selecionado = "HGBS11"
        host._fundamental_history_store = _FakeStore()

        host._do_update(host._fundamental_evolution_panel)

        host._fundamental_evolution_panel.update.assert_called_once()


class TestSincronizarSelecaoFundamental:
    def test_preserva_ticker_presente(self):
        host = ActionsMixin()
        host._ticker_selecionado = "VALE3"
        host._fundamental_table = MagicMock()
        host._fundamental_table.has_ticker.return_value = True

        host._sincronizar_selecao_fundamental()

        host._fundamental_table.select_ticker.assert_called_once_with("VALE3")
        host._fundamental_table.first_ticker.assert_not_called()

    def test_auto_seleciona_primeiro(self):
        host = ActionsMixin()
        host._ticker_selecionado = None
        host._fundamental_table = MagicMock()
        host._fundamental_table.first_ticker.return_value = "AAA00"

        host._sincronizar_selecao_fundamental()

        assert host._ticker_selecionado == "AAA00"
        host._fundamental_table.select_ticker.assert_called_once_with("AAA00")

    def test_sem_linhas_limpa_selecao(self):
        host = ActionsMixin()
        host._ticker_selecionado = "VALE3"
        host._fundamental_table = MagicMock()
        host._fundamental_table.has_ticker.return_value = False
        host._fundamental_table.first_ticker.return_value = None

        host._sincronizar_selecao_fundamental()

        assert host._ticker_selecionado is None
        host._fundamental_table.select_ticker.assert_not_called()

    def test_sem_tabela_nao_falha(self):
        host = ActionsMixin()
        host._sincronizar_selecao_fundamental()


class TestSetFundamentalData:
    def test_adota_primeiro_quando_sem_selecao(self):
        host = ActionsMixin()
        host._ticker_selecionado = None
        host.set_fundamental_data({"PETR4": {}, "VALE3": {}})
        assert host._ticker_selecionado == "PETR4"

    def test_preserva_selecao_valida(self):
        host = ActionsMixin()
        host._ticker_selecionado = "VALE3"
        host.set_fundamental_data({"PETR4": {}, "VALE3": {}})
        assert host._ticker_selecionado == "VALE3"

    def test_sem_dados_limpa_selecao(self):
        host = ActionsMixin()
        host._ticker_selecionado = "PETR4"
        host.set_fundamental_data({})
        assert host._ticker_selecionado is None


class TestDeveAtualizar:
    def test_evolucao_atualiza_sem_dados_b3(self):
        host = TabActionsMixin()
        host._current_data = {}
        host._fundamental_evolution_panel = object()
        assert host._deve_atualizar(host._fundamental_evolution_panel) is True

    def test_outros_paineis_nao_atualizam_sem_dados(self):
        host = TabActionsMixin()
        host._current_data = {}
        host._fundamental_evolution_panel = object()
        assert host._deve_atualizar(object()) is False

    def test_com_dados_todos_atualizam(self):
        host = TabActionsMixin()
        host._current_data = {"x": 1}
        host._fundamental_evolution_panel = object()
        assert host._deve_atualizar(object()) is True


class TestPinTicker:
    def test_editar_tickers_preserva_ticker_selecionado(self):
        host = TabActionsMixin()
        host._ticker_selecionado = "HGBS11"
        host._controller = MagicMock()

        host._on_ticker_edit()

        assert host._ticker_selecionado == "HGBS11"
        host._controller.on_ticker_edit.assert_called_once()

    def test_select_tab_inexistente_retorna_false(self):
        notebook = MagicMock()
        notebook.index.return_value = 0
        notebook.tab.return_value = "Outra"
        assert TabActionsMixin._select_tab(notebook, "Evolução dos Fundamentos") is False


class TestOrientationText:
    def test_conteudo_existe(self):
        chave = ("Análise do Ticker", "Evolução dos Fundamentos")
        assert chave in TAB_CONTENT
        titulo, corpo = TAB_CONTENT[chave]
        assert "Evolução dos Fundamentos" in titulo
        assert isinstance(corpo, list) and corpo

    def test_explica_amostragem_e_origem(self):
        _titulo, corpo = TAB_CONTENT[("Análise do Ticker", "Evolução dos Fundamentos")]
        texto = " ".join(parte for parte, _estilo in corpo)
        assert "small multiples" in texto
        assert "Fibonacci" in texto
        assert "cache" in texto
        assert "Nº de cotistas" in texto
