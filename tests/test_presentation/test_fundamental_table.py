import os
import tkinter as tk
from dataclasses import replace
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
    MargensFii,
    MotivoMargem,
    PatrimonioFii,
    PrecoObservacao,
    ResultadoMargem,
    TendenciaDividendo,
    TendenciaFfo,
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
    formatar_margem,
    formatar_patrimonio,
    formatar_percentual,
    formatar_quantidade,
    formatar_ratio,
    formatar_valor,
    montar_csv,
    montar_linhas,
    rotulo_classe_cotistas,
    rotulo_classe_patrimonio,
    rotulo_tendencia,
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


def _margens_hgbs11() -> MargensFii:
    return MargensFii(
        ffo_receita_12m=ResultadoMargem(Decimal("0.873")),
        ffo_receita_3m=ResultadoMargem(Decimal("0.855")),
        dividendos_receita_12m=ResultadoMargem(Decimal("1.157")),
        dividendos_receita_3m=ResultadoMargem(Decimal("0.768")),
        dividendos_ffo_12m=ResultadoMargem(Decimal("1.326")),
        dividendos_ffo_3m=ResultadoMargem(Decimal("0.899")),
        ffo_trend=TendenciaFfo.ESTAVEL,
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
            tendencia=TendenciaDividendo.FORTE_ALTA,
        ),
        dividendos_12m_por_cota=Decimal("1.05"),
        metricas=metricas,
        margens=_margens_hgbs11(),
        cotas=Decimal("144355726"),
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

    def test_formatar_margem(self):
        assert formatar_margem(None) == NA
        assert formatar_margem(ResultadoMargem(None)) == NA
        assert formatar_margem(ResultadoMargem(Decimal("0.873"))) == "87,3%"
        assert (
            formatar_margem(ResultadoMargem(None, MotivoMargem.RECEITA_NEGATIVA))
            == "Receita negativa"
        )
        assert (
            formatar_margem(ResultadoMargem(None, MotivoMargem.FFO_NEGATIVO))
            == "FFO negativo"
        )
        assert (
            formatar_margem(
                ResultadoMargem(None, MotivoMargem.RECEITA_E_FFO_NEGATIVOS)
            )
            == "Receita e FFO negativos"
        )

    def test_formatar_ratio(self):
        assert formatar_ratio(Decimal("12.25")) == "12,25x"
        assert formatar_ratio(None) == NA

    def test_formatar_inteiro(self):
        assert formatar_inteiro(100000) == "100.000"
        assert formatar_inteiro(None) == NA

    def test_formatar_quantidade(self):
        assert formatar_quantidade(Decimal("144355726")) == "144.355.726"
        assert formatar_quantidade(Decimal("1000000.0000")) == "1.000.000"
        assert formatar_quantidade(None) == NA

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

    def test_coluna_p_l_alinhada_a_direita(self):
        from flowscope.presentation.gui.charts.fundamental_table import (
            _COLUNAS_DIREITA,
        )

        assert "p_l" in _COLUNAS_DIREITA


