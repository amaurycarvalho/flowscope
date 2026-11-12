import io
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.cvm import acionistas as mod
from flowscope.infrastructure.cvm.acionistas import (
    CvmAcionistasSource,
    parse_acoes_circulacao,
    parse_cadastro_cia,
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


def _downloader_csv(
    tmp_path: Path,
    nome_csv: str,
    conteudo: bytes,
    contador: list[int] | None = None,
) -> CvmDatasetDownloader:
    def fetch(ano: int) -> bytes:
        if contador is not None:
            contador.append(ano)
        return conteudo

    return CvmDatasetDownloader(
        base_url="https://example.invalid",
        arquivo=lambda _ano: nome_csv,
        dataset="cad_teste",
        cache_dir=tmp_path,
        fetch=fetch,
        zipado=False,
    )


def _source_fallback(
    tmp_path: Path,
    *,
    resolver=None,
    cad_conteudo: bytes | None = None,
    cad_erro: bool = False,
    parser_version: str = "cvm-acionistas-v2",
) -> CvmAcionistasSource:
    fre = _downloader(
        tmp_path,
        "fre_cia_aberta_distribuicao_capital_2026.csv",
        _fixture("fre_cia_aberta_distribuicao_capital_fallback_2026.csv"),
        "fre_cia_aberta_2026.zip",
    )
    fca = _downloader(
        tmp_path,
        "fca_cia_aberta_valor_mobiliario_2026.csv",
        _fixture("fca_cia_aberta_valor_mobiliario_fallback_2026.csv"),
        "fca_cia_aberta_2026.zip",
    )
    if cad_erro:
        def fetch(_ano: int) -> bytes:
            raise RuntimeError("cadastro indisponível")
        cad = CvmDatasetDownloader(
            base_url="https://example.invalid",
            arquivo=lambda _ano: "cad_cia_aberta.csv",
            dataset="cad_teste",
            cache_dir=tmp_path,
            fetch=fetch,
            zipado=False,
        )
    else:
        cad = _downloader_csv(
            tmp_path,
            "cad_cia_aberta.csv",
            cad_conteudo or _fixture("cad_cia_aberta_2026.csv"),
        )

    codigos = {
        "BPAC11": "22616",
        "CMIN3": "25585",
        "MBRF3": "20788",
        "CSNA3": "4030",
    }
    return CvmAcionistasSource(
        downloader_fre=fre,
        downloader_fca=fca,
        downloader_cad=cad,
        cache=CacheManager(cache_dir=tmp_path),
        parser_version=parser_version,
        resolver_code_cvm=resolver or (lambda ticker: codigos.get(ticker)),
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

    def test_parse_acoes_circulacao_maior_versao(self):
        mapa = parse_acoes_circulacao(
            _fixture("fre_cia_aberta_distribuicao_capital_2026.csv")
        )
        assert mapa[CNPJ_PETR] == Decimal("6000000000")
        assert mapa[CNPJ_AXIA] == Decimal("500000000")

    def test_parse_acoes_circulacao_ignora_ausente(self):
        mapa = parse_acoes_circulacao(
            _fixture("fre_cia_aberta_distribuicao_capital_2026.csv")
        )
        assert "00000000000191" not in mapa

    def test_parse_acoes_circulacao_vazio(self):
        assert parse_acoes_circulacao(b"") == {}


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

    def test_obter_free_float(self, tmp_path):
        source = _source(tmp_path)
        assert source.obter_free_float("PETR4", REFERENCIA) == Decimal("6000000000")
        assert source.obter_free_float("XPTO3", REFERENCIA) is None

    def test_obter_free_float_retorna_decimal_apos_cache(self, tmp_path):
        source = _source(tmp_path)
        assert source.obter_free_float("PETR4", REFERENCIA) == Decimal("6000000000")
        # A segunda leitura vem do cache normalizado (JSON serializa Decimal como texto).
        valor = source.obter_free_float("PETR4", REFERENCIA)
        assert isinstance(valor, Decimal)
        assert valor == Decimal("6000000000")

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


class TestParseCadastro:
    def test_normaliza_codigo_e_cnpj(self):
        mapa = parse_cadastro_cia(_fixture("cad_cia_aberta_2026.csv"))
        assert mapa["22616"]["cnpj"] == "30306294000145"
        assert mapa["25585"]["cnpj"] == "08902291000115"
        assert mapa["20788"]["cnpj"] == "03853896000140"
        assert mapa["4030"]["cnpj"] == "33042730000104"

    def test_inclui_razao_social(self):
        mapa = parse_cadastro_cia(_fixture("cad_cia_aberta_2026.csv"))
        assert mapa["22616"]["razao_social"] == "BANCO BTG PACTUAL S/A"
        assert mapa["4030"]["razao_social"] == "CIA SIDERURGICA NACIONAL"

    def test_ignora_registro_sem_cnpj_valido(self):
        mapa = parse_cadastro_cia(
            b"CNPJ_CIA;CD_CVM\n;123\n00000000000000;456\n"
        )
        assert mapa == {}


class TestFallbackCodeCvm:
    def test_watchlist_resolve_por_codecvm(self, tmp_path):
        source = _source_fallback(tmp_path)
        esperado = {
            "BPAC11": "30306294000145",
            "CMIN3": "08902291000115",
            "MBRF3": "03853896000140",
            "CSNA3": "33042730000104",
        }
        for ticker, cnpj in esperado.items():
            assert source.obter_cnpj(ticker, REFERENCIA) == cnpj

    def test_identidade_papel_inclui_razao_social(self, tmp_path):
        source = _source_fallback(tmp_path)
        esperado = {
            "BPAC11": ("30306294000145", "BANCO BTG PACTUAL S/A"),
            "CMIN3": ("08902291000115", "CSN MINERAÇÃO S.A."),
            "MBRF3": ("03853896000140", "MARFRIG GLOBAL FOODS SA"),
            "CSNA3": ("33042730000104", "CIA SIDERURGICA NACIONAL"),
        }
        for ticker, identidade in esperado.items():
            assert source.obter_identidade_papel(ticker, REFERENCIA) == identidade

    def test_identidade_papel_fca_sem_codecvm_mantem_cnpj(self, tmp_path):
        source = _source(tmp_path)
        assert source.obter_identidade_papel("PETR4", REFERENCIA) == (
            CNPJ_PETR,
            None,
        )

    def test_acionistas_e_free_float_usam_cnpj_do_fallback(self, tmp_path):
        source = _source_fallback(tmp_path)
        assert source.obter_acionistas("BPAC11", REFERENCIA) == 125
        assert source.obter_free_float("BPAC11", REFERENCIA) == Decimal(
            "1000000"
        )

    def test_sem_codecvm_retorna_none(self, tmp_path):
        source = _source_fallback(tmp_path, resolver=lambda _ticker: None)
        assert source.obter_cnpj("BPAC11", REFERENCIA) is None
        assert source.obter_cnpj("XPTO3", REFERENCIA) is None

    def test_cadastro_indisponivel_retorna_none(self, tmp_path):
        source = _source_fallback(tmp_path, cad_erro=True)
        assert source.obter_cnpj("BPAC11", REFERENCIA) is None

    def test_cache_legado_em_string_preserva_cnpj(self, tmp_path, monkeypatch):
        source = _source_fallback(tmp_path)
        monkeypatch.setattr(source, "_codigo_cvm", lambda ticker: "22616")
        monkeypatch.setattr(
            source,
            "_mapa",
            lambda *args, **kwargs: {"22616": "30306294000145"},
        )
        assert source.obter_identidade_papel("BPAC11", REFERENCIA) == (
            "30306294000145",
            None,
        )

    def test_cadastro_reaproveitado(self, tmp_path, monkeypatch):
        chamadas = {"n": 0}
        original = mod.parse_cadastro_cia

        def contando(conteudo):
            chamadas["n"] += 1
            return original(conteudo)

        monkeypatch.setattr(mod, "parse_cadastro_cia", contando)
        source = _source_fallback(tmp_path)
        assert source.obter_cnpj("BPAC11", REFERENCIA) == "30306294000145"
        assert source.obter_cnpj("CMIN3", REFERENCIA) == "08902291000115"
        assert chamadas["n"] == 1

    def test_mudanca_de_parser_invalida_cache_do_cadastro(
        self, tmp_path, monkeypatch
    ):
        chamadas = {"n": 0}
        original = mod.parse_cadastro_cia

        def contando(conteudo):
            chamadas["n"] += 1
            return original(conteudo)

        monkeypatch.setattr(mod, "parse_cadastro_cia", contando)
        p1 = _source_fallback(tmp_path, parser_version="p1")
        assert p1.obter_cnpj("BPAC11", REFERENCIA) == "30306294000145"
        p2 = _source_fallback(tmp_path, parser_version="p2")
        assert p2.obter_cnpj("BPAC11", REFERENCIA) == "30306294000145"
        assert chamadas["n"] == 2
