from flowscope.domain.fii import (
    TAXONOMIA_FII_PADRAO,
    SubTipoAcao,
    SubTipoFii,
    TaxonomiaFii,
    TipoAtivo,
    classe_fii_elegivel_ffo,
    classificar_exibicao,
    classificar_ticker,
    elegivel_ffo,
    normalizar_ticker,
)


def _resolver_codigo_cvm(ticker: str) -> str | None:
    codigos = {
        "PETR3": "9512",
        "PETR4": "9512",
        "VALE3": "4170",
        "SANB11": "20455",
    }
    return codigos.get(ticker)


class TestEnums:
    def test_tipo_ativo_membros_esperados(self):
        assert set(TipoAtivo) == {
            TipoAtivo.ACAO,
            TipoAtivo.FII,
            TipoAtivo.ETF,
            TipoAtivo.BDR,
            TipoAtivo.DESCONHECIDO,
        }

    def test_sub_tipo_acao_membros_esperados(self):
        assert set(SubTipoAcao) == {
            SubTipoAcao.ORDINARIA,
            SubTipoAcao.PREFERENCIAL,
            SubTipoAcao.ETF,
        }

    def test_sub_tipo_fii_membros_esperados(self):
        assert set(SubTipoFii) == {
            SubTipoFii.TIJOLO,
            SubTipoFii.PAPEL,
            SubTipoFii.HIBRIDO,
            SubTipoFii.FIAGRO,
            SubTipoFii.FIINFRA,
            SubTipoFii.DESCONHECIDO,
        }


class TestTaxonomiaFii:
    def test_versao_explicita(self):
        assert isinstance(TAXONOMIA_FII_PADRAO.versao, str)
        assert TAXONOMIA_FII_PADRAO.versao

    def test_ticker_mapeado_retorna_sub_tipo(self):
        assert TAXONOMIA_FII_PADRAO.sub_tipo("KNRI11") is SubTipoFii.TIJOLO

    def test_ticker_normalizado_independente_de_caixa(self):
        assert TAXONOMIA_FII_PADRAO.sub_tipo("knri11") is SubTipoFii.TIJOLO

    def test_ticker_nao_mapeado_retorna_desconhecido(self):
        assert TAXONOMIA_FII_PADRAO.sub_tipo("ZZZZ11") is SubTipoFii.DESCONHECIDO

    def test_contem_apenas_entradas_explicitas(self):
        assert TAXONOMIA_FII_PADRAO.contem("HGBS11")
        assert not TAXONOMIA_FII_PADRAO.contem("ZZZZ11")


class TestClassificarTicker:
    def test_acao_ordinaria(self):
        classificacao = classificar_ticker(
            "PETR3", resolver_code_cvm=_resolver_codigo_cvm
        )
        assert classificacao.tipo is TipoAtivo.ACAO
        assert classificacao.sub_tipo is SubTipoAcao.ORDINARIA

    def test_acao_preferencial(self):
        classificacao = classificar_ticker(
            "PETR4", resolver_code_cvm=_resolver_codigo_cvm
        )
        assert classificacao.tipo is TipoAtivo.ACAO
        assert classificacao.sub_tipo is SubTipoAcao.PREFERENCIAL

    def test_acao_ordinaria_offline(self):
        classificacao = classificar_ticker("VALE3")
        assert classificacao.tipo is TipoAtivo.ACAO
        assert classificacao.sub_tipo is SubTipoAcao.ORDINARIA

    def test_fii_classificado_pela_taxonomia(self):
        classificacao = classificar_ticker("KNRI11")
        assert classificacao.tipo is TipoAtivo.FII
        assert classificacao.sub_tipo is SubTipoFii.TIJOLO

    def test_etf_reconhecido(self):
        classificacao = classificar_ticker("BOVA11")
        assert classificacao.tipo is TipoAtivo.ETF
        assert classificacao.sub_tipo is SubTipoAcao.ETF

    def test_bdr_reconhecido_pelo_sufixo(self):
        classificacao = classificar_ticker("AAPL34")
        assert classificacao.tipo is TipoAtivo.BDR
        assert classificacao.sub_tipo is None

    def test_unidade_de_acao_resolvida_por_code_cvm(self):
        classificacao = classificar_ticker(
            "SANB11", resolver_code_cvm=_resolver_codigo_cvm
        )
        assert classificacao.tipo is TipoAtivo.ACAO

    def test_sem_resolucao_e_sem_taxonomia_retorna_desconhecido(self):
        classificacao = classificar_ticker(
            "ZZZZ11", taxonomia_fii=TaxonomiaFii(versao="teste", tickers={})
        )
        assert classificacao.tipo is TipoAtivo.DESCONHECIDO
        assert classificacao.sub_tipo is None

    def test_acao_sem_code_cvm_nao_classificada(self):
        classificacao = classificar_ticker(
            "PETR3",
            resolver_code_cvm=lambda _ticker: None,
            taxonomia_fii=TaxonomiaFii(versao="teste", tickers={}),
        )
        assert classificacao.tipo is TipoAtivo.DESCONHECIDO

    def test_ticker_invalido_retorna_desconhecido(self):
        assert (
            classificar_ticker("FOO").tipo is TipoAtivo.DESCONHECIDO
        )
        assert (
            classificar_ticker("12345").tipo is TipoAtivo.DESCONHECIDO
        )

    def test_fonte_registrada(self):
        from flowscope.domain.fii import FonteClassificacao

        assert (
            classificar_ticker("PETR3", resolver_code_cvm=_resolver_codigo_cvm).fonte
            is FonteClassificacao.CODE_CVM
        )
        assert (
            classificar_ticker("KNRI11").fonte is FonteClassificacao.TAXONOMIA_FII
        )

    def test_ticker_normalizado(self):
        assert normalizar_ticker(" knri11 ") == "KNRI11"

    def test_fiagro_reconhecido_por_resolver(self):
        classificacao = classificar_ticker(
            "BBGO11", resolver_fiagro=lambda ticker: ticker == "BBGO11"
        )
        assert classificacao.tipo is TipoAtivo.FII
        assert classificacao.sub_tipo is SubTipoFii.FIAGRO

    def test_fiagro_nao_elegivel_ao_ffo(self):
        classificacao = classificar_ticker(
            "BBGO11", resolver_fiagro=lambda _ticker: True
        )
        assert elegivel_ffo(classificacao) is False

    def test_ticker_11_nao_reconhecido_permanece_desconhecido(self):
        classificacao = classificar_ticker(
            "ZZZZ11",
            taxonomia_fii=TaxonomiaFii(versao="teste", tickers={}),
            resolver_fiagro=lambda _ticker: False,
        )
        assert classificacao.tipo is TipoAtivo.DESCONHECIDO
        assert classificacao.sub_tipo is None


