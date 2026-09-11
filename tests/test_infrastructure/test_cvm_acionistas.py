import io
import zipfile
from datetime import date
from pathlib import Path

import pytest

from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.cvm import acionistas as mod
from flowscope.infrastructure.cvm.acionistas import (
    CvmAcionistasSource,
    parse_distribuicao_capital,
    parse_valor_mobiliario,
)
from flowscope.infrastructure.cvm.datasets import CvmDatasetDownloader

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "cvm"
REFERENCIA = date(2026, 9, 4)
CNPJ_PETR = "33000167000101"
CNPJ_AXIA = "00001180000126"


def _fixture(nome: str) -> bytes:
    return (_FIXTURES / nome).read_bytes()


def _zip(csvs: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        for nome, conteudo in csvs.items():
            arquivo.writestr(nome, conteudo)
    return buffer.getvalue()


def _downloader(
    tmp_path: Path,
    nome_csv: str,
    conteudo: bytes,
    arquivo_zip: str,
    contador: list[int] | None = None,
) -> CvmDatasetDownloader:
    def fetch(ano: int) -> bytes:
        if contador is not None:
            contador.append(ano)
        return _zip({nome_csv: conteudo})

    return CvmDatasetDownloader(
        base_url="https://example.invalid",
        arquivo=lambda _ano: arquivo_zip,
        dataset="teste",
        cache_dir=tmp_path,
        fetch=fetch,
    )


def _source(tmp_path: Path) -> CvmAcionistasSource:
    fre = _downloader(
        tmp_path,
        "fre_cia_aberta_distribuicao_capital_2026.csv",
        _fixture("fre_cia_aberta_distribuicao_capital_2026.csv"),
        "fre_cia_aberta_2026.zip",
    )
    fca = _downloader(
        tmp_path,
        "fca_cia_aberta_valor_mobiliario_2026.csv",
        _fixture("fca_cia_aberta_valor_mobiliario_2026.csv"),
        "fca_cia_aberta_2026.zip",
    )
    return CvmAcionistasSource(
        downloader_fre=fre, downloader_fca=fca, cache=CacheManager(cache_dir=tmp_path)
    )


class TestParsers:
    def test_parse_valor_mobiliario(self):
        mapa = parse_valor_mobiliario(
            _fixture("fca_cia_aberta_valor_mobiliario_2026.csv")
        )
        assert mapa["PETR4"] == CNPJ_PETR
        assert mapa["PETR3"] == CNPJ_PETR
        assert mapa["AXIA3"] == CNPJ_AXIA

    def test_parse_distribuicao_capital_soma_tipos_e_maior_versao(self):
        mapa = parse_distribuicao_capital(
            _fixture("fre_cia_aberta_distribuicao_capital_2026.csv")
        )
        assert mapa[CNPJ_PETR] == 1175160 + 5987 + 2628
        assert mapa[CNPJ_AXIA] == 211771 + 45586 + 1462

    def test_parse_distribuicao_capital_vazio(self):
        assert parse_distribuicao_capital(b"") == {}
        assert parse_valor_mobiliario(b"") == {}


class TestSource:
    def test_ticker_presente_resolve_quantidade(self, tmp_path):
        source = _source(tmp_path)
        assert source.obter_acionistas("PETR4", REFERENCIA) == 1183775

    def test_ticker_ausente_retorna_none(self, tmp_path):
        source = _source(tmp_path)
        assert source.obter_acionistas("XPTO3", REFERENCIA) is None

    def test_obter_cnpj_resolve_no_fca(self, tmp_path):
        source = _source(tmp_path)
        assert source.obter_cnpj("PETR4", REFERENCIA) == CNPJ_PETR
        assert source.obter_cnpj("XPTO3", REFERENCIA) is None

    def test_falha_de_rede_retorna_none(self, tmp_path):
        def fetch(_ano: int) -> bytes:
            raise RuntimeError("rede fora")

        fre = CvmDatasetDownloader(
            base_url="https://example.invalid",
            arquivo=lambda _ano: "fre.zip",
            dataset="fre",
            cache_dir=tmp_path,
            fetch=fetch,
        )
        fca = CvmDatasetDownloader(
            base_url="https://example.invalid",
            arquivo=lambda _ano: "fca.zip",
            dataset="fca",
            cache_dir=tmp_path,
            fetch=fetch,
        )
        source = CvmAcionistasSource(
            downloader_fre=fre,
            downloader_fca=fca,
            cache=CacheManager(cache_dir=tmp_path),
        )
        assert source.obter_acionistas("PETR4", REFERENCIA) is None


class TestCacheNormalizado:
    def test_segunda_resolucao_usa_cache_normalizado(self, tmp_path, monkeypatch):
        chamadas = {"fre": 0, "fca": 0}
        original_fre = mod.parse_distribuicao_capital
        original_fca = mod.parse_valor_mobiliario

        def cont_fre(conteudo):
            chamadas["fre"] += 1
            return original_fre(conteudo)

        def cont_fca(conteudo):
            chamadas["fca"] += 1
            return original_fca(conteudo)

        monkeypatch.setattr(mod, "parse_distribuicao_capital", cont_fre)
        monkeypatch.setattr(mod, "parse_valor_mobiliario", cont_fca)
        source = _source(tmp_path)
        assert source.obter_acionistas("PETR4", REFERENCIA) == 1183775
        assert source.obter_acionistas("PETR4", REFERENCIA) == 1183775
        assert chamadas == {"fre": 1, "fca": 1}

    def test_mudanca_de_parser_invalida_cache(self, tmp_path, monkeypatch):
        chamadas = {"n": 0}
        original = mod.parse_distribuicao_capital

        def contando(conteudo):
            chamadas["n"] += 1
            return original(conteudo)

        monkeypatch.setattr(mod, "parse_distribuicao_capital", contando)
        fre = _downloader(
            tmp_path,
            "fre_cia_aberta_distribuicao_capital_2026.csv",
            _fixture("fre_cia_aberta_distribuicao_capital_2026.csv"),
            "fre_cia_aberta_2026.zip",
        )
        fca = _downloader(
            tmp_path,
            "fca_cia_aberta_valor_mobiliario_2026.csv",
            _fixture("fca_cia_aberta_valor_mobiliario_2026.csv"),
            "fca_cia_aberta_2026.zip",
        )
        cache = CacheManager(cache_dir=tmp_path)
        p1 = CvmAcionistasSource(
            downloader_fre=fre, downloader_fca=fca, cache=cache, parser_version="p1"
        )
        assert p1.obter_acionistas("PETR4", REFERENCIA) == 1183775
        assert chamadas["n"] == 1
        p2 = CvmAcionistasSource(
            downloader_fre=fre, downloader_fca=fca, cache=cache, parser_version="p2"
        )
        assert p2.obter_acionistas("PETR4", REFERENCIA) == 1183775
        assert chamadas["n"] == 2