class TestRotuloTendencia:
    def test_rotulos_descritivos_do_ffo(self):
        assert rotulo_tendencia(TendenciaFfo.FORTE_ALTA) == "Forte Alta"
        assert rotulo_tendencia(TendenciaFfo.ALTA) == "Leve Alta"
        assert rotulo_tendencia(TendenciaFfo.ESTAVEL) == "Estável"
        assert rotulo_tendencia(TendenciaFfo.QUEDA) == "Leve Queda"
        assert rotulo_tendencia(TendenciaFfo.FORTE_QUEDA) == "Forte Queda"

    def test_rotulo_dividendo_usa_o_mesmo_mapa(self):
        assert rotulo_tendencia(TendenciaDividendo.FORTE_ALTA) == "Forte Alta"
        assert rotulo_tendencia(TendenciaDividendo.FORTE_QUEDA) == "Forte Queda"

    def test_rotulo_na(self):
        assert rotulo_tendencia(None) == NA
        assert rotulo_tendencia(TendenciaDividendo.N_A) == NA


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
        assert colunas[4] == NA
        assert colunas[5] == NA
        assert colunas[6] == NA
        assert colunas[7] == NA
        assert colunas[8] == "0,92x"
        assert colunas[9] == NA
        assert colunas[10] == "7,9%"
        assert colunas[11] == "10/07/2026"
        assert colunas[12] == "0,55"
        assert colunas[13] == "0,50"
        assert colunas[14] == "Forte Alta"
        assert colunas[15] == "87,3%"
        assert colunas[16] == "85,5%"
        assert colunas[17] == "Estável"
        assert colunas[18] == "115,7%"
        assert colunas[19] == "76,8%"
        assert colunas[20] == "132,6%"
        assert colunas[21] == "89,9%"
        assert colunas[22] == "144.355.726"

    def test_coluna_p_l_renderiza_apos_p_vp(self):
        analise = replace(_analise_hgbs11(), p_l=Decimal("2.84"))
        colunas = montar_linhas({"HGBS11": analise})[0]
        assert colunas[8] == "0,92x"
        assert colunas[9] == "2,84x"

    def test_colunas_preco_tipico_e_p_pt_apos_cotacao(self):
        analise = replace(
            _analise_hgbs11(),
            cotacao=Decimal("9"),
            preco_tipico=Decimal("10"),
            pct_preco_tipico=Decimal("-0.10"),
        )
        colunas = montar_linhas({"HGBS11": analise})[0]
        assert colunas[4] == "9,00"
        assert colunas[5] == "10,00"
        assert colunas[6] == "-10,00%"

    def test_linha_de_acao_fica_na_nas_colunas_ffo_e_dividendo(self):
        linhas = montar_linhas({"PETR4": _analise_acao()})
        colunas = linhas[0]
        assert colunas[2] == "Papel"
        assert colunas[3] == "Preferencial"
        assert all(coluna == NA for coluna in colunas[4:])

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


def _acao_com_indicadores() -> AnaliseFundamental:
    return replace(
        _analise_acao(),
        lpa=Decimal("1.23"),
        roe=Decimal("0.154"),
        roic=Decimal("0.12"),
        preco_tipico=Decimal("10"),
        pct_preco_tipico=Decimal("-0.10"),
    )


def _fii_de_tijolo() -> AnaliseFundamental:
    return replace(
        _analise_hgbs11(),
        qtd_imoveis=16,
        cap_rate=Decimal("0.065"),
        vacancia_media=Decimal("0.032"),
        preco_tipico=Decimal("10"),
        pct_preco_tipico=Decimal("-0.10"),
        indexadores={"IPCA": Decimal("0.22"), "INCC": Decimal("0.05")},
    )


class TestInformacoesAdicionais:
    def test_papel_com_indicadores(self):
        colunas = montar_linhas({"PETR4": _acao_com_indicadores()})[0]
        assert colunas[28] == "LPA 1,23 | ROE 15,40% | ROIC 12,00%"

    def test_fii_de_tijolo_com_imoveis_e_indexadores(self):
        colunas = montar_linhas({"HGBS11": _fii_de_tijolo()})[0]
        assert colunas[28] == (
            "Qtd Imóveis 16 | Cap Rate 6,50% | Vacância Média 3,20% | "
            "IPCA 22,00% | INCC 5,00%"
        )

    def test_fii_de_papel_omite_imoveis(self):
        analise = replace(
            _fii_de_tijolo(),
            qtd_imoveis=0,
            cap_rate=Decimal("0.065"),
            vacancia_media=Decimal("0.032"),
        )
        colunas = montar_linhas({"HGBS11": analise})[0]
        assert "Qtd Imóveis" not in colunas[28]
        assert "Cap Rate" not in colunas[28]
        assert "Vacância Média" not in colunas[28]
        assert colunas[28] == "IPCA 22,00% | INCC 5,00%"

    def test_fii_sem_fundamentus_omite_imoveis(self):
        analise = replace(
            _fii_de_tijolo(),
            qtd_imoveis=None,
            cap_rate=None,
            vacancia_media=None,
        )
        colunas = montar_linhas({"HGBS11": analise})[0]
        assert "Qtd Imóveis" not in colunas[28]
        assert "Cap Rate" not in colunas[28]
        assert "Vacância Média" not in colunas[28]

    def test_itens_ausentes_omitidos_sem_impedir_os_demais(self):
        analise = replace(
            _acao_com_indicadores(),
            roe=None,
            pct_preco_tipico=None,
        )
        colunas = montar_linhas({"PETR4": analise})[0]
        assert colunas[28] == "LPA 1,23 | ROIC 12,00%"

    def test_coluna_sem_itens_exibe_na(self):
        colunas = montar_linhas({"PETR4": _analise_acao()})[0]
        assert colunas[28] == NA


