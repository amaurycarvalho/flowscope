from datetime import date
from decimal import Decimal

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.application.fundamental_ports import (
    CAMPO_COTACAO,
    CAMPO_COTAS_EMITIDAS,
    CAMPO_DISCRIMINADOR,
    CAMPO_DIVIDENDO_POR_COTA,
    CAMPO_MAX_52_SEM,
    CAMPO_MIN_52_SEM,
    CAMPO_P_L,
    CAMPO_VP_COTA,
    CampoFundamental,
    OrigemDados,
)
from flowscope.domain.bdr import DadosBdr
from flowscope.domain.fii import (
    ClasseCotistas,
    DividendoConsolidado,
    FfoObservacao,
    PatrimonioFii,
    PrecoObservacao,
    SubTipoAcao,
    SubTipoFii,
    TendenciaDividendo,
    TipoAtivo,
    UltimoDividendo,
)
from flowscope.domain.structured import ISIN, Provento, ValorProvento

REFERENCIA = date(2026, 9, 4)
_ISIN = "BR0000000000"


def _provento(tipo: str, data_base: date, valor: str, data_pagamento: date | None = None) -> Provento:
    return Provento(
        codigo_isin=ISIN(_ISIN),
        codigo_negociacao="X",
        tipo=tipo,
        data_base=data_base,
        valor_por_unidade=ValorProvento(Decimal(valor)),
        data_pagamento=data_pagamento or data_base,
        periodo_referencia="",
        isento_ir=True,
    )


class FakeFundamentalRepository:
    def __init__(self, proventos_por_ticker=None, nome_por_ticker=None,
                 patrimonio_por_ticker=None, falhar_em=None):
        self.proventos_por_ticker = proventos_por_ticker or {}
        self.nome_por_ticker = nome_por_ticker or {}
        self.patrimonio_por_ticker = patrimonio_por_ticker or {}
        self.falhar_em = falhar_em or set()

    def obter_nome(self, ticker: str) -> str | None:
        return self.nome_por_ticker.get(ticker)

    def obter_proventos(self, ticker: str, reference_date: date):
        if ticker in self.falhar_em:
            raise RuntimeError(f"falha ao obter proventos de {ticker}")
        return self.proventos_por_ticker.get(ticker, [])

    def obter_patrimonio(self, ticker: str, reference_date: date):
        return self.patrimonio_por_ticker.get(ticker)


class FakeFfoProvider:
    def __init__(self, ffo_por_ticker=None):
        self.ffo_por_ticker = ffo_por_ticker or {}

    def obter_ffo(self, ticker: str, reference_date: date):
        return self.ffo_por_ticker.get(ticker)


class FakeDividendHistory:
    def __init__(self, dividendos_por_ticker=None):
        self.dividendos_por_ticker = dividendos_por_ticker or {}

    def obter_dividendos(self, ticker: str, reference_date: date):
        return self.dividendos_por_ticker.get(ticker, [])


class FakeBdrProvider:
    def __init__(self, dados_por_ticker=None, falhar=False):
        self.dados_por_ticker = dados_por_ticker or {}
        self.falhar = falhar
        self.chamadas: list[str] = []

    def obter_dados_bdr(self, ticker: str, reference_date: date):
        self.chamadas.append(ticker)
        if self.falhar:
            raise RuntimeError("fonte de BDR indisponível")
        return self.dados_por_ticker.get(ticker)

    def obter_dividendos(self, ticker: str, reference_date: date):
        dados = self.dados_por_ticker.get(ticker)
        return list(dados.dividendos) if dados is not None else []


class FakeFundamentusFonte:
    def __init__(self, campos):
        self.campos = campos

    def obter(self, ticker: str, reference_date: date):
        return self.campos


class FakeMarket:
    def __init__(self, preco_por_ticker=None):
        self.preco_por_ticker = preco_por_ticker or {}

    def preco_fechamento(self, ticker: str, reference_date: date):
        return self.preco_por_ticker.get(ticker)


class FakeAcionistas:
    def __init__(self, por_ticker=None):
        self.por_ticker = por_ticker or {}

    def obter_acionistas(self, ticker: str, reference_date: date):
        return self.por_ticker.get(ticker)


