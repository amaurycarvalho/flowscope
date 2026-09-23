import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from flowscope.infrastructure.b3.emprestimos import (
    B3ShortInterestSource,
    parse_btb_lending,
)
from flowscope.infrastructure.cache import CacheManager

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "b3"
REFERENCIA = date(2026, 9, 22)


def _payload() -> dict:
    return json.loads(
        (_FIXTURES / "emprestimos_posicoes.json").read_text(encoding="utf-8")
    )


def _source(tmp_path: Path, fetch=None) -> B3ShortInterestSource:
    return B3ShortInterestSource(
        cache=CacheManager(cache_dir=tmp_path),
        fetch=fetch or (lambda _url: _payload()),
    )


class TestParser:
    def test_usa_linha_total_por_ticker(self):
        mapa = parse_btb_lending(_payload())
        assert mapa["PETR4"] == Decimal(194503553)
        assert mapa["VALE3"] == Decimal(101819420)

    def test_ticker_sem_total_soma_as_demais_linhas(self):
        mapa = parse_btb_lending(_payload())
        assert mapa["HGBS11"] == Decimal(229546)

    def test_payload_vazio_retorna_vazio(self):
        assert parse_btb_lending({}) == {}
        assert parse_btb_lending({"table": {}}) == {}
        assert parse_btb_lending(None) == {}


class TestSource:
    def test_ticker_presente_retorna_acoes_alugadas(self, tmp_path):
        source = _source(tmp_path)
        assert source.obter_acoes_alugadas("PETR4", REFERENCIA) == Decimal(194503553)

    def test_ticker_ausente_retorna_none(self, tmp_path):
        source = _source(tmp_path)
        assert source.obter_acoes_alugadas("XPTO3", REFERENCIA) is None

    def test_normaliza_ticker(self, tmp_path):
        source = _source(tmp_path)
        assert source.obter_acoes_alugadas(" petr4 ", REFERENCIA) == Decimal(194503553)

    def test_data_nao_publicada_recua_para_a_anterior(self, tmp_path):
        def fetch(url: str) -> dict:
            return _payload() if "2026-09-22" in url else {"table": {"values": []}}

        source = _source(tmp_path, fetch=fetch)
        assert source.obter_acoes_alugadas(
            "PETR4", REFERENCIA + timedelta(days=1)
        ) == Decimal(194503553)

    def test_fora_da_janela_retorna_none(self, tmp_path):
        def fetch(url: str) -> dict:
            return _payload() if "2026-09-22" in url else {"table": {"values": []}}

        source = _source(tmp_path, fetch=fetch)
        assert source.obter_acoes_alugadas(
            "PETR4", REFERENCIA + timedelta(days=30)
        ) is None

    def test_falha_de_rede_retorna_none(self, tmp_path):
        def fetch(_url: str) -> dict:
            raise RuntimeError("rede fora")

        source = _source(tmp_path, fetch=fetch)
        assert source.obter_acoes_alugadas("PETR4", REFERENCIA) is None

    def test_segunda_leitura_usa_cache(self, tmp_path):
        chamadas: list[str] = []

        def fetch(url: str) -> dict:
            chamadas.append(url)
            return _payload()

        source = _source(tmp_path, fetch=fetch)
        assert source.obter_acoes_alugadas("PETR4", REFERENCIA) == Decimal(194503553)
        assert source.obter_acoes_alugadas("PETR4", REFERENCIA) == Decimal(194503553)
        assert len(chamadas) == 1

    def test_pagina_multipla_agrega_todos_os_tickers(self, tmp_path):
        petr = {
            "table": {
                "pageCount": 2,
                "columns": [{"name": "TckrSymb"}, {"name": "Market"}, {"name": "StockBalance"}],
                "values": [["PETR4", "Total", 194503553]],
            }
        }
        vale = {
            "table": {
                "pageCount": 2,
                "columns": [{"name": "TckrSymb"}, {"name": "Market"}, {"name": "StockBalance"}],
                "values": [["VALE3", "Total", 101819420]],
            }
        }

        def fetch(url: str) -> dict:
            return petr if url.endswith("/1/1000") else vale

        source = _source(tmp_path, fetch=fetch)
        assert source.obter_acoes_alugadas("PETR4", REFERENCIA) == Decimal(194503553)
        assert source.obter_acoes_alugadas("VALE3", REFERENCIA) == Decimal(101819420)

    def test_url_inclui_data_em_iso(self, tmp_path):
        urls: list[str] = []

        def fetch(url: str) -> dict:
            urls.append(url)
            return _payload()

        source = _source(tmp_path, fetch=fetch)
        source.obter_acoes_alugadas("PETR4", REFERENCIA)
        assert urls and "/2026-09-22/2026-09-22/1/" in urls[0]