class TestDadosFiscais:
    def test_fii_exibe_cnpj_administrador_e_gestor_com_nomes(self):
        analise = replace(
            _fii_de_tijolo(),
            cnpj="12.345.678/0001-90",
            nome_administrador="BANCO GENIAL S.A.",
            cnpj_administrador="98.765.432/0001-10",
            nome_gestor="CY.CAPITAL GESTORA",
            cnpj_gestor="11.222.333/0001-44",
        )
        colunas = montar_linhas({"HGBS11": analise})[0]
        assert colunas[29] == (
            "CNPJ 12.345.678/0001-90 | "
            "Administrador BANCO GENIAL S.A. (98.765.432/0001-10) | "
            "Gestor CY.CAPITAL GESTORA (11.222.333/0001-44)"
        )

    def test_fii_sem_nomes_exibe_apenas_cnpjs(self):
        analise = replace(
            _fii_de_tijolo(),
            cnpj="12.345.678/0001-90",
            cnpj_administrador="98.765.432/0001-10",
            cnpj_gestor="11.222.333/0001-44",
        )
        colunas = montar_linhas({"HGBS11": analise})[0]
        assert colunas[29] == (
            "CNPJ 12.345.678/0001-90 | Administrador (98.765.432/0001-10) | "
            "Gestor (11.222.333/0001-44)"
        )

    def test_cnpj_sem_pontuacao_e_formatado(self):
        analise = replace(
            _fii_de_tijolo(),
            cnpj="12345678000190",
            cnpj_gestor="11222333000144",
        )
        colunas = montar_linhas({"HGBS11": analise})[0]
        assert colunas[29] == (
            "CNPJ 12.345.678/0001-90 | Gestor (11.222.333/0001-44)"
        )

    def test_papel_exibe_apenas_cnpj(self):
        analise = replace(
            _analise_acao(),
            cnpj="33.000.167/0001-01",
            cnpj_administrador="98.765.432/0001-10",
            cnpj_gestor="11.222.333/0001-44",
        )
        colunas = montar_linhas({"PETR4": analise})[0]
        assert colunas[29] == "CNPJ 33.000.167/0001-01"

    def test_item_ausente_omitido(self):
        analise = replace(
            _fii_de_tijolo(),
            cnpj="12.345.678/0001-90",
            cnpj_administrador=None,
            cnpj_gestor="11.222.333/0001-44",
        )
        colunas = montar_linhas({"HGBS11": analise})[0]
        assert colunas[29] == (
            "CNPJ 12.345.678/0001-90 | Gestor (11.222.333/0001-44)"
        )

    def test_coluna_sem_itens_exibe_na(self):
        colunas = montar_linhas({"PETR4": _analise_acao()})[0]
        assert colunas[29] == NA