class FakeIndexadores:
    def __init__(self, por_ticker=None):
        self.por_ticker = por_ticker or {}

    def obter_indexadores(self, ticker: str, reference_date: date):
        return self.por_ticker.get(ticker, {})


def _repo_hgbs11() -> FakeFundamentalRepository:
    return FakeFundamentalRepository(
        proventos_por_ticker={
            "HGBS11": [
                _provento("Rendimento", date(2026, 1, 15), "0.50", date(2026, 2, 1)),
                _provento("Rendimento", date(2026, 7, 10), "0.55", date(2026, 8, 1)),
                _provento("Amortização", date(2026, 5, 20), "3.00", date(2026, 6, 1)),
            ],
            "HCRI11": [
                _provento("Rendimento", date(2026, 3, 10), "1.00", date(2026, 4, 1)),
            ],
        },
        nome_por_ticker={
            "HGBS11": "CSHG Renda Urbana",
            "HCRI11": "CSHG Recebíveis Imobiliários",
            "PETR4": "Petrobras PN",
        },
        patrimonio_por_ticker={
            "HGBS11": PatrimonioFii(
                reference_date=REFERENCIA,
                net_asset_value=Decimal(2942000000),
                shares_outstanding=Decimal(144355726),
                cotistas=100000,
                fonte="CVM",
            ),
        },
    )


def _infra_completa():
    return (
        FakeFfoProvider(
            {
                "HGBS11": FfoObservacao(
                    ffo_12m=Decimal(220777000),
                    ffo_3m=Decimal(63802000),
                    fonte="FUNDAMENTUS",
                )
            }
        ),
        FakeMarket(
            {
                "HGBS11": PrecoObservacao(
                    preco=Decimal("18.74"), data_preco=REFERENCIA, fonte="B3"
                )
            }
        ),
    )


