import os
import tkinter as tk
from datetime import date
from decimal import Decimal
from tkinter import ttk

import pytest

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.domain.fii import (
    AnaliseFundamental,
    ClasseCotistas,
    ClassePatrimonio,
    FiiSnapshot,
    FfoObservacao,
    PatrimonioFii,
    PrecoObservacao,
    TendenciaDividendo,
    UltimoDividendo,
    analisar_snapshot,
    classificar_exibicao,
    classificar_ticker,
)
from flowscope.domain.structured import ISIN, Provento, ValorProvento
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.app_tabs import TAB_CONTENT
from flowscope.presentation.gui.charts.fundamental_table import (
    FundamentalTablePanel,
    formatar_data,
    formatar_inteiro,
    formatar_patrimonio,
    formatar_percentual,
    formatar_ratio,
    formatar_valor,
    montar_csv,
    montar_linhas,
    rotulo_classe_cotistas,
    rotulo_classe_patrimonio,
)

NA = "N/A"
_ISIN = "BR0000000000"


def _provento(tipo: str, data_base: date, valor: str) -> Provento:
    return Provento(
        codigo_isin=ISIN(_ISIN),
        codigo_negociacao="X",
        tipo=tipo,
        data_base=data_base,
        valor_por_unidade=ValorProvento(Decimal(valor)),
        data_pagamento=data_base,
        periodo_referencia="",
        isento_ir=True,
    )


def _analise_hgbs11() -> AnaliseFundamental:
    metricas = analisar_snapshot(
        FiiSnapshot(
            ticker="HGBS11",
            reference_date=date(2026, 9, 4),
            price=Decimal("18.74"),
            shares_outstanding=Decimal("144355726"),
            net_asset_value=Decimal("2942000000"),
            ffo_12m=Decimal("220777000"),
            ffo_3m=Decimal("63802000"),
            dividends_12m=Decimal("213080000"),
        )
    )
    return AnaliseFundamental(
        ticker="HGBS11",
        nome="CSHG Renda Urbana",
        classificacao=classificar_ticker("HGBS11"),
        ultimo_dividendo=UltimoDividendo(
            data_com=date(2026, 7, 10),
            valor=Decimal("0.55"),
            valor_anterior=Decimal("0.50"),
            tendencia=TendenciaDividendo.CRESCIMENTO,
        ),
        dividendos_12m_por_cota=Decimal("1.05"),
        metricas=metricas,
    )


def _analise_acao() -> AnaliseFundamental:
    return AnaliseFundamental(
        ticker="PETR4",
        nome="Petrobras PN",
        classificacao=classificar_ticker("PETR4"),
        ultimo_dividendo=UltimoDividendo(
            data_com=None,
            valor=None,
            valor_anterior=None,
            tendencia=TendenciaDividendo.N_A,
        ),
        dividendos_12m_por_cota=None,
        metricas=None,
    )


class TestFormatadores:
    def test_formatar_valor_na(self):
        assert formatar_valor(None) == NA

    def test_formatar_valor_com_virgula(self):
        assert formatar_valor(Decimal("0.55")) == "0,55"
        assert formatar_valor(Decimal("0.08355")) == "0,08"
        assert formatar_valor(Decimal("0.7")) == "0,70"
        assert formatar_valor(Decimal("15.5")) == "15,50"
        assert formatar_valor(Decimal("9")) == "9,00"

    def test_formatar_data_na(self):
        assert formatar_data(None) == NA

    def test_formatar_data_brasileira(self):
        assert formatar_data(date(2026, 7, 10)) == "10/07/2026"

    def test_formatar_percentual(self):
        assert formatar_percentual(Decimal("0.0816")) == "8,16%"
        assert formatar_percentual(None) == NA

    def test_formatar_ratio(self):
        assert formatar_ratio(Decimal("12.25")) == "12,25x"
        assert formatar_ratio(None) == NA

    def test_formatar_inteiro(self):
        assert formatar_inteiro(100000) == "100.000"
        assert formatar_inteiro(None) == NA

    def test_formatar_patrimonio(self):
        assert formatar_patrimonio(Decimal("2942000000")) == "R$ 2,94 bi"
        assert formatar_patrimonio(Decimal("150000000")) == "R$ 150,00 mi"
        assert formatar_patrimonio(Decimal("250000")) == "R$ 250.000,00"
        assert formatar_patrimonio(None) == NA

    def test_rotulos_de_classe(self):
        assert rotulo_classe_cotistas(ClasseCotistas.MEDIO) == "Médio"
        assert rotulo_classe_patrimonio(ClassePatrimonio.GIGANTE) == "Gigante"
        assert rotulo_classe_cotistas(None) == NA
        assert rotulo_classe_patrimonio(None) == NA