class TestMontarCsv:
    def test_cabecalho_corresponde_as_colunas_da_tabela(self):
        csv = montar_csv({"HGBS11": _analise_hgbs11()})
        assert csv.split("\n")[0] == (
            "Ticker;Nome;Tipo;Sub-tipo;P (Cotação);Preço Típico;P / PT;"
            "VP (VP/Cota);P/VP;P/L;"
            "Dividend Yield;Última data-com;Último dividendo;Dividendo anterior;"
            "Tendência do dividendo;FFO/Receita (12m);FFO/Receita (3m);FFO Trend;"
            "Dividendos/Receita (12m);Dividendos/Receita (3m);"
            "Dividendos/FFO (12m);Dividendos/FFO (3m);Nº de cotas;Nº de cotistas;"
            "Classe de cotistas;Patrimônio;Classe de patrimônio;Data de referência;"
            "Informações adicionais;Dados fiscais"
        )

    def test_linhas_preservam_ordem_e_valores_formatados(self):
        csv = montar_csv(
            {"HGBS11": _analise_hgbs11(), "PETR4": _analise_acao()}
        )
        linhas = csv.split("\n")
        assert linhas[1].startswith(
            "HGBS11;CSHG Renda Urbana;FII;Tijolo;N/A;N/A;N/A;N/A;0,92x;N/A;"
            "7,9%;10/07/2026;0,55;0,50;Forte Alta;87,3%"
        )
        assert linhas[2].startswith("PETR4;Petrobras PN;Papel;Preferencial;")

    def test_csv_usa_duas_casas_decimais(self):
        csv = montar_csv({"HGBS11": _analise_hgbs11()})
        campos = csv.split("\n")[1].split(";")
        assert campos[12] == "0,55"
        assert campos[13] == "0,50"
        assert campos[16] == "85,5%"
        assert campos[22] == "144.355.726"

    def test_csv_inclui_colunas_novas_com_os_mesmos_textos(self):
        analise = replace(
            _fii_de_tijolo(),
            cnpj="12.345.678/0001-90",
            cnpj_administrador="98.765.432/0001-10",
            cnpj_gestor="11.222.333/0001-44",
        )
        linha = montar_linhas({"HGBS11": analise})[0]
        campos = montar_csv({"HGBS11": analise}).split("\n")[1].split(";")
        assert campos[28] == linha[28]
        assert campos[29] == linha[29]
        assert campos[29] == (
            "CNPJ 12.345.678/0001-90 | Administrador (98.765.432/0001-10) | "
            "Gestor (11.222.333/0001-44)"
        )

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
    def test_painel_expoe_dois_treeviews(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            assert tuple(painel._tree_fixo.cget("columns")) == ("ticker", "nome")
            assert len(painel._tree_rolavel.cget("columns")) == 28
        finally:
            root.destroy()

    @needs_display
    def test_update_popula_os_dois_treeviews(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.update({"HGBS11": _analise_hgbs11(), "PETR4": _analise_acao()})
            fixos = painel._tree_fixo.get_children()
            rolantes = painel._tree_rolavel.get_children()
            assert fixos == rolantes == ("HGBS11", "PETR4")
            valores = painel._tree_fixo.item(fixos[0], "values")
            assert valores[0] == "HGBS11"
            assert valores[1] == "CSHG Renda Urbana"
            rolavel = painel._tree_rolavel.item(fixos[0], "values")
            assert rolavel[13] == "87,3%"
        finally:
            root.destroy()

    @needs_display
    def test_linha_dividida_reconstroi_30_campos(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.update({"HGBS11": _analise_hgbs11()})
            iid = painel._tree_fixo.get_children()[0]
            congelados = tuple(painel._tree_fixo.item(iid, "values"))
            rolantes = tuple(painel._tree_rolavel.item(iid, "values"))
            assert len(congelados) == 2
            assert len(rolantes) == 28
            assert len(congelados + rolantes) == 30
        finally:
            root.destroy()

    @needs_display
    def test_update_vazio_limpa_os_dois_treeviews(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.update({"HGBS11": _analise_hgbs11()})
            painel.reset()
            assert len(painel._tree_fixo.get_children()) == 0
            assert len(painel._tree_rolavel.get_children()) == 0
        finally:
            root.destroy()

    @needs_display
    def test_layout_em_grid_com_barra_compartilhada(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            assert painel._frame_fixo.grid_info()["column"] == 0
            assert painel._divisor.grid_info()["column"] == 1
            assert painel._frame_rolavel.grid_info()["column"] == 2
            assert painel._scrollbar_v.grid_info()["column"] == 3
            assert painel._scrollbar_v.grid_info()["in"] == painel.frame
            assert painel._scrollbar_h.grid_info()["in"] == painel._frame_rolavel
            assert painel.frame.grid_columnconfigure(0)["weight"] == 0
            assert painel.frame.grid_columnconfigure(1)["weight"] == 0
            assert painel.frame.grid_columnconfigure(2)["weight"] == 1
            assert painel._espacador.grid_info()["in"] == painel._frame_fixo
            assert painel._espacador.grid_info()["row"] == 1
        finally:
            root.destroy()

    @needs_display
    def test_divisor_fixo_entre_os_paineis(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            assert isinstance(painel._divisor, ttk.Separator)
            assert str(painel._divisor.cget("orient")) == "vertical"
            assert painel._divisor.grid_info()["column"] == 1
            assert painel._divisor.grid_info()["in"] == painel.frame
        finally:
            root.destroy()

    @needs_display
    def test_get_column_widths_agrega_os_dois_treeviews(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            larguras = painel.get_column_widths()
            assert set(larguras) == set(painel._columns)
            assert len(larguras) == 30
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
    def test_larguras_persistidas_vai_para_treeview_correto(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(
                root, widths={"ticker": 200, "nome": 180, "p": 90}
            )
            assert int(painel._tree_fixo.column("ticker", "width")) == 200
            assert int(painel._tree_fixo.column("nome", "width")) == 180
            assert int(painel._tree_rolavel.column("p", "width")) == 90
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
            painel._tree_fixo.column("ticker", width=222)
            painel._on_column_resized()
            assert registradas and registradas[-1]["ticker"] == 222
            assert registradas[-1]["p"] == 140
        finally:
            root.destroy()

    @needs_display
    def test_fronteira_ajusta_ao_redimensionar_coluna_congelada(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.frame.pack(fill="both", expand=True)
            root.geometry("900x300")
            root.update()
            painel._tree_fixo.column("ticker", width=200)
            painel._tree_fixo.column("nome", width=210)
            painel._on_column_resized()
            root.update()
            assert painel._frame_fixo.winfo_width() == 410
        finally:
            root.destroy()

    @needs_display
    def test_painel_rolavel_mantem_largura_minima(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.frame.pack(fill="both", expand=True)
            root.geometry("400x300")
            root.update()
            painel._tree_fixo.column("ticker", width=600)
            painel._tree_fixo.column("nome", width=600)
            painel._on_column_resized()
            root.update()
            disponivel = painel.frame.winfo_width()
            assert painel._frame_fixo.winfo_width() <= disponivel - 200
        finally:
            root.destroy()

    @needs_display
    def test_rolagem_vertical_sincroniza_os_paineis(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.frame.pack(fill="both", expand=True)
            root.geometry("900x200")
            root.update()
            painel.update(
                {f"AAA{i:02d}": {"daily_data": []} for i in range(60)}
            )
            root.update()
            painel._tree_rolavel.yview_moveto(0.5)
            root.update()
            assert painel._tree_fixo.yview()[0] == pytest.approx(
                painel._tree_rolavel.yview()[0]
            )
        finally:
            root.destroy()

    @needs_display
    def test_barra_vertical_move_os_dois_paineis(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.frame.pack(fill="both", expand=True)
            root.geometry("900x200")
            root.update()
            painel.update(
                {f"AAA{i:02d}": {"daily_data": []} for i in range(60)}
            )
            root.update()
            painel._on_vscroll("moveto", "0.4")
            root.update()
            assert painel._tree_fixo.yview()[0] == pytest.approx(0.4, abs=0.01)
            assert painel._tree_fixo.yview()[0] == pytest.approx(
                painel._tree_rolavel.yview()[0]
            )
        finally:
            root.destroy()

    @needs_display
    def test_roda_do_mouse_encaminha_rolagem(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.frame.pack(fill="both", expand=True)
            root.geometry("900x200")
            root.update()
            painel.update(
                {f"AAA{i:02d}": {"daily_data": []} for i in range(60)}
            )
            root.update()

            class _Evento:
                num = 5
                delta = 0

            inicio = painel._tree_rolavel.yview()[0]
            assert painel._on_mousewheel(_Evento()) == "break"
            root.update()
            assert painel._tree_rolavel.yview()[0] > inicio
            assert painel._tree_fixo.yview()[0] == pytest.approx(
                painel._tree_rolavel.yview()[0]
            )
        finally:
            root.destroy()

    @needs_display
    def test_selecao_espelhada_entre_os_paineis(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.update(
                {f"AAA{i:02d}": {"daily_data": []} for i in range(5)}
            )
            painel._tree_fixo.selection_set("AAA02")
            root.update()
            assert painel._tree_rolavel.selection() == ("AAA02",)
            painel._tree_rolavel.selection_set("AAA04")
            root.update()
            assert painel._tree_fixo.selection() == ("AAA04",)
        finally:
            root.destroy()

    @needs_display
    def test_selecao_e_unica(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            assert str(painel._tree_fixo.cget("selectmode")) == "browse"
            assert str(painel._tree_rolavel.cget("selectmode")) == "browse"
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
                "dividend_yield",
                "ffo_receita_12m",
                "ffo_receita_3m",
                "dividendos_receita_12m",
                "dividendos_receita_3m",
                "dividendos_ffo_12m",
                "dividendos_ffo_3m",
                "p",
                "preco_tipico",
                "p_pt",
                "vp",
                "p_vp",
                "p_l",
                "cotas",
                "cotistas",
                "patrimonio",
            }
            for coluna_id in painel._columns:
                tree = (
                    painel._tree_fixo
                    if coluna_id in painel._columns_fixas
                    else painel._tree_rolavel
                )
                esperado = "e" if coluna_id in direita else "w"
                assert str(tree.column(coluna_id, "anchor")) == esperado
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
        assert all(coluna == NA for coluna in petr[4:])

        hcri = por_ticker["HCRI11"]
        assert hcri[2] == "FII"
        assert hcri[3] == "Papel"
        assert hcri[12] == "1,00"
        assert all(coluna == NA for coluna in hcri[15:])

        hgbs = por_ticker["HGBS11"]
        assert hgbs[2] == "FII"
        assert hgbs[3] == "Tijolo"
        assert hgbs[8] == "0,92x"
        assert hgbs[10] == "35,2%"
        assert hgbs[11] == "10/07/2026"
        assert hgbs[12] == "0,55"
        assert hgbs[13] == "0,50"
        assert hgbs[14] == "Forte Alta"
        assert all(coluna == NA for coluna in hgbs[15:22])
        assert hgbs[22] == "144.355.726"
        assert hgbs[23] == "100.000"
        assert hgbs[24] == "Muito grande"
        assert hgbs[25] == "R$ 2,94 bi"
        assert hgbs[26] == "Gigante"


class TestWiringSubAba:
    def test_tab_content_fundamentos_existe(self):
        assert ("Análise Geral", "Fundamentos") in TAB_CONTENT
        titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        assert "Fundamentos" in titulo
        assert isinstance(corpo, list) and len(corpo) > 0

    def test_orientation_panel_explica_p_l_e_acionistas(self):
        _titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        texto = " ".join(parte for parte, _estilo in corpo)
        assert "último dividendo" in texto
        assert "acionistas" in texto

    def test_orientation_panel_descreve_colunas_recentes(self):
        _titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        texto = " ".join(parte for parte, _estilo in corpo)
        assert "Preço Típico" in texto
        assert "P / PT" in texto
        assert "Dividendos/FFO" in texto
        assert "Informações adicionais" in texto
        assert "Dados fiscais" in texto

    def test_orientation_panel_orienta_quantidade_de_cotas(self):
        _titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        texto = " ".join(parte for parte, _estilo in corpo)
        assert "cotas emitidas" in texto
        assert "Nro. Ações" in texto

    def test_orientation_panel_descreve_tipo_e_subtipo_implementados(self):
        _titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        texto = " ".join(parte for parte, _estilo in corpo)
        assert "tipo (`Papel` para ações, ETFs e BDRs; `FII`)" in texto
        assert "Tijolo:" in texto
        assert "Papel:" in texto
        assert "segmento e gestão" in texto

    def test_orientation_panel_orienta_interpretacao_das_colunas(self):
        _titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        texto = " ".join(parte for parte, _estilo in corpo)
        assert "desconto" in texto
        assert "prêmio" in texto
        assert "FFO/Receita" in texto
        assert "administrador" in texto
        assert "gestor" in texto

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
