from datetime import date
from decimal import Decimal

from flowscope.domain.entities import TradeDay
from flowscope.domain.fii import PatrimonioFii
from flowscope.domain.fii.analysis import PatrimonioFii
from flowscope.domain.structured import (
    CNPJ,
    DocumentoProvento,
    Entidade,
    ISIN,
    Provento,
    ValorProvento,
)
from flowscope.domain.value_objects import Price, Ticker, Volume
from flowscope.infrastructure.fii.b3_price import B3MarketPricePort
from flowscope.infrastructure.fii.fundamental_repository import FundamentalRepository

REFERENCIA = date(2026, 9, 4)


def _documento(tipo: str, data_base: date, valor: str) -> DocumentoProvento:
    provento = Provento(
        codigo_isin=ISIN("BR0000000000"),
        codigo_negociacao="HGBS11",
        tipo=tipo,
        data_base=data_base,
        valor_por_unidade=ValorProvento(Decimal(valor)),
        data_pagamento=data_base,
        periodo_referencia="",
        isento_ir=True,
    )
    entidade = Entidade(
        nome="CSHG Renda Urbana",
        cnpj=CNPJ("12.345.678/0001-95"),
        nome_administrador="Administradora",
        cnpj_administrador=CNPJ("98.765.432/0001-10"),
        responsavel="Responsável",
        telefone="(11) 1111-1111",
    )
    return DocumentoProvento(
        ticker="HGBS11",
        id_fnet="id-fnet",
        id_documento="id-documento",
        url_documento="https://example.org/doc",
        data_extracao="2026-09-01",
        entidade=entidade,
        provento=provento,
    )


class StubProventosUseCase:
    def __init__(self, documentos, excecao: Exception | None = None):
        self.documentos = documentos
        self.excecao = excecao
        self.chamadas: list[tuple[str, date, date]] = []

    def execute(self, ticker, data_inicio, data_fim, progress_callback=None):
        self.chamadas.append((ticker, data_inicio, data_fim))
        if self.excecao is not None:
            raise self.excecao
        if ticker != "HGBS11":
            return []
        return self.documentos


class TestFundamentalRepository:
    def test_obter_proventos_retorna_lista(self):
        stub = StubProventosUseCase(
            [_documento("Rendimento", date(2026, 8, 1), "0.55")]
        )
        repositorio = FundamentalRepository(proventos_use_case=stub)
        proventos = repositorio.obter_proventos("HGBS11", REFERENCIA)
        assert len(proventos) == 1
        assert proventos[0].tipo == "Rendimento"

    def test_obter_nome_do_primeiro_documento(self):
        stub = StubProventosUseCase(
            [_documento("Rendimento", date(2026, 8, 1), "0.55")]
        )
        repositorio = FundamentalRepository(proventos_use_case=stub)
        assert repositorio.obter_nome("HGBS11") == "CSHG Renda Urbana"

    def test_ticker_sem_dados_retorna_vazio(self):
        stub = StubProventosUseCase([_documento("Rendimento", date(2026, 8, 1), "0.55")])
        repositorio = FundamentalRepository(proventos_use_case=stub)
        assert repositorio.obter_proventos("PETR4", REFERENCIA) == []
        assert repositorio.obter_nome("PETR4") is None

    def test_falha_na_fonte_retorna_vazio_sem_erro(self):
        stub = StubProventosUseCase([], excecao=RuntimeError("boom"))
        repositorio = FundamentalRepository(proventos_use_case=stub)
        assert repositorio.obter_proventos("HGBS11", REFERENCIA) == []
        assert repositorio.obter_nome("HGBS11") is None

    def test_resultado_memorizado_evita_nova_busca(self):
        stub = StubProventosUseCase(
            [_documento("Rendimento", date(2026, 8, 1), "0.55")]
        )
        repositorio = FundamentalRepository(proventos_use_case=stub)
        repositorio.obter_proventos("HGBS11", REFERENCIA)
        repositorio.obter_proventos("HGBS11", REFERENCIA)
        assert len(stub.chamadas) == 1

    def test_patrimonio_sem_fonte_retorna_none(self):
        repositorio = FundamentalRepository(proventos_use_case=StubProventosUseCase([]))
        assert repositorio.obter_patrimonio("HGBS11", REFERENCIA) is None

    def test_patrimonio_delega_para_fonte_cvm(self):
        esperado = PatrimonioFii(
            reference_date=REFERENCIA,
            net_asset_value=Decimal("2942000000"),
            shares_outstanding=Decimal("144355726"),
            cotistas=100,
            fonte="CVM",
        )

        class FonteStub:
            def patrimonio(self, ticker, reference_date):
                if ticker == "HGBS11":
                    return esperado
                return None

        repositorio = FundamentalRepository(
            proventos_use_case=StubProventosUseCase([]),
            patrimonio_source=FonteStub(),
        )
        assert repositorio.obter_patrimonio("HGBS11", REFERENCIA) is esperado
        assert repositorio.obter_patrimonio("PETR4", REFERENCIA) is None


class TestB3MarketPricePort:
    def _negociacao(self, ticker: str, dia: date, preco: str) -> TradeDay:
        return TradeDay(
            date=dia,
            ticker=Ticker(ticker),
            segment="CASH",
            min_price=Price(preco),
            max_price=Price(preco),
            avg_price=Price(preco),
            last_price=Price(preco),
            trades_qty=Volume(100),
            fin_vol=Decimal("1000"),
            fin_instr_qty=100,
        )

    def test_retorna_ultimo_fechamento_ate_a_referencia(self):
        port = B3MarketPricePort(
            [
                self._negociacao("HGBS11", date(2026, 9, 1), "18.00"),
                self._negociacao("HGBS11", date(2026, 9, 3), "18.74"),
                self._negociacao("HGBS11", date(2026, 9, 5), "19.00"),
            ]
        )
        preco = port.preco_fechamento("HGBS11", date(2026, 9, 4))
        assert preco is not None
        assert preco.preco == Decimal("18.74")
        assert preco.data_preco == date(2026, 9, 3)

    def test_ignora_dados_futuros(self):
        port = B3MarketPricePort(
            [self._negociacao("HGBS11", date(2026, 9, 10), "19.00")]
        )
        assert port.preco_fechamento("HGBS11", date(2026, 9, 4)) is None

    def test_ignora_preco_zero(self):
        negociacao = self._negociacao("HGBS11", date(2026, 9, 3), "0.00")
        port = B3MarketPricePort([negociacao])
        assert port.preco_fechamento("HGBS11", date(2026, 9, 4)) is None

    def test_normaliza_ticker(self):
        port = B3MarketPricePort(
            [self._negociacao("HGBS11", date(2026, 9, 3), "18.74")]
        )
        preco = port.preco_fechamento(" hgbs11 ", date(2026, 9, 4))
        assert preco is not None
        assert preco.preco == Decimal("18.74")

    def test_ticker_sem_dados_retorna_none(self):
        port = B3MarketPricePort([])
        assert port.preco_fechamento("PETR4", date(2026, 9, 4)) is None
