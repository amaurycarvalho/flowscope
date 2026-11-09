from flowscope.application.performance.classificacao import (
    benchmark_padrao,
    benchmarks_disponiveis,
    classificar_elegiveis,
    tickers_para_benchmark,
)
from flowscope.domain.fii.classification import (
    ClassificacaoAtivo,
    ClassificacaoExibicao,
    FonteClassificacao,
    TipoAtivo,
)


def _analise(tipo: TipoAtivo) -> dict:
    return {
        "classificacao": ClassificacaoAtivo(
            ticker="X", tipo=tipo, sub_tipo=None, fonte=FonteClassificacao.SINTAXE
        )
    }


class TestClassificarElegiveis:
    def test_fundamental_tem_precedencia(self):
        resultado = classificar_elegiveis(
            ["ABCD11"], {"ABCD11": _analise(TipoAtivo.FII)}
        )
        assert resultado == {"ABCD11": "FII"}

    def test_fallback_sintatico_acao(self):
        assert classificar_elegiveis(["PETR4"]) == {"PETR4": "ACAO"}

    def test_fallback_taxonomia_fii(self):
        assert classificar_elegiveis(["HGLG11"]) == {"HGLG11": "FII"}

    def test_etf_bdr_e_desconhecido_ficam_fora(self):
        assert classificar_elegiveis(["BOVA11", "ABCD32", "XYZ"]) == {}

    def test_resolver_fiagro(self):
        resultado = classificar_elegiveis(
            ["KNRI11"], resolver_fiagro=lambda ticker: True
        )
        assert resultado == {"KNRI11": "FII"}

    def test_fundamental_com_formato_dict(self):
        resultado = classificar_elegiveis(
            ["XYZ"], {"XYZ": {"classificacao": {"tipo": "acao"}}}
        )
        assert resultado == {"XYZ": "ACAO"}

    def test_exibicao_fii_cobre_ticker_fora_da_taxonomia(self):
        analise = {
            "classificacao": {"tipo": "desconhecido"},
            "classificacao_exibicao": {
                "tipo": "FII", "sub_tipo": "Tijolo: Escritórios, Ativa",
            },
        }
        assert classificar_elegiveis(["TVRI11"], {"TVRI11": analise}) == {
            "TVRI11": "FII"
        }

    def test_exibicao_papel_vira_acao(self):
        analise = {"classificacao_exibicao": ClassificacaoExibicao("Papel", "ON")}
        assert classificar_elegiveis(["ABCD11"], {"ABCD11": analise}) == {
            "ABCD11": "ACAO"
        }

    def test_exibicao_bdr_e_etf_ficam_fora(self):
        for rotulo in ("BDR", "ETF"):
            analise = {"classificacao_exibicao": ClassificacaoExibicao("Papel", rotulo)}
            assert classificar_elegiveis(["ABCD11"], {"ABCD11": analise}) == {}


class TestBenchmarks:
    def test_somente_fii(self):
        assert benchmarks_disponiveis({"HGLG11": "FII"}) == ["IFIX"]

    def test_somente_acao(self):
        assert benchmarks_disponiveis({"PETR4": "ACAO"}) == ["IBOV", "IDIV"]

    def test_misto(self):
        opcoes = benchmarks_disponiveis({"HGLG11": "FII", "PETR4": "ACAO"})
        assert opcoes == ["IFIX", "IBOV", "IDIV"]

    def test_padrao_primeiro_fii(self):
        classificacao = {"PETR4": "ACAO", "HGLG11": "FII"}
        assert benchmark_padrao(["PETR4", "HGLG11"], classificacao) == "IBOV"
        assert benchmark_padrao(["HGLG11", "PETR4"], classificacao) == "IFIX"

    def test_padrao_sem_ticker(self):
        assert benchmark_padrao([], {}) is None

    def test_tickers_por_benchmark(self):
        classificacao = {"HGLG11": "FII", "PETR4": "ACAO", "VALE3": "ACAO"}
        assert tickers_para_benchmark(classificacao, "IFIX") == ["HGLG11"]
        assert tickers_para_benchmark(classificacao, "IBOV") == ["PETR4", "VALE3"]
