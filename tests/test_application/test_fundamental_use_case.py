from datetime import date
from decimal import Decimal

import pytest

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.application.fundamental_ports import (
    CAMPO_DIVIDENDO_POR_COTA,
    CampoFundamental,
    OrigemDados,
)
from flowscope.domain.fii import (
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
                net_asset_value=Decimal("2942000000"),
                shares_outstanding=Decimal("144355726"),
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
                    ffo_12m=Decimal("220777000"),
                    ffo_3m=Decimal("63802000"),
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
        assert resultado.ultimo_dividendo.tendencia is TendenciaDividendo.CRESCIMENTO
