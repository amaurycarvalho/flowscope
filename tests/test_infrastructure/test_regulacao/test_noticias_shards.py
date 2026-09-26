"""Testes do particionamento dos caches de notícias por ano e mês."""

from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.infrastructure.b3.noticias_aquisicao import ESCOPO_NOTICIAS
from flowscope.infrastructure.b3.noticias_shards import (
    ESCOPO_SEM_DATA,
    NoticiasSummaryStore,
    NoticiasTextStore,
    escopo_shard,
)
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.infrastructure.document_texts import JsonDocumentTextStore

_CHAVE_SET = "noticias/2026/09/aaaa.html"
_CHAVE_MAR = "noticias/2025/03/bbbb.html"


class TestEscopoShard:
    def test_deriva_ano_e_mes_da_chave(self):
        assert escopo_shard(_CHAVE_SET) == "NOTICIAS-2026-09"
        assert escopo_shard("noticias/2026/1/x.html") == "NOTICIAS-2026-01"

    def test_chave_fora_do_padrao_usa_fallback(self):
        assert escopo_shard("outro/x.html") == ESCOPO_SEM_DATA
        assert escopo_shard("noticias/2026/13/x.html") == ESCOPO_SEM_DATA


class TestNoticiasTextStore:
    def test_grava_no_shard_do_mes(self, tmp_path):
        store = NoticiasTextStore(cache_dir=tmp_path)
        store.salvar(ESCOPO_NOTICIAS, _CHAVE_SET, "texto A")
        assert (tmp_path / "document-texts" / "NOTICIAS-2026-09.json").is_file()
        assert store.obter(ESCOPO_NOTICIAS, _CHAVE_SET) == "texto A"

    def test_gravar_um_shard_nao_toca_o_outro(self, tmp_path):
        store = NoticiasTextStore(cache_dir=tmp_path)
        store.salvar(ESCOPO_NOTICIAS, _CHAVE_SET, "setembro")
        setembro = tmp_path / "document-texts" / "NOTICIAS-2026-09.json"
        antes = setembro.read_bytes()
        store.salvar(ESCOPO_NOTICIAS, _CHAVE_MAR, "marco")
        assert setembro.read_bytes() == antes
        assert (tmp_path / "document-texts" / "NOTICIAS-2025-03.json").is_file()

    def test_textos_mescla_os_shards(self, tmp_path):
        store = NoticiasTextStore(cache_dir=tmp_path)
        store.salvar(ESCOPO_NOTICIAS, _CHAVE_SET, "setembro")
        store.salvar(ESCOPO_NOTICIAS, _CHAVE_MAR, "marco")
        assert store.textos(ESCOPO_NOTICIAS) == {
            _CHAVE_SET: "setembro",
            _CHAVE_MAR: "marco",
        }

    def test_migra_o_formato_anterior(self, tmp_path):
        legado = JsonDocumentTextStore(cache_dir=tmp_path)
        legado.salvar(ESCOPO_NOTICIAS, _CHAVE_SET, "setembro")
        legado.salvar(ESCOPO_NOTICIAS, _CHAVE_MAR, "marco")
        assert (tmp_path / "document-texts" / "NOTICIAS.json").is_file()

        store = NoticiasTextStore(cache_dir=tmp_path)
        assert store.obter(ESCOPO_NOTICIAS, _CHAVE_SET) == "setembro"
        assert store.obter(ESCOPO_NOTICIAS, _CHAVE_MAR) == "marco"
        assert not (tmp_path / "document-texts" / "NOTICIAS.json").exists()
        assert (tmp_path / "document-texts" / "NOTICIAS-2025-03.json").is_file()

    def test_migracao_nao_toca_documentos(self, tmp_path):
        documentos = JsonDocumentTextStore(cache_dir=tmp_path)
        documentos.salvar("ALZR11", "bdr/ALZR11/2026/02/10.pdf", "texto ALZR")
        JsonDocumentTextStore(cache_dir=tmp_path).salvar(
            ESCOPO_NOTICIAS, _CHAVE_SET, "setembro"
        )

        NoticiasTextStore(cache_dir=tmp_path).obter(ESCOPO_NOTICIAS, _CHAVE_SET)

        assert documentos.obter("ALZR11", "bdr/ALZR11/2026/02/10.pdf") == "texto ALZR"
        assert (tmp_path / "document-texts" / "ALZR11.json").is_file()


class TestEscala:
    def test_cada_gravacao_toca_apenas_o_shard_do_mes(self, tmp_path):
        store = NoticiasTextStore(cache_dir=tmp_path)
        gravados: list[str] = []
        original = store._gravar

        def espiao(ticker, textos):
            gravados.append(ticker)
            original(ticker, textos)

        store._gravar = espiao
        for i in range(24):
            mes = (i % 12) + 1
            store.salvar(
                ESCOPO_NOTICIAS,
                f"noticias/2026/{mes:02d}/{i:03d}.html",
                f"texto {i}",
            )

        assert len(gravados) == 24
        assert set(gravados) == {
            f"NOTICIAS-2026-{mes:02d}" for mes in range(1, 13)
        }


class TestNoticiasSummaryStore:
    def test_grava_e_mescla_resumos(self, tmp_path):
        store = NoticiasSummaryStore(cache_dir=tmp_path)
        store.salvar(ESCOPO_NOTICIAS, _CHAVE_SET, "curto set", "longo set")
        store.salvar(ESCOPO_NOTICIAS, _CHAVE_MAR, "curto mar", "longo mar")
        assert (
            tmp_path / "document-summaries" / "NOTICIAS-2026-09.json"
        ).is_file()
        assert store.obter(ESCOPO_NOTICIAS, _CHAVE_SET) == ResumoDocumento(
            "curto set", "longo set"
        )
        assert store.resumos(ESCOPO_NOTICIAS) == {
            _CHAVE_SET: ResumoDocumento("curto set", "longo set"),
            _CHAVE_MAR: ResumoDocumento("curto mar", "longo mar"),
        }

    def test_migra_o_formato_anterior(self, tmp_path):
        legado = JsonDocumentSummaryStore(cache_dir=tmp_path)
        legado.salvar(ESCOPO_NOTICIAS, _CHAVE_SET, "curto", "longo")
        assert (tmp_path / "document-summaries" / "NOTICIAS.json").is_file()

        store = NoticiasSummaryStore(cache_dir=tmp_path)
        assert store.obter(ESCOPO_NOTICIAS, _CHAVE_SET) == ResumoDocumento(
            "curto", "longo"
        )
        assert not (tmp_path / "document-summaries" / "NOTICIAS.json").exists()