class TestClassificacaoExibicao:
    def test_fii_tijolo_usa_prefixo_tijolo(self):
        resultado = classificar_exibicao(
            discriminador="fii",
            segmento="Shoppings",
            gestao="Ativa",
            qtd_imoveis=16,
        )
        assert resultado.tipo == "FII"
        assert resultado.sub_tipo == "Tijolo: Shoppings, Ativa"

    def test_fii_papel_usa_prefixo_papel(self):
        resultado = classificar_exibicao(
            discriminador="fii",
            segmento="Multicategoria",
            gestao="Ativa",
            qtd_imoveis=0,
        )
        assert resultado.sub_tipo == "Papel: Multicategoria, Ativa"

    def test_fii_sem_imoveis_usa_papel(self):
        resultado = classificar_exibicao(
            discriminador="fii",
            segmento="Shoppings",
            gestao="Ativa",
            qtd_imoveis=None,
        )
        assert resultado.sub_tipo.startswith("Papel: ")

    def test_papel_concatena_especie_setor_subsetor(self):
        resultado = classificar_exibicao(
            discriminador="papel",
            especie="PN",
            setor="Petróleo, Gás e Biocombustíveis",
            subsetor="Exploração, Refino e Distribuição",
        )
        assert resultado.tipo == "Papel"
        assert resultado.sub_tipo == (
            "PN, Petróleo, Gás e Biocombustíveis, Exploração, Refino e Distribuição"
        )

    def test_fallback_taxonomia_quando_sem_discriminador(self):
        resultado = classificar_exibicao(
            discriminador=None, fallback=classificar_ticker("HGBS11")
        )
        assert resultado.tipo == "FII"
        assert resultado.sub_tipo == "Tijolo"

    def test_fallback_acao(self):
        resultado = classificar_exibicao(
            discriminador=None, fallback=classificar_ticker("PETR4")
        )
        assert resultado.tipo == "Papel"
        assert resultado.sub_tipo == "Preferencial"

    def test_sem_fallback_e_desconhecido(self):
        resultado = classificar_exibicao(discriminador=None)
        assert resultado.tipo == "Desconhecido"
        assert resultado.sub_tipo is None


class TestMontarLinhas:
    def test_linha_de_fii_elegivel_preenche_ffo(self):
        linhas = montar_linhas({"HGBS11": _analise_hgbs11()})
        assert len(linhas) == 1
        colunas = linhas[0]
        assert colunas[0] == "HGBS11"
        assert colunas[1] == "CSHG Renda Urbana"
        assert colunas[2] == "FII"
        assert colunas[3] == "Tijolo"
        assert colunas[4] == "10/07/2026"
        assert colunas[5] == "0,55"
        assert colunas[6] == "0,50"
        assert colunas[7] == "Crescimento"
        assert colunas[8] == "8,16%"
        assert colunas[9] == "7,9%"
        assert colunas[10] == "96,51%"
        assert colunas[11] == "ALTA"
        assert colunas[12] == NA
        assert colunas[13] == NA
        assert colunas[14] == "12,25x"
        assert colunas[15] == "0,92x"

    def test_linha_de_acao_fica_na_nas_colunas_ffo_e_dividendo(self):
        linhas = montar_linhas({"PETR4": _analise_acao()})
        colunas = linhas[0]
        assert colunas[2] == "Papel"
        assert colunas[3] == "Preferencial"
        assert colunas[4] == NA
        assert colunas[5] == NA
        assert colunas[6] == NA
        assert colunas[7] == "N/A"
        assert all(coluna == NA for coluna in colunas[8:])

    def test_ordem_das_linhas_preserva_ordem_da_watchlist(self):
        linhas = montar_linhas(
            {"HGBS11": _analise_hgbs11(), "PETR4": _analise_acao()}
        )
        assert [linha[0] for linha in linhas] == ["HGBS11", "PETR4"]

    def test_payload_sintetico_usa_classificacao_offline(self):
        linhas = montar_linhas({"VALE3": {"daily_data": []}})
        colunas = linhas[0]
        assert colunas[0] == "VALE3"
        assert colunas[2] == "Papel"
        assert colunas[3] == "Ordinária"
        assert all(coluna == NA for coluna in colunas[4:])


