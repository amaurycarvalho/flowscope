from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
import requests

from flowscope.domain.fii.fundamentus import TIPO_ACAO, TIPO_FII
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.fii.fundamentus.client import FundamentusClient
from flowscope.infrastructure.fii.fundamentus.errors import (
    LayoutChanged,
    NetworkError,
    TickerNotFound,
)
from flowscope.infrastructure.fii.fundamentus.normalizers import (
    para_data,
    para_decimal,
    para_int,
)
from flowscope.infrastructure.fii.fundamentus.parser import parse_ativo
from flowscope.infrastructure.fii.fundamentus.provider import FundamentusProvider

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "fundamentus"


def _fixture(nome: str) -> str:
    return (_FIXTURES / nome).read_text(encoding="utf-8")


class TestNormalizadores:
    def test_decimal_com_milhar(self):
        assert para_decimal("R$ 691.996.000.000") == Decimal(691996000000)

    def test_percentual_negativo(self):
        assert para_decimal("-0,08%") == Decimal("-0.08")

    def test_decimal_com_virgula(self):
        assert para_decimal("1.234,56") == Decimal("1234.56")

    def test_celulas_vazias(self):
        assert para_decimal("") is None
        assert para_decimal("-") is None
        assert para_decimal(None) is None

    def test_int(self):
        assert para_int("11") == 11
        assert para_int("") is None

    def test_data(self):
        assert para_data("10/09/2026") == date(2026, 9, 10)
        assert para_data("") is None


class TestParser:
    def test_parse_acao(self):
        ativo = parse_ativo("petr4", _fixture("acao_petr4.html"))
        assert ativo.ticker == "PETR4"
        assert ativo.tipo == TIPO_ACAO
        assert ativo.nome == "PETROBRAS PN"
        assert ativo.cotacao == Decimal("53.69")
        assert ativo.data_ultima_cotacao == date(2026, 9, 10)
        assert ativo.min_52_sem == Decimal("30.00")
        assert ativo.max_52_sem == Decimal("60.00")
        assert ativo.volume_medio_2m == Decimal(1234567)
        assert ativo.oscilacoes["Dia"] == Decimal("-0.08")
        assert ativo.indicadores["P/VP"] == Decimal("1.20")
        assert ativo.indicadores["Div. Yield"] == Decimal("7.30")
        assert ativo.demonstrativos_12m["Lucro Líquido"] == Decimal(133376000000)
        assert ativo.demonstrativos_3m["Lucro Líquido"] == Decimal(33000000000)
        assert ativo.raw["Nome"] == "PETROBRAS PN"

    def test_parse_fii(self):
        ativo = parse_ativo("hgbs11", _fixture("fii_hgbs11.html"))
        assert ativo.tipo == TIPO_FII
        assert ativo.eh_fii() is True
        assert ativo.indicadores["FFO Yield"] == Decimal("8.16")
        assert ativo.indicadores["P/VP"] == Decimal("0.92")
        assert ativo.demonstrativos_12m["FFO"] == Decimal(220777000)
        assert ativo.demonstrativos_3m["FFO"] == Decimal(63802000)
        assert ativo.imoveis["qtd_imoveis"] == 11
        assert ativo.imoveis["area_m2"] == Decimal(545901)
        assert ativo.composicao_ativos["Imóveis para Renda"] == Decimal(60)
        assert ativo.composicao_ativos["CRI / CRA"] == Decimal(30)

    def test_campos_ausentes_retornam_none(self):
        ativo = parse_ativo("petr4", _fixture("acao_petr4.html"))
        assert ativo.imoveis["qtd_imoveis"] is None
        assert ativo.composicao_ativos == {}

    def test_layout_alterado_levanta(self):
        with pytest.raises(LayoutChanged):
            parse_ativo("XPTO", "<html><body><p>vazio</p></body></html>")


class _FakeResponse:
    def __init__(self, text: str, status: int = 200) -> None:
        self.text = text
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class _FakeSession:
    def __init__(self, resposta: _FakeResponse) -> None:
        self._resposta = resposta
        self.chamadas: list[dict] = []

    def get(self, url: str, **kwargs) -> _FakeResponse:
        self.chamadas.append({"url": url, **kwargs})
        return self._resposta


class TestClient:
    def test_fetch_serializa_requisicoes(self):
        dormidas: list[float] = []
        session = _FakeSession(_FakeResponse(_fixture("fii_hgbs11.html")))
        client = FundamentusClient(
            session=session,
            sleep=dormidas.append,
            rate_limit_s=0.5,
            respect_robots=False,
        )
        client.fetch("HGBS11")
        client.fetch("HGBS11")
        assert len(session.chamadas) == 2
        assert dormidas and dormidas[0] > 0

    def test_ticker_nao_encontrado(self):
        session = _FakeSession(_FakeResponse("Nenhum papel encontrado"))
        client = FundamentusClient(session=session, respect_robots=False)
        with pytest.raises(TickerNotFound):
            client.fetch("XPTO")

    def test_falha_de_rede(self):
        session = _FakeSession(_FakeResponse("erro", status=500))
        client = FundamentusClient(session=session, respect_robots=False)
        with pytest.raises(NetworkError):
            client.fetch("PETR4")

    def test_robots_bloqueia(self):
        import urllib.robotparser

        parser = urllib.robotparser.RobotFileParser()
        parser.parse(["User-agent: *", "Disallow: /detalhes.php"])
        session = _FakeSession(_FakeResponse(_fixture("acao_petr4.html")))
        client = FundamentusClient(
            session=session, robot_parser=parser, respect_robots=True
        )
        with pytest.raises(NetworkError):
            client.fetch("PETR4")


class TestProvider:
    def test_get_com_loader(self):
        provider = FundamentusProvider(loader=lambda _t: _fixture("fii_hgbs11.html"))
        ativo = provider.get("hgbs11")
        assert ativo.ticker == "HGBS11"
        assert ativo.tipo == TIPO_FII

    def test_get_usa_cache(self, tmp_path):
        chamadas: list[str] = []

        def loader(ticker: str) -> str:
            chamadas.append(ticker)
            return _fixture("fii_hgbs11.html")

        provider = FundamentusProvider(
            loader=loader, cache=CacheManager(cache_dir=tmp_path)
        )
        provider.get("HGBS11")
        provider.get("HGBS11")
        assert chamadas == ["HGBS11"]
