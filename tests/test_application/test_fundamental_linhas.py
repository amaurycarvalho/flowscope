"""Testes puros de formatação, montagem de linhas e CSV da tabela."""

from dataclasses import replace
from datetime import date
from decimal import Decimal

from flowscope.application.fundamental.formatters import (
    formatar_data,
    formatar_dias,
    formatar_inteiro,
    formatar_margem,
    formatar_patrimonio,
    formatar_percentual,
    formatar_quantidade,
    formatar_ratio,
    formatar_valor,
    rotulo_classificacao_short,
    rotulo_classe_cotistas,
    rotulo_classe_patrimonio,
    rotulo_tendencia,
)
from flowscope.application.fundamental.linhas import (
    montar_csv,
    montar_linhas,
)
from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.domain.fii import (
    AnaliseFundamental,
    ClasseCotistas,
    ClassePatrimonio,
    ClasseRiscoFechamento,
    ClasseShorts,
    FfoObservacao,
    FiiSnapshot,
    MargensFii,
    MetricasShort,
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
            shares_outstanding=Decimal(144355726),
            net_asset_value=Decimal(2942000000),
            ffo_12m=Decimal(220777000),
            ffo_3m=Decimal(63802000),
            dividends_12m=Decimal(213080000),
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
        cotas=Decimal(144355726),
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


def _analise_com_short() -> AnaliseFundamental:
    return replace(
        _analise_hgbs11(),
        short=MetricasShort(
            shorts_pct=Decimal("0.1"),
            volume_shorts=ClasseShorts.BAIXO,
            sir=Decimal("5"),
            risco_fechamento=ClasseRiscoFechamento.ALTO,
        ),
    )


class TestFormatadores:
    def test_formatar_valor_na(self):
        assert formatar_valor(None) == NA

    def test_formatar_valor_com_virgula(self):
        assert formatar_valor(Decimal("0.55")) == "0,55"
        assert formatar_valor(Decimal("0.08355")) == "0,08"
        assert formatar_valor(Decimal("0.7")) == "0,70"
        assert formatar_valor(Decimal("15.5")) == "15,50"
        assert formatar_valor(Decimal(9)) == "9,00"

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

    def test_formatar_dias(self):
        assert formatar_dias(Decimal("5")) == "5,0d"
        assert formatar_dias(Decimal("13.27")) == "13,3d"
        assert formatar_dias(None) == NA

    def test_formatar_inteiro(self):
        assert formatar_inteiro(100000) == "100.000"
        assert formatar_inteiro(None) == NA

    def test_formatar_quantidade(self):
        assert formatar_quantidade(Decimal(144355726)) == "144.355.726"
        assert formatar_quantidade(Decimal("1000000.0000")) == "1.000.000"
        assert formatar_quantidade(None) == NA

    def test_formatar_patrimonio(self):
        assert formatar_patrimonio(Decimal(2942000000)) == "R$ 2,94 bi"
        assert formatar_patrimonio(Decimal(150000000)) == "R$ 150,00 mi"
        assert formatar_patrimonio(Decimal(250000)) == "R$ 250.000,00"
        assert formatar_patrimonio(None) == NA

    def test_rotulos_de_classe(self):
        assert rotulo_classe_cotistas(ClasseCotistas.MEDIO) == "Médio"
        assert rotulo_classe_patrimonio(ClassePatrimonio.GIGANTE) == "Gigante"
        assert rotulo_classe_cotistas(None) == NA
        assert rotulo_classe_patrimonio(None) == NA

    def test_coluna_p_l_alinhada_a_direita(self):
        from flowscope.application.fundamental.linhas import (
            _COLUNAS_DIREITA,
        )

        assert "p_l" in _COLUNAS_DIREITA
        assert "shorts_pct" in _COLUNAS_DIREITA
        assert "sir" in _COLUNAS_DIREITA

    def test_rotulo_classificacao_short(self):
        assert rotulo_classificacao_short(ClasseShorts.INEXISTENTE) == "Inexistente"
        assert rotulo_classificacao_short(ClasseShorts.MUITO_BAIXO) == "Muito Baixo"
        assert rotulo_classificacao_short(ClasseShorts.BAIXO) == "Baixo"
        assert rotulo_classificacao_short(ClasseShorts.ALTO) == "Alto"
        assert rotulo_classificacao_short(ClasseShorts.MUITO_ALTO) == "Muito Alto"
        assert rotulo_classificacao_short(None) == "Inexistente"
        assert rotulo_classificacao_short(ClasseRiscoFechamento.ALTO) == "Alto"


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
        assert colunas[15] == NA
        assert colunas[16] == "Inexistente"
        assert colunas[17] == NA
        assert colunas[18] == "Inexistente"
        assert colunas[19] == "87,3%"
        assert colunas[20] == "85,5%"
        assert colunas[21] == "Estável"
        assert colunas[22] == "115,7%"
        assert colunas[23] == "76,8%"
        assert colunas[24] == "132,6%"
        assert colunas[25] == "89,9%"
        assert colunas[26] == "144.355.726"

    def test_colunas_short_interest_preenchidas(self):
        colunas = montar_linhas({"HGBS11": _analise_com_short()})[0]
        assert colunas[15] == "10,0%"
        assert colunas[16] == "Baixo"
        assert colunas[17] == "5,0d"
        assert colunas[18] == "Alto"

    def test_colunas_short_interest_vazias_classificam_inexistente(self):
        colunas = montar_linhas({"HGBS11": _analise_hgbs11()})[0]
        assert colunas[15:19] == (NA, "Inexistente", NA, "Inexistente")

    def test_colunas_short_posicionadas_apos_tendencia_do_dividendo(self):
        from flowscope.application.fundamental.linhas import _COLUNAS

        ids = [coluna_id for coluna_id, _ in _COLUNAS]
        assert ids.index("shorts_pct") == ids.index("tendencia_dividendo") + 1
        assert ids.index("risco_fechamento") == ids.index("ffo_receita_12m") - 1

    def test_colunas_short_sao_rolantes_com_largura_padrao(self):
        from flowscope.application.fundamental.linhas import (
            _COLUNAS_DIREITA,
            _COLUNAS_ROLANTES,
            _largura_coluna,
        )

        ids = [coluna_id for coluna_id, _ in _COLUNAS_ROLANTES]
        for coluna in ("shorts_pct", "volume_shorts", "sir", "risco_fechamento"):
            assert coluna in ids
            assert _largura_coluna(None, coluna) == 140
        assert "volume_shorts" not in _COLUNAS_DIREITA
        assert "risco_fechamento" not in _COLUNAS_DIREITA

    def test_coluna_p_l_renderiza_apos_p_vp(self):
        analise = replace(_analise_hgbs11(), p_l=Decimal("2.84"))
        colunas = montar_linhas({"HGBS11": analise})[0]
        assert colunas[8] == "0,92x"
        assert colunas[9] == "2,84x"

    def test_colunas_preco_tipico_e_p_pt_apos_cotacao(self):
        analise = replace(
            _analise_hgbs11(),
            cotacao=Decimal(9),
            preco_tipico=Decimal(10),
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
        assert all(coluna == NA for coluna in colunas[4:16])
        assert colunas[16] == "Inexistente"
        assert colunas[17] == NA
        assert colunas[18] == "Inexistente"
        assert all(coluna == NA for coluna in colunas[19:])

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
        preco_tipico=Decimal(10),
        pct_preco_tipico=Decimal("-0.10"),
    )


def _fii_de_tijolo() -> AnaliseFundamental:
    return replace(
        _analise_hgbs11(),
        qtd_imoveis=16,
        cap_rate=Decimal("0.065"),
        vacancia_media=Decimal("0.032"),
        preco_tipico=Decimal(10),
        pct_preco_tipico=Decimal("-0.10"),
        indexadores={"IPCA": Decimal("0.22"), "INCC": Decimal("0.05")},
    )


def _analise_bdr() -> AnaliseFundamental:
    return AnaliseFundamental(
        ticker="EXXO34",
        nome="Exxon Mobil",
        classificacao=classificar_ticker("EXXO34"),
        ultimo_dividendo=UltimoDividendo(
            data_com=date(2026, 8, 10),
            valor=Decimal("0.50"),
            valor_anterior=None,
            tendencia=TendenciaDividendo.N_A,
        ),
        dividendos_12m_por_cota=None,
        metricas=None,
        cotacao=Decimal("10.00"),
        p_l=Decimal("5.00"),
        bdr_nivel="Nível I Não Patrocinado",
        bdr_observacao=(
            "O valor informado já está deduzido de IR, IOF e tarifa"
        ),
        nome_depositario="Banco B3 S.A.",
        nome_empresa_bdr="Exxon Mobil Corporation",
        isin="BREXXOBDR006",
    )


class TestInformacoesAdicionais:
    def test_papel_com_indicadores(self):
        colunas = montar_linhas({"PETR4": _acao_com_indicadores()})[0]
        assert colunas[32] == "LPA 1,23 | ROE 15,40% | ROIC 12,00%"

    def test_fii_de_tijolo_com_imoveis_e_indexadores(self):
        colunas = montar_linhas({"HGBS11": _fii_de_tijolo()})[0]
        assert colunas[32] == (
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
        assert "Qtd Imóveis" not in colunas[32]
        assert "Cap Rate" not in colunas[32]
        assert "Vacância Média" not in colunas[32]
        assert colunas[32] == "IPCA 22,00% | INCC 5,00%"

    def test_fii_sem_fundamentus_omite_imoveis(self):
        analise = replace(
            _fii_de_tijolo(),
            qtd_imoveis=None,
            cap_rate=None,
            vacancia_media=None,
        )
        colunas = montar_linhas({"HGBS11": analise})[0]
        assert "Qtd Imóveis" not in colunas[32]
        assert "Cap Rate" not in colunas[32]
        assert "Vacância Média" not in colunas[32]

    def test_itens_ausentes_omitidos_sem_impedir_os_demais(self):
        analise = replace(
            _acao_com_indicadores(),
            roe=None,
            pct_preco_tipico=None,
        )
        colunas = montar_linhas({"PETR4": analise})[0]
        assert colunas[32] == "LPA 1,23 | ROIC 12,00%"

    def test_coluna_sem_itens_exibe_na(self):
        colunas = montar_linhas({"PETR4": _analise_acao()})[0]
        assert colunas[32] == NA

    def test_bdr_exibe_nivel_e_observacao_fiscal(self):
        colunas = montar_linhas({"EXXO34": _analise_bdr()})[0]
        assert colunas[32] == (
            "Nível I Não Patrocinado | Obs.: O valor informado já está "
            "deduzido de IR, IOF e tarifa"
        )

    def test_bdr_sem_nivel_e_observacao_exibe_na(self):
        analise = replace(_analise_bdr(), bdr_nivel=None, bdr_observacao=None)
        colunas = montar_linhas({"EXXO34": analise})[0]
        assert colunas[32] == NA

    def test_bdr_exibe_tipo_papel_e_sub_tipo_bdr(self):
        colunas = montar_linhas({"EXXO34": _analise_bdr()})[0]
        assert colunas[2] == "Papel"
        assert colunas[3] == "BDR"


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
        assert colunas[33] == (
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
        assert colunas[33] == (
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
        assert colunas[33] == (
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
        assert colunas[33] == "CNPJ 33.000.167/0001-01"

    def test_item_ausente_omitido(self):
        analise = replace(
            _fii_de_tijolo(),
            cnpj="12.345.678/0001-90",
            cnpj_administrador=None,
            cnpj_gestor="11.222.333/0001-44",
        )
        colunas = montar_linhas({"HGBS11": analise})[0]
        assert colunas[33] == (
            "CNPJ 12.345.678/0001-90 | Gestor (11.222.333/0001-44)"
        )

    def test_coluna_sem_itens_exibe_na(self):
        colunas = montar_linhas({"PETR4": _analise_acao()})[0]
        assert colunas[33] == NA

    def test_bdr_exibe_depositario_empresa_e_isin(self):
        colunas = montar_linhas({"EXXO34": _analise_bdr()})[0]
        assert colunas[33] == (
            "Depositário Banco B3 S.A. | Empresa Exxon Mobil Corporation | "
            "ISIN BREXXOBDR006"
        )

    def test_bdr_item_indisponivel_omitido(self):
        analise = replace(_analise_bdr(), isin=None)
        colunas = montar_linhas({"EXXO34": analise})[0]
        assert colunas[33] == (
            "Depositário Banco B3 S.A. | Empresa Exxon Mobil Corporation"
        )

    def test_bdr_com_cnpj_nao_usa_identidade_dos_avisos(self):
        analise = replace(_analise_bdr(), cnpj="12.345.678/0001-90")
        colunas = montar_linhas({"EXXO34": analise})[0]
        assert colunas[33] == "CNPJ 12.345.678/0001-90"


class TestMontarCsv:
    def test_cabecalho_corresponde_as_colunas_da_tabela(self):
        csv = montar_csv({"HGBS11": _analise_hgbs11()})
        assert csv.split("\n")[0] == (
            "Ticker;Nome;Tipo;Sub-tipo;P (Cotação);Preço Típico;P / PT;"
            "VP (VP/Cota);P/VP;P/L;"
            "Dividend Yield;Última data-com;Último dividendo;Dividendo anterior;"
            "Tendência do dividendo;Shorts%;Volume de Shorts;Fechamento Shorts;"
            "Risco Fechamento;FFO/Receita (12m);FFO/Receita (3m);FFO Trend;"
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
            "7,9%;10/07/2026;0,55;0,50;Forte Alta;N/A;Inexistente;N/A;"
            "Inexistente;87,3%"
        )
        assert linhas[2].startswith("PETR4;Petrobras PN;Papel;Preferencial;")

    def test_csv_usa_duas_casas_decimais(self):
        csv = montar_csv({"HGBS11": _analise_hgbs11()})
        campos = csv.split("\n")[1].split(";")
        assert campos[12] == "0,55"
        assert campos[13] == "0,50"
        assert campos[20] == "85,5%"
        assert campos[26] == "144.355.726"

    def test_csv_inclui_colunas_novas_com_os_mesmos_textos(self):
        analise = replace(
            _fii_de_tijolo(),
            cnpj="12.345.678/0001-90",
            cnpj_administrador="98.765.432/0001-10",
            cnpj_gestor="11.222.333/0001-44",
        )
        linha = montar_linhas({"HGBS11": analise})[0]
        campos = montar_csv({"HGBS11": analise}).split("\n")[1].split(";")
        assert campos[32] == linha[32]
        assert campos[33] == linha[33]
        assert campos[33] == (
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
                net_asset_value=Decimal(2942000000),
                shares_outstanding=Decimal(144355726),
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
                ffo_12m=Decimal(220777000),
                ffo_3m=Decimal(63802000),
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
        assert all(coluna == NA for coluna in petr[4:16])
        assert petr[16] == "Inexistente"
        assert petr[17] == NA
        assert petr[18] == "Inexistente"
        assert all(coluna == NA for coluna in petr[19:])

        hcri = por_ticker["HCRI11"]
        assert hcri[2] == "FII"
        assert hcri[3] == "Papel"
        assert hcri[12] == "1,00"
        assert hcri[15] == NA
        assert hcri[16] == "Inexistente"
        assert hcri[17] == NA
        assert hcri[18] == "Inexistente"
        assert all(coluna == NA for coluna in hcri[19:])

        hgbs = por_ticker["HGBS11"]
        assert hgbs[2] == "FII"
        assert hgbs[3] == "Tijolo"
        assert hgbs[8] == "0,92x"
        assert hgbs[10] == "35,2%"
        assert hgbs[11] == "10/07/2026"
        assert hgbs[12] == "0,55"
        assert hgbs[13] == "0,50"
        assert hgbs[14] == "Forte Alta"
        assert hgbs[15] == NA
        assert hgbs[16] == "Inexistente"
        assert hgbs[17] == NA
        assert hgbs[18] == "Inexistente"
        assert all(coluna == NA for coluna in hgbs[19:26])
        assert hgbs[26] == "144.355.726"
        assert hgbs[27] == "100.000"
        assert hgbs[28] == "Muito grande"
        assert hgbs[29] == "R$ 2,94 bi"
        assert hgbs[30] == "Gigante"