class TestMontarCsv:
    def test_cabecalho_corresponde_as_colunas_da_tabela(self):
        csv = montar_csv({"HGBS11": _analise_hgbs11()})
        assert csv.split("\n")[0] == (
            "Ticker;Nome;Tipo;Sub-tipo;Última data-com;Último dividendo;"
            "Dividendo anterior;Tendência do dividendo;FFO Yield;Dividend Yield;"
            "Dividend Payout (DY/FFOY);FFO Trend;P (Cotação);VP (VP/Cota);"
            "P/FFO;P/VP;Nº de cotistas;Classe de cotistas;Patrimônio;"
            "Classe de patrimônio;Data de referência"
        )

    def test_linhas_preservam_ordem_e_valores_formatados(self):
        csv = montar_csv(
            {"HGBS11": _analise_hgbs11(), "PETR4": _analise_acao()}
        )
        linhas = csv.split("\n")
        assert linhas[1].startswith(
            "HGBS11;CSHG Renda Urbana;FII;Tijolo;10/07/2026;0,55;0,50;Crescimento;8,16%"
        )
        assert linhas[2].startswith("PETR4;Petrobras PN;Papel;Preferencial;")

    def test_csv_usa_duas_casas_decimais(self):
        csv = montar_csv({"HGBS11": _analise_hgbs11()})
        campos = csv.split("\n")[1].split(";")
        assert campos[5] == "0,55"
        assert campos[6] == "0,50"
        assert campos[10] == "96,51%"

    def test_vazio_retorna_apenas_cabecalho(self):
        csv = montar_csv({})
        assert "\n" not in csv
        assert csv.startswith("Ticker;Nome;")

    def test_delimiter_customizado(self):
        csv = montar_csv({"PETR4": _analise_acao()}, delimiter=",")
        assert csv.split("\n")[0].startswith("Ticker,Nome,")


needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