class TestElegibilidade:
    def test_fii_de_tijolo_elegivel(self):
        classificacao = classificar_ticker("KNRI11")
        assert elegivel_ffo(classificacao) is True

    def test_fii_de_papel_nao_elegivel(self):
        classificacao = classificar_ticker("HCRI11")
        assert elegivel_ffo(classificacao) is False

    def test_acao_nao_elegivel(self):
        classificacao = classificar_ticker("VALE3")
        assert elegivel_ffo(classificacao) is False

    def test_etf_nao_elegivel(self):
        classificacao = classificar_ticker("BOVA11")
        assert elegivel_ffo(classificacao) is False

    def test_bdr_nao_elegivel(self):
        classificacao = classificar_ticker("AAPL34")
        assert elegivel_ffo(classificacao) is False

    def test_desconhecido_nao_elegivel(self):
        classificacao = classificar_ticker("ZZZZ99")
        assert elegivel_ffo(classificacao) is False

    def test_fiagro_nao_elegivel(self):
        from flowscope.domain.fii import ClassificacaoAtivo, FonteClassificacao

        classificacao = ClassificacaoAtivo(
            ticker="SNAG11",
            tipo=TipoAtivo.FII,
            sub_tipo=SubTipoFii.FIAGRO,
            fonte=FonteClassificacao.TAXONOMIA_FII,
        )
        assert elegivel_ffo(classificacao) is False


class TestClassificacaoFiiAutorregulacao:
    def test_classe_papel_nao_elegivel(self):
        assert classe_fii_elegivel_ffo("Papel") is False

    def test_classe_tijolo_elegivel(self):
        assert classe_fii_elegivel_ffo("Tijolo") is True

    def test_classe_hibrido_elegivel(self):
        assert classe_fii_elegivel_ffo("Híbrido") is True

    def test_classe_desconhecida_indefinida(self):
        assert classe_fii_elegivel_ffo(None) is None
        assert classe_fii_elegivel_ffo("Outros") is None


class TestClassificacaoExibicaoComB3:
    def test_papel_prefixa_papel(self):
        exibicao = classificar_exibicao(
            discriminador="fii",
            segmento="Outros",
            gestao="Ativa",
            classificacao_fii="Papel",
        )
        assert exibicao.tipo == "FII"
        assert exibicao.sub_tipo == "Papel: Outros, Ativa"

    def test_tijolo_prefixa_tijolo(self):
        exibicao = classificar_exibicao(
            discriminador="fii",
            segmento="Logística",
            gestao="Ativa",
            classificacao_fii="Tijolo",
        )
        assert exibicao.sub_tipo == "Tijolo: Logística, Ativa"

    def test_hibrido_prefixa_tijolo(self):
        exibicao = classificar_exibicao(
            discriminador="fii",
            classificacao_fii="Híbrido",
        )
        assert exibicao.sub_tipo == "Tijolo:"

    def test_bdr_exibe_papel_com_sub_tipo_bdr(self):
        exibicao = classificar_exibicao(
            discriminador=None, fallback=classificar_ticker("EXXO34")
        )
        assert exibicao.tipo == "Papel"
        assert exibicao.sub_tipo == "BDR"

    def test_sem_classificacao_usa_qtd_imoveis(self):
        assert (
            classificar_exibicao(
                discriminador="fii", segmento="Outros", qtd_imoveis=0
            ).sub_tipo
            == "Papel: Outros"
        )
        assert (
            classificar_exibicao(
                discriminador="fii", segmento="Outros", qtd_imoveis=5
            ).sub_tipo
            == "Tijolo: Outros"
        )