class TestFundamentalAnalysisUseCase:
    def test_linhas_por_ticker_da_watchlist(self):
        repo = _repo_hgbs11()
        ffo, mercado = _infra_completa()
        caso = FundamentalAnalysisUseCase(repo, ffo_provider=ffo, mercado=mercado)
        resultado = caso.execute(["PETR4", "HCRI11", "HGBS11"], REFERENCIA)
        assert [linha.ticker for linha in resultado] == ["PETR4", "HCRI11", "HGBS11"]

    def test_acao_identidade_sem_dividendos_e_ffo_na(self):
        repo = _repo_hgbs11()
        caso = FundamentalAnalysisUseCase(repo)
        resultado = caso.execute(["PETR4"], REFERENCIA)[0]
        assert resultado.classificacao.tipo is TipoAtivo.ACAO
        assert resultado.classificacao.sub_tipo is SubTipoAcao.PREFERENCIAL
        assert resultado.ultimo_dividendo == UltimoDividendo(
            data_com=None, valor=None, valor_anterior=None,
            tendencia=TendenciaDividendo.N_A,
        )
        assert resultado.metricas is None
        assert resultado.dividendos_12m_por_cota is None

    def test_fii_de_papel_tem_dividendos_mas_ffo_na(self):
        repo = _repo_hgbs11()
        caso = FundamentalAnalysisUseCase(repo)
        resultado = caso.execute(["HCRI11"], REFERENCIA)[0]
        assert resultado.classificacao.tipo is TipoAtivo.FII
        assert resultado.classificacao.sub_tipo is SubTipoFii.PAPEL
        assert resultado.ultimo_dividendo.valor == Decimal("1.00")
        assert resultado.metricas is None

    def test_fii_elegivel_calcula_metricas_ffo(self):
        repo = _repo_hgbs11()
        ffo, mercado = _infra_completa()
        caso = FundamentalAnalysisUseCase(repo, ffo_provider=ffo, mercado=mercado)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.classificacao.tipo is TipoAtivo.FII
        assert resultado.classificacao.sub_tipo is SubTipoFii.TIJOLO
        assert resultado.metricas is not None
        assert resultado.metricas.ffo_yield.quantize(Decimal("0.0001")) == Decimal("0.0816")
        assert resultado.metricas.p_ffo.quantize(Decimal("0.01")) == Decimal("12.25")
        assert resultado.dividendos_12m_por_cota == Decimal("1.05")
        assert resultado.avisos == ()

    def test_fii_elegivel_sem_dados_de_mercado_retorna_na(self):
        repo = _repo_hgbs11()
        caso = FundamentalAnalysisUseCase(repo, ffo_provider=FakeFfoProvider(),
                                          mercado=FakeMarket())
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.metricas is None
        assert resultado.avisos == ("FFO_NOT_AVAILABLE",)

    def test_cotacao_e_vp_cota_propagados_da_fonte(self):
        repo = _repo_hgbs11()
        fonte = FakeFundamentusFonte(
            {
                CAMPO_COTACAO: CampoFundamental(Decimal("104.13")),
                CAMPO_VP_COTA: CampoFundamental(Decimal("115.82")),
            }
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.cotacao == Decimal("104.13")
        assert resultado.vp_cota == Decimal("115.82")

    def test_cotacao_e_vp_cota_ausentes_retornam_none(self):
        repo = _repo_hgbs11()
        caso = FundamentalAnalysisUseCase(repo)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.cotacao is None
        assert resultado.vp_cota is None

    def test_falha_de_um_ticker_nao_invalida_os_demais(self):
        repo = _repo_hgbs11()
        repo.falhar_em = {"HGBS11"}
        caso = FundamentalAnalysisUseCase(repo)
        resultado = caso.execute(["HGBS11", "HCRI11"], REFERENCIA)
        assert resultado[0].erro is not None
        assert resultado[1].erro is None
        assert resultado[1].ultimo_dividendo.valor == Decimal("1.00")

    def test_isolamento_nao_interrompe_processamento(self):
        repo = _repo_hgbs11()
        ffo, mercado = _infra_completa()
        caso = FundamentalAnalysisUseCase(repo, ffo_provider=ffo, mercado=mercado)
        resultado = caso.execute(["HGBS11", "HCRI11", "PETR4"], REFERENCIA)
        assert len(resultado) == 3
        assert resultado[0].metricas is not None
        assert resultado[1].metricas is None
        assert resultado[2].metricas is None

    def test_tickers_sao_normalizados(self):
        repo = _repo_hgbs11()
        caso = FundamentalAnalysisUseCase(repo)
        resultado = caso.execute([" hgbs11 "], REFERENCIA)[0]
        assert resultado.ticker == "HGBS11"


class TestPl:
    def test_p_l_de_acao_vem_da_fonte(self):
        repo = _repo_hgbs11()
        fonte = FakeFundamentusFonte(
            {CAMPO_P_L: CampoFundamental(Decimal("5.19"))}
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["PETR4"], REFERENCIA)[0]
        assert resultado.p_l == Decimal("5.19")

    def test_p_l_de_fii_derivado_do_ultimo_dividendo(self):
        repo = FakeFundamentalRepository(
            proventos_por_ticker={
                "HGBS11": [_provento("Rendimento", date(2026, 7, 10), "0.55")]
            }
        )
        fonte = FakeFundamentusFonte(
            {CAMPO_COTACAO: CampoFundamental(Decimal("18.74"))}
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.p_l.quantize(Decimal("0.01")) == Decimal("2.84")

    def test_p_l_de_fii_sem_dividendo_e_none(self):
        repo = FakeFundamentalRepository()
        fonte = FakeFundamentusFonte(
            {CAMPO_COTACAO: CampoFundamental(Decimal("18.74"))}
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.p_l is None

    def test_p_l_de_acao_sem_fonte_e_none(self):
        repo = _repo_hgbs11()
        caso = FundamentalAnalysisUseCase(repo)
        resultado = caso.execute(["PETR4"], REFERENCIA)[0]
        assert resultado.p_l is None

    def test_p_l_de_fii_fora_da_taxonomia_usa_discriminador(self):
        repo = FakeFundamentalRepository(
            proventos_por_ticker={
                "ALZR11": [_provento("Rendimento", date(2026, 7, 10), "0.08")]
            }
        )
        fonte = FakeFundamentusFonte(
            {
                CAMPO_COTACAO: CampoFundamental(Decimal("9.99")),
                CAMPO_DISCRIMINADOR: CampoFundamental("fii"),
            }
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["ALZR11"], REFERENCIA)[0]
        assert resultado.p_l.quantize(Decimal("0.01")) == Decimal("10.41")

    def test_p_l_de_papel_com_discriminador_nao_deriva(self):
        repo = FakeFundamentalRepository(
            proventos_por_ticker={
                "PETR4": [_provento("Rendimento", date(2026, 7, 10), "0.50")]
            }
        )
        fonte = FakeFundamentusFonte(
            {
                CAMPO_COTACAO: CampoFundamental(Decimal("53.69")),
                CAMPO_DISCRIMINADOR: CampoFundamental("papel"),
            }
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["PETR4"], REFERENCIA)[0]
        assert resultado.p_l is None


class TestAcionistasPapel:
    def test_acao_preenche_cotistas_da_cvm(self):
        repo = _repo_hgbs11()
        caso = FundamentalAnalysisUseCase(
            repo, acionistas_provider=FakeAcionistas({"PETR4": 1183775})
        )
        resultado = caso.execute(["PETR4"], REFERENCIA)[0]
        assert resultado.cotistas == 1183775
        assert resultado.classe_cotistas is ClasseCotistas.GIGANTE

    def test_fii_mantem_cotistas_do_repositorio(self):
        repo = _repo_hgbs11()
        caso = FundamentalAnalysisUseCase(
            repo, acionistas_provider=FakeAcionistas({"HGBS11": 999})
        )
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.cotistas == 100000
        assert resultado.classe_cotistas is ClasseCotistas.MUITO_GRANDE

    def test_falha_do_provider_nao_quebra(self):
        class Explode:
            def obter_acionistas(self, ticker, reference_date):
                raise RuntimeError("indisponível")

        repo = _repo_hgbs11()
        caso = FundamentalAnalysisUseCase(repo, acionistas_provider=Explode())
        resultado = caso.execute(["PETR4"], REFERENCIA)[0]
        assert resultado.cotistas is None
        assert resultado.erro is None


class TestResolucaoCotas:
    def test_fii_prioriza_repositorio_sobre_fundamentus(self):
        repo = _repo_hgbs11()
        fonte = FakeFundamentusFonte(
            {CAMPO_COTAS_EMITIDAS: CampoFundamental(Decimal(999))}
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.cotas == Decimal(144355726)

    def test_fii_usa_fundamentus_quando_repositorio_ausente(self):
        repo = FakeFundamentalRepository()
        fonte = FakeFundamentusFonte(
            {CAMPO_COTAS_EMITIDAS: CampoFundamental(Decimal(144355726))}
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.cotas == Decimal(144355726)

    def test_papel_usa_fundamentus_e_ignora_repositorio(self):
        repo = FakeFundamentalRepository(
            patrimonio_por_ticker={
                "PETR4": PatrimonioFii(
                    reference_date=REFERENCIA,
                    net_asset_value=Decimal(1),
                    shares_outstanding=Decimal(111),
                    cotistas=1,
                    fonte="CVM",
                )
            }
        )
        fonte = FakeFundamentusFonte(
            {CAMPO_COTAS_EMITIDAS: CampoFundamental(Decimal(12888700000))}
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["PETR4"], REFERENCIA)[0]
        assert resultado.cotas == Decimal(12888700000)

    def test_ausente_retorna_none(self):
        repo = FakeFundamentalRepository()
        caso = FundamentalAnalysisUseCase(repo)
        resultado = caso.execute(["PETR4"], REFERENCIA)[0]
        assert resultado.cotas is None


class TestPrecoTipicoEIndexadores:
    def test_preco_tipico_e_percentual_calculados(self):
        repo = _repo_hgbs11()
        fonte = FakeFundamentusFonte(
            {
                CAMPO_COTACAO: CampoFundamental(Decimal(10)),
                CAMPO_MIN_52_SEM: CampoFundamental(Decimal(8)),
                CAMPO_MAX_52_SEM: CampoFundamental(Decimal(12)),
            }
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.preco_tipico == Decimal(10)
        assert resultado.pct_preco_tipico == Decimal(0)

    def test_preco_tipico_ausente_quando_falta_insumo(self):
        repo = _repo_hgbs11()
        fonte = FakeFundamentusFonte(
            {CAMPO_COTACAO: CampoFundamental(Decimal(10))}
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.preco_tipico is None
        assert resultado.pct_preco_tipico is None

    def test_indexadores_propagados_do_provider(self):
        repo = _repo_hgbs11()
        caso = FundamentalAnalysisUseCase(
            repo,
            indexadores_provider=FakeIndexadores(
                {"HGBS11": {"IPCA": Decimal("0.22"), "INCC": Decimal("0.05")}}
            ),
        )
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.indexadores == {
            "IPCA": Decimal("0.22"),
            "INCC": Decimal("0.05"),
        }

    def test_sem_indexadores_retorna_vazio(self):
        repo = _repo_hgbs11()
        caso = FundamentalAnalysisUseCase(repo)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.indexadores == {}

    def test_falha_do_provider_de_indexadores_nao_quebra(self):
        class Explode:
            def obter_indexadores(self, ticker, reference_date):
                raise RuntimeError("indisponível")

        repo = _repo_hgbs11()
        caso = FundamentalAnalysisUseCase(repo, indexadores_provider=Explode())
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.indexadores == {}
        assert resultado.erro is None


class _ProviderComResultado:
    def __init__(self, origem: OrigemDados) -> None:
        self._origem = origem

    def obter(self, ticker, reference_date):
        return {}

    def obter_com_resultado(self, ticker, reference_date):
        return {}, self._origem


class TestAgregacaoAtualizacao:
    def test_houve_atualizacao_quando_provider_atualiza(self):
        caso = FundamentalAnalysisUseCase(
            _repo_hgbs11(),
            fundamental_provider=_ProviderComResultado(OrigemDados.REDE),
        )
        caso.execute(["HGBS11"], REFERENCIA)
        assert caso.houve_atualizacao is True

    def test_sem_atualizacao_quando_provider_nao_atualiza(self):
        caso = FundamentalAnalysisUseCase(
            _repo_hgbs11(),
            fundamental_provider=_ProviderComResultado(OrigemDados.CACHE),
        )
        caso.execute(["HGBS11"], REFERENCIA)
        assert caso.houve_atualizacao is False

    def test_flag_resetada_entre_execucoes(self):
        caso = FundamentalAnalysisUseCase(
            _repo_hgbs11(),
            fundamental_provider=_ProviderComResultado(OrigemDados.REDE),
        )
        caso.execute(["HGBS11"], REFERENCIA)
        caso._fundamental_provider = _ProviderComResultado(OrigemDados.CACHE)
        caso.execute(["HGBS11"], REFERENCIA)
        assert caso.houve_atualizacao is False

    def test_progresso_marca_dado_em_cache(self):
        detalhes = []
        caso = FundamentalAnalysisUseCase(
            _repo_hgbs11(),
            fundamental_provider=_ProviderComResultado(OrigemDados.CACHE),
        )
        caso.execute(
            ["HGBS11"],
            REFERENCIA,
            progress_callback=lambda detalhe, falhou: detalhes.append(detalhe),
        )
        assert detalhes and detalhes[0].endswith(" - cached")

    def test_progresso_sem_cache_nao_marca(self):
        detalhes = []
        caso = FundamentalAnalysisUseCase(
            _repo_hgbs11(),
            fundamental_provider=_ProviderComResultado(OrigemDados.REDE),
        )
        caso.execute(
            ["HGBS11"],
            REFERENCIA,
            progress_callback=lambda detalhe, falhou: detalhes.append(detalhe),
        )
        assert detalhes and not detalhes[0].endswith(" - cached")


class TestConsolidacaoDividendos:
    def test_cvm_preenche_quando_b3_vazio(self):
        repo = FakeFundamentalRepository(proventos_por_ticker={"HGLG11": []})
        historico = FakeDividendHistory(
            {
                "HGLG11": [
                    DividendoConsolidado(date(2026, 1, 10), Decimal("1.00"), "CVM")
                ]
            }
        )
        caso = FundamentalAnalysisUseCase(repo, historico_dividendos=historico)
        resultado = caso.execute(["HGLG11"], REFERENCIA)[0]
        assert resultado.ultimo_dividendo.valor == Decimal("1.00")
        assert resultado.ultimo_dividendo.data_com == date(2026, 1, 10)

    def test_fundamentus_fallback_quando_sem_historico(self):
        repo = FakeFundamentalRepository()
        fonte = FakeFundamentusFonte(
            {CAMPO_DIVIDENDO_POR_COTA: CampoFundamental(Decimal("0.55"))}
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["HGLG11"], REFERENCIA)[0]
        assert resultado.ultimo_dividendo.valor == Decimal("0.55")
        assert resultado.ultimo_dividendo.data_com is None

    def test_b3_tem_prioridade_sobre_fundamentus(self):
        repo = FakeFundamentalRepository(
            proventos_por_ticker={
                "HGBS11": [_provento("Rendimento", date(2026, 1, 15), "0.50")]
            }
        )
        fonte = FakeFundamentusFonte(
            {CAMPO_DIVIDENDO_POR_COTA: CampoFundamental(Decimal("9.99"))}
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.ultimo_dividendo.valor == Decimal("0.50")

    def test_tendencia_usa_novos_rotulos(self):
        repo = FakeFundamentalRepository(
            proventos_por_ticker={
                "HGBS11": [
                    _provento("Rendimento", date(2026, 1, 15), "0.50"),
                    _provento("Rendimento", date(2026, 7, 10), "0.60"),
                ]
            }
        )
        caso = FundamentalAnalysisUseCase(repo)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.ultimo_dividendo.tendencia is TendenciaDividendo.FORTE_ALTA


class TestConsolidacaoPapel:
    def test_acao_preenche_dividendos_do_historico_fundamentus(self):
        repo = FakeFundamentalRepository()
        historico = FakeDividendHistory(
            {
                "PETR4": [
                    DividendoConsolidado(
                        date(2026, 3, 10), Decimal("0.30"), "FUNDAMENTUS"
                    ),
                    DividendoConsolidado(
                        date(2026, 6, 10), Decimal("0.45"), "FUNDAMENTUS"
                    ),
                ]
            }
        )
        caso = FundamentalAnalysisUseCase(repo, historico_dividendos=historico)
        resultado = caso.execute(["PETR4"], REFERENCIA)[0]
        assert resultado.ultimo_dividendo.data_com == date(2026, 6, 10)
        assert resultado.ultimo_dividendo.valor == Decimal("0.45")
        assert resultado.ultimo_dividendo.valor_anterior == Decimal("0.30")
        assert resultado.ultimo_dividendo.tendencia is TendenciaDividendo.FORTE_ALTA

    def test_fii_b3_preenche_data_com_anterior_e_tendencia(self):
        repo = FakeFundamentalRepository(
            proventos_por_ticker={
                "HGBS11": [
                    _provento("Rendimento", date(2026, 1, 15), "0.50"),
                    _provento("Rendimento", date(2026, 7, 10), "0.55"),
                ]
            }
        )
        fonte = FakeFundamentusFonte(
            {CAMPO_DIVIDENDO_POR_COTA: CampoFundamental(Decimal("9.99"))}
        )
        caso = FundamentalAnalysisUseCase(repo, fundamental_provider=fonte)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.ultimo_dividendo.data_com == date(2026, 7, 10)
        assert resultado.ultimo_dividendo.valor == Decimal("0.55")
        assert resultado.ultimo_dividendo.valor_anterior == Decimal("0.50")
        assert resultado.ultimo_dividendo.tendencia is TendenciaDividendo.FORTE_ALTA

    def test_p_l_de_fii_derivado_do_historico_secundario(self):
        repo = FakeFundamentalRepository()
        historico = FakeDividendHistory(
            {
                "HGBS11": [
                    DividendoConsolidado(
                        date(2026, 7, 10), Decimal("0.55"), "FUNDAMENTUS"
                    )
                ]
            }
        )
        fonte = FakeFundamentusFonte(
            {CAMPO_COTACAO: CampoFundamental(Decimal("18.74"))}
        )
        caso = FundamentalAnalysisUseCase(
            repo, fundamental_provider=fonte, historico_dividendos=historico
        )
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert resultado.p_l.quantize(Decimal("0.01")) == Decimal("2.84")


def _dados_bdr(
    valor: str = "0.50",
    nivel: str | None = "Nível I Não Patrocinado",
    observacao: str | None = "O valor informado já está deduzido de IR",
):
    return DadosBdr(
        dividendos=(
            DividendoConsolidado(date(2026, 8, 10), Decimal(valor), "BDR"),
        ),
        nivel_programa=nivel,
        observacao=observacao,
        nome_depositario="Banco B3 S.A.",
        nome_empresa="Exxon Mobil Corporation",
        isin="BREXXOBDR006",
    )


def _fonte_cotacao(valor: str):
    return FakeFundamentusFonte(
        {CAMPO_COTACAO: CampoFundamental(Decimal(valor))}
    )


class TestBdrDividendos:
    def test_fonte_bdr_preenche_data_com_tendencia_e_origem(self):
        repo = FakeFundamentalRepository()
        fonte = FakeBdrProvider({"EXXO34": _dados_bdr()})
        caso = FundamentalAnalysisUseCase(
            repo,
            fundamental_provider=_fonte_cotacao("10.00"),
            bdr_provider=fonte,
        )
        resultado = caso.execute(["EXXO34"], REFERENCIA)[0]
        assert resultado.ultimo_dividendo.data_com == date(2026, 8, 10)
        assert resultado.ultimo_dividendo.valor == Decimal("0.50")
        assert resultado.ultimo_dividendo.tendencia is TendenciaDividendo.N_A

    def test_pl_e_dividend_yield_bdr_anualizam_por_quatro(self):
        repo = FakeFundamentalRepository()
        fonte = FakeBdrProvider({"EXXO34": _dados_bdr()})
        caso = FundamentalAnalysisUseCase(
            repo,
            fundamental_provider=_fonte_cotacao("10.00"),
            bdr_provider=fonte,
        )
        resultado = caso.execute(["EXXO34"], REFERENCIA)[0]
        assert resultado.p_l == Decimal("5.00")
        assert resultado.metricas is not None
        assert resultado.metricas.dividend_yield == Decimal("0.20")

    def test_bdr_sem_cotacao_retorna_pl_e_dy_na(self):
        repo = FakeFundamentalRepository()
        fonte = FakeBdrProvider({"EXXO34": _dados_bdr()})
        caso = FundamentalAnalysisUseCase(repo, bdr_provider=fonte)
        resultado = caso.execute(["EXXO34"], REFERENCIA)[0]
        assert resultado.p_l is None
        assert resultado.metricas is None

    def test_bdr_cotacao_zero_retorna_pl_e_dy_na(self):
        repo = FakeFundamentalRepository()
        fonte = FakeBdrProvider({"EXXO34": _dados_bdr()})
        caso = FundamentalAnalysisUseCase(
            repo,
            fundamental_provider=_fonte_cotacao("0"),
            bdr_provider=fonte,
        )
        resultado = caso.execute(["EXXO34"], REFERENCIA)[0]
        assert resultado.p_l is None
        assert resultado.metricas is None

    def test_bdr_sem_dividendo_nao_calcula(self):
        repo = FakeFundamentalRepository()
        fonte = FakeBdrProvider(
            {"EXXO34": DadosBdr(dividendos=())}
        )
        caso = FundamentalAnalysisUseCase(
            repo,
            fundamental_provider=_fonte_cotacao("10.00"),
            bdr_provider=fonte,
        )
        resultado = caso.execute(["EXXO34"], REFERENCIA)[0]
        assert resultado.p_l is None
        assert resultado.ultimo_dividendo.valor is None

    def test_nome_bdr_usa_empresa_do_aviso_como_fallback(self):
        repo = FakeFundamentalRepository()
        fonte = FakeBdrProvider({"EXXO34": _dados_bdr()})
        caso = FundamentalAnalysisUseCase(repo, bdr_provider=fonte)
        resultado = caso.execute(["EXXO34"], REFERENCIA)[0]
        assert resultado.nome == "Exxon Mobil Corporation"

    def test_nome_de_fonte_primaria_tem_prioridade_sobre_bdr(self):
        repo = FakeFundamentalRepository(nome_por_ticker={"EXXO34": "EXXO"})
        fonte = FakeBdrProvider({"EXXO34": _dados_bdr()})
        caso = FundamentalAnalysisUseCase(repo, bdr_provider=fonte)
        resultado = caso.execute(["EXXO34"], REFERENCIA)[0]
        assert resultado.nome == "EXXO"

    def test_campos_de_bdr_preenchidos_apenas_para_bdr(self):
        repo = FakeFundamentalRepository()
        fonte = FakeBdrProvider({"EXXO34": _dados_bdr()})
        caso = FundamentalAnalysisUseCase(repo, bdr_provider=fonte)
        resultado = caso.execute(["EXXO34"], REFERENCIA)[0]
        assert resultado.bdr_nivel == "Nível I Não Patrocinado"
        assert resultado.bdr_observacao == (
            "O valor informado já está deduzido de IR"
        )
        assert resultado.nome_depositario == "Banco B3 S.A."
        assert resultado.nome_empresa_bdr == "Exxon Mobil Corporation"
        assert resultado.isin == "BREXXOBDR006"

    def test_ativo_nao_bdr_nao_aciona_a_fonte(self):
        repo = _repo_hgbs11()
        fonte = FakeBdrProvider()
        caso = FundamentalAnalysisUseCase(repo, bdr_provider=fonte)
        resultado = caso.execute(["HGBS11"], REFERENCIA)[0]
        assert fonte.chamadas == []
        assert resultado.bdr_nivel is None
        assert resultado.bdr_observacao is None
        assert resultado.nome_depositario is None

    def test_falha_da_fonte_bdr_nao_quebra_o_ticker(self):
        repo = FakeFundamentalRepository()
        fonte = FakeBdrProvider(falhar=True)
        caso = FundamentalAnalysisUseCase(repo, bdr_provider=fonte)
        resultado = caso.execute(["EXXO34"], REFERENCIA)[0]
        assert resultado.erro is None
        assert resultado.ultimo_dividendo.valor is None


class TestIntegracaoFiagroBdr:
    def test_fiagro_classificado_e_com_campos(self):
        repo = FakeFundamentalRepository(
            nome_por_ticker={"BBGO11": "BBGO FIAGRO"},
            patrimonio_por_ticker={
                "BBGO11": PatrimonioFii(
                    reference_date=REFERENCIA,
                    net_asset_value=Decimal(1000000),
                    shares_outstanding=Decimal(100000),
                    cotistas=5000,
                    fonte="B3",
                )
            },
        )
        fonte = _fonte_cotacao("10.00")
        caso = FundamentalAnalysisUseCase(
            repo,
            fundamental_provider=fonte,
            resolver_fiagro=lambda ticker: ticker in {"BBGO11", "KNCA11"},
        )
        resultado = caso.execute(["BBGO11"], REFERENCIA)[0]
        assert resultado.classificacao.tipo is TipoAtivo.FII
        assert resultado.classificacao.sub_tipo is SubTipoFii.FIAGRO
        assert resultado.classificacao.elegivel_ffo() is False
        assert resultado.nome == "BBGO FIAGRO"
        assert resultado.cotacao == Decimal("10.00")

    def test_linhas_de_fiagro_e_bdr_preenchem_campos_alvo(self):
        repo = FakeFundamentalRepository(
            nome_por_ticker={"BBGO11": "BBGO FIAGRO", "KNCA11": "KNCA FIAGRO"},
        )
        bdr = FakeBdrProvider({"EXXO34": _dados_bdr()})
        caso = FundamentalAnalysisUseCase(
            repo,
            fundamental_provider=_fonte_cotacao("10.00"),
            bdr_provider=bdr,
            resolver_fiagro=lambda ticker: ticker in {"BBGO11", "KNCA11"},
        )
        resultados = caso.execute(["BBGO11", "KNCA11", "EXXO34"], REFERENCIA)
        assert [r.ticker for r in resultados] == ["BBGO11", "KNCA11", "EXXO34"]
        assert all(r.classificacao.sub_tipo is SubTipoFii.FIAGRO for r in resultados[:2])
        exxo = resultados[2]
        assert exxo.classificacao.tipo is TipoAtivo.BDR
        assert exxo.nome_depositario == "Banco B3 S.A."
        assert exxo.p_l == Decimal("5.00")