class TestFundamentalTablePanel:
    @needs_display
    def test_update_popula_treeview(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.update({"HGBS11": _analise_hgbs11(), "PETR4": _analise_acao()})
            filhos = painel._tree.get_children()
            assert len(filhos) == 2
            valores = painel._tree.item(filhos[0], "values")
            assert valores[0] == "HGBS11"
            assert valores[8] == "8,16%"
        finally:
            root.destroy()

    @needs_display
    def test_update_vazio_limpa_treeview(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.update({"HGBS11": _analise_hgbs11()})
            painel.reset()
            assert len(painel._tree.get_children()) == 0
        finally:
            root.destroy()

    @needs_display
    def test_painel_aplica_larguras_iniciais(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root, widths={"ticker": 200})
            assert painel.get_column_widths()["ticker"] == 200
        finally:
            root.destroy()

    @needs_display
    def test_painel_usa_largura_padrao_sem_preferencia(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            assert painel.get_column_widths()["ticker"] == 140
        finally:
            root.destroy()

    @needs_display
    def test_painel_notifica_mudanca_de_largura(self):
        root = tk.Tk()
        try:
            registradas = []
            painel = FundamentalTablePanel(
                root, on_widths_changed=registradas.append
            )
            painel._tree.column("ticker", width=222)
            painel._on_column_resized()
            assert registradas and registradas[-1]["ticker"] == 222
        finally:
            root.destroy()

    @needs_display
    def test_painel_alinhamento_das_colunas(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            direita = {
                "ultimo_dividendo",
                "dividendo_anterior",
                "ffo_yield",
                "dividend_yield",
                "dividend_payout",
                "p",
                "vp",
                "p_ffo",
                "p_vp",
                "cotistas",
                "patrimonio",
            }
            for coluna_id in painel._columns:
                esperado = "e" if coluna_id in direita else "w"
                assert str(painel._tree.column(coluna_id, "anchor")) == esperado
        finally:
            root.destroy()


class _FakeRepo:
    def __init__(self):
        self.proventos = {
            "HGBS11": [
                _provento("Rendimento", date(2026, 7, 10), "0.55"),
                _provento("Rendimento", date(2026, 1, 15), "0.50"),
            ],
            "HCRI11": [
                _provento("Rendimento", date(2026, 3, 10), "1.00"),
            ],
        }
        self.patrimonio = {
            "HGBS11": PatrimonioFii(
                reference_date=date(2026, 9, 4),
                net_asset_value=Decimal("2942000000"),
                shares_outstanding=Decimal("144355726"),
                cotistas=100000,
                fonte="CVM",
            ),
        }

    def obter_nome(self, ticker):
        nomes = {
            "HGBS11": "CSHG Renda Urbana",
            "HCRI11": "CSHG Recebíveis Imobiliários",
            "PETR4": "Petrobras PN",
        }
        return nomes.get(ticker)

    def obter_proventos(self, ticker, reference_date):
        return self.proventos.get(ticker, [])

    def obter_patrimonio(self, ticker, reference_date):
        return self.patrimonio.get(ticker)


class _FakeFfo:
    def obter_ffo(self, ticker, reference_date):
        if ticker == "HGBS11":
            return FfoObservacao(
                ffo_12m=Decimal("220777000"),
                ffo_3m=Decimal("63802000"),
                fonte="FUNDAMENTUS",
            )
        return None


class _FakeMercado:
    def preco_fechamento(self, ticker, reference_date):
        if ticker == "HGBS11":
            return PrecoObservacao(
                preco=Decimal("18.74"),
                data_preco=reference_date,
                fonte="B3",
            )
        return None


class TestIntegracaoWatchlist:
    def test_watchlist_com_fiis_e_acoes(self):
        caso = FundamentalAnalysisUseCase(
            repository=_FakeRepo(),
            ffo_provider=_FakeFfo(),
            mercado=_FakeMercado(),
        )
        resultados = caso.execute(["PETR4", "HCRI11", "HGBS11"], date(2026, 9, 4))
        linhas = montar_linhas(
            {resultado.ticker: resultado for resultado in resultados}
        )
        por_ticker = {linha[0]: linha for linha in linhas}

        petr = por_ticker["PETR4"]
        assert petr[2] == "Papel"
        assert petr[4] == NA
        assert petr[5] == NA
        assert petr[6] == NA
        assert petr[7] == "N/A"
        assert all(coluna == NA for coluna in petr[8:])

        hcri = por_ticker["HCRI11"]
        assert hcri[2] == "FII"
        assert hcri[3] == "Papel"
        assert hcri[5] == "1,00"
        assert all(coluna == NA for coluna in hcri[8:])

        hgbs = por_ticker["HGBS11"]
        assert hgbs[2] == "FII"
        assert hgbs[3] == "Tijolo"
        assert hgbs[5] == "0,55"
        assert hgbs[6] == "0,50"
        assert hgbs[7] == "Crescimento"
        assert hgbs[8] == "8,16%"
        assert hgbs[9] == "5,6%"
        assert hgbs[10] == "68,65%"
        assert hgbs[11] == "ALTA"
        assert hgbs[14] == "12,25x"
        assert hgbs[15] == "0,92x"
        assert hgbs[16] == "100.000"
        assert hgbs[17] == "Muito grande"
        assert hgbs[18] == "R$ 2,94 bi"
        assert hgbs[19] == "Gigante"


class TestWiringSubAba:
    def test_tab_content_fundamentos_existe(self):
        assert ("Análise Geral", "Fundamentos") in TAB_CONTENT
        titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        assert "Fundamentos" in titulo
        assert isinstance(corpo, list) and len(corpo) > 0

    @needs_display
    def test_sub_aba_fundamentos_aparece_na_analise_geral(self):
        root = tk.Tk()
        try:
            host = TabsLayoutMixin()
            host._general_notebook = ttk.Notebook(root)
            host._copy_chart = lambda _figure: None
            host._on_quadrant_summary = lambda *_args: None
            host._build_general_tabs()
            abas = [
                host._general_notebook.tab(indice, "text")
                for indice in range(host._general_notebook.index("end"))
            ]
            assert "Fundamentos" in abas
            assert hasattr(host, "_fundamental_table")
        finally:
            root.destroy()
