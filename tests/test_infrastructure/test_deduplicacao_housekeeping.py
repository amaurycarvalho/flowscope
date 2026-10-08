"""Testes da poda de derivados e do housekeeping de deduplicação por hash."""

import json
from datetime import date
from pathlib import Path

import pytest

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)
from flowscope.infrastructure.b3.noticias_index import (
    NoticiaMeta,
    NoticiasIndexStore,
)
from flowscope.infrastructure.b3.noticias_shards import (
    NoticiasSummaryStore,
    NoticiasTextStore,
)
from flowscope.infrastructure.content_hashes import (
    JsonHashStore,
    caminho_hashes_documentos,
    caminho_hashes_noticias,
    hash_sha256,
)
from flowscope.infrastructure.deduplicacao import (
    CandidatoHash,
    HousekeepingDeduplicacao,
    candidatos_documentos,
    candidatos_noticias,
    executar_housekeeping_documentos,
    executar_housekeeping_noticias,
    podar_documento,
    podar_noticia,
)
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.infrastructure.document_texts import JsonDocumentTextStore

_CONTEUDO_A = b"A" * 2048
_CONTEUDO_B = b"B" * 2048


def _escrever(caminho: Path, conteudo: bytes) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(conteudo)
    return caminho


def _meta(titulo: str = "Suspensão") -> NoticiaMeta:
    return NoticiaMeta(
        secao="Geral",
        titulo=titulo,
        data_publicacao="2026-09-20 10:00:00",
        categoria="Suspensão",
        url="https://x/1",
    )


class TestPodaDocumento:
    def test_remove_arquivo_resumo_e_texto(self, tmp_path):
        caminho = _escrever(
            tmp_path / "documentos-relevantes" / "ALZR11" / "2026"
            / "07" / "assembleia" / "1.pdf",
            _CONTEUDO_A,
        )
        relativo = caminho.relative_to(tmp_path).as_posix()
        JsonDocumentSummaryStore(tmp_path).salvar(
            "ALZR11", relativo, "curto", "longo"
        )
        JsonDocumentTextStore(tmp_path).salvar("ALZR11", relativo, "texto")
        podar_documento(tmp_path, "ALZR11", relativo)
        assert not caminho.exists()
        assert JsonDocumentSummaryStore(tmp_path).obter("ALZR11", relativo) is None
        assert JsonDocumentTextStore(tmp_path).obter("ALZR11", relativo) is None


class TestPodaNoticia:
    def test_remove_arquivo_indice_resumo_e_texto(self, tmp_path):
        caminho = _escrever(
            tmp_path / "noticias" / "2026" / "09" / "abc.html", _CONTEUDO_A
        )
        relativo = caminho.relative_to(tmp_path).as_posix()
        NoticiasIndexStore(tmp_path).registrar(caminho, _meta())
        NoticiasSummaryStore(tmp_path).salvar(
            "NOTICIAS", relativo, "curto", "longo"
        )
        NoticiasTextStore(tmp_path).salvar("NOTICIAS", relativo, "texto")
        podar_noticia(tmp_path, relativo)
        assert not caminho.exists()
        assert NoticiasIndexStore(tmp_path).itens() == {}
        assert NoticiasSummaryStore(tmp_path).obter("NOTICIAS", relativo) is None
        assert NoticiasTextStore(tmp_path).obter("NOTICIAS", relativo) is None


class TestRemocaoShards:
    def test_remove_apenas_o_shard_do_item(self, tmp_path):
        resumos = NoticiasSummaryStore(tmp_path)
        textos = NoticiasTextStore(tmp_path)
        chave_set = "noticias/2026/09/aaa.html"
        chave_out = "noticias/2026/10/bbb.html"
        resumos.salvar("NOTICIAS", chave_set, "c", "l")
        resumos.salvar("NOTICIAS", chave_out, "c2", "l2")
        textos.salvar("NOTICIAS", chave_set, "t")
        textos.salvar("NOTICIAS", chave_out, "t2")
        resumos.remover("NOTICIAS", chave_set)
        textos.remover("NOTICIAS", chave_set)
        assert resumos.obter("NOTICIAS", chave_set) is None
        assert textos.obter("NOTICIAS", chave_set) is None
        assert resumos.obter("NOTICIAS", chave_out) is not None
        assert textos.obter("NOTICIAS", chave_out) is not None


class TestRemocaoIndice:
    def test_remove_item_preserva_marcadores_da_geral(self, tmp_path):
        store = NoticiasIndexStore(tmp_path)
        caminho = tmp_path / "noticias" / "2026" / "09" / "abc.html"
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(_CONTEUDO_A)
        store.registrar_lote(
            [(caminho, _meta())],
            geral_mais_antiga=date(2026, 9, 1),
            geral_referencia=date(2026, 9, 25),
        )
        relativo = caminho.relative_to(tmp_path).as_posix()
        store.remover(relativo)
        assert store.itens() == {}
        doc = json.loads(store.path.read_text(encoding="utf-8"))
        assert doc["geral_mais_antiga"] == "2026-09-01"
        assert doc["geral_referencia"] == "2026-09-25"

    def test_remover_inexistente_nao_grava(self, tmp_path):
        store = NoticiasIndexStore(tmp_path)
        store.remover("noticias/2026/09/nao.html")
        assert not store.path.exists()


class TestCandidatos:
    def test_documentos_em_ordem_cronologica(self, tmp_path):
        _escrever(
            tmp_path / "informe-mensal" / "ALZR11" / "2026" / "07" / "2.html",
            _CONTEUDO_A,
        )
        _escrever(
            tmp_path / "bdr" / "ALZR11" / "2025" / "12" / "1.pdf",
            _CONTEUDO_B,
        )
        candidatos = candidatos_documentos(tmp_path, "ALZR11")
        relativos = [c.relativo for c in candidatos]
        assert relativos == [
            "bdr/ALZR11/2025/12/1.pdf",
            "informe-mensal/ALZR11/2026/07/2.html",
        ]

    def test_noticias_em_ordem_cronologica(self, tmp_path):
        _escrever(tmp_path / "noticias" / "2026" / "10" / "b.html", _CONTEUDO_A)
        _escrever(tmp_path / "noticias" / "2026" / "09" / "a.html", _CONTEUDO_B)
        candidatos = candidatos_noticias(tmp_path)
        assert [c.relativo for c in candidatos] == [
            "noticias/2026/09/a.html",
            "noticias/2026/10/b.html",
        ]


class TestHousekeepingDocumentos:
    def test_duplicatas_legadas_mantem_a_mais_antiga(self, tmp_path):
        antigo = _escrever(
            tmp_path / "documentos-relevantes" / "ALZR11" / "2025"
            / "01" / "assembleia" / "1.pdf",
            _CONTEUDO_A,
        )
        novo = _escrever(
            tmp_path / "informe-mensal" / "ALZR11" / "2026" / "05" / "2.html",
            _CONTEUDO_A,
        )
        executar_housekeeping_documentos(tmp_path, "ALZR11")
        assert antigo.exists()
        assert not novo.exists()

    def test_registro_compartilhado_entre_raizes(self, tmp_path):
        _escrever(
            tmp_path / "documentos-relevantes" / "ALZR11" / "2025"
            / "01" / "assembleia" / "1.pdf",
            _CONTEUDO_A,
        )
        _escrever(
            tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "2.pdf",
            _CONTEUDO_A,
        )
        executar_housekeeping_documentos(tmp_path, "ALZR11")
        registry = JsonHashStore(
            caminho_hashes_documentos(tmp_path, "ALZR11")
        )
        assert registry.registrados() == {
            hash_sha256(_CONTEUDO_A): (
                "documentos-relevantes/ALZR11/2025/01/assembleia/1.pdf"
            )
        }

    def test_sem_dedup_entre_tickers(self, tmp_path):
        primeiro = _escrever(
            tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "1.pdf",
            _CONTEUDO_A,
        )
        segundo = _escrever(
            tmp_path / "bdr" / "BZLI11" / "2026" / "02" / "2.pdf",
            _CONTEUDO_A,
        )
        executar_housekeeping_documentos(tmp_path, "ALZR11")
        assert primeiro.exists()
        assert segundo.exists()

    def test_canonico_ausente_e_reavaliado(self, tmp_path):
        digest = hash_sha256(_CONTEUDO_A)
        registry = JsonHashStore(caminho_hashes_documentos(tmp_path, "ALZR11"))
        registry.registrar(digest, "bdr/ALZR11/2026/01/sumido.pdf")
        atual = _escrever(
            tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "real.pdf",
            _CONTEUDO_A,
        )
        executar_housekeeping_documentos(tmp_path, "ALZR11")
        assert atual.exists()
        assert registry.canonico(digest) == "bdr/ALZR11/2026/02/real.pdf"

    def test_conteudo_pequeno_nao_e_registrado(self, tmp_path):
        arquivo = _escrever(
            tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "1.pdf", b"x"
        )
        executar_housekeeping_documentos(tmp_path, "ALZR11")
        assert arquivo.exists()
        assert JsonHashStore(
            caminho_hashes_documentos(tmp_path, "ALZR11")
        ).registrados() == {}

    def test_falha_de_leitura_nao_interrompe(self, tmp_path):
        _escrever(
            tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "bom.pdf",
            _CONTEUDO_A,
        )
        registry = JsonHashStore(caminho_hashes_documentos(tmp_path, "ALZR11"))
        housekeeping = HousekeepingDeduplicacao(
            tmp_path, registry, lambda relativo: None
        )
        candidatos = [
            CandidatoHash("ausente.pdf", tmp_path / "ausente.pdf", (0, 0, "a")),
            CandidatoHash(
                "bdr/ALZR11/2026/02/bom.pdf",
                tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "bom.pdf",
                (2026, 2, "bom.pdf"),
            ),
        ]
        housekeeping.executar(candidatos)
        assert registry.registrados() == {
            hash_sha256(_CONTEUDO_A): "bdr/ALZR11/2026/02/bom.pdf"
        }

    def test_cancelamento_interrompe(self, tmp_path):
        _escrever(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "1.pdf", _CONTEUDO_A)
        token = CancellationToken()
        token.request()
        with pytest.raises(OperacaoCancelada):
            executar_housekeeping_documentos(tmp_path, "ALZR11", token)


class TestHousekeepingNoticias:
    def test_duplicatas_globais_entre_datas(self, tmp_path):
        antiga = _escrever(
            tmp_path / "noticias" / "2026" / "01" / "a.html", _CONTEUDO_A
        )
        nova = _escrever(
            tmp_path / "noticias" / "2026" / "02" / "b.html", _CONTEUDO_A
        )
        executar_housekeeping_noticias(tmp_path)
        assert antiga.exists()
        assert not nova.exists()

    def test_dedup_entre_secoes(self, tmp_path):
        antiga = _escrever(
            tmp_path / "noticias" / "2026" / "01" / "a.html", _CONTEUDO_A
        )
        outra = _escrever(
            tmp_path / "noticias" / "2026" / "02" / "b.html", _CONTEUDO_A
        )
        executar_housekeeping_noticias(tmp_path)
        assert antiga.exists()
        assert not outra.exists()
        assert JsonHashStore(caminho_hashes_noticias(tmp_path)).registrados() == {
            hash_sha256(_CONTEUDO_A): "noticias/2026/01/a.html"
        }

    def test_remove_indice_e_derivados_da_duplicata(self, tmp_path):
        nova = _escrever(
            tmp_path / "noticias" / "2026" / "02" / "b.html", _CONTEUDO_A
        )
        _escrever(tmp_path / "noticias" / "2026" / "01" / "a.html", _CONTEUDO_A)
        relativo_nova = nova.relative_to(tmp_path).as_posix()
        NoticiasIndexStore(tmp_path).registrar(nova, _meta())
        NoticiasSummaryStore(tmp_path).salvar(
            "NOTICIAS", relativo_nova, "curto", "longo"
        )
        NoticiasTextStore(tmp_path).salvar("NOTICIAS", relativo_nova, "texto")
        executar_housekeeping_noticias(tmp_path)
        assert not nova.exists()
        assert NoticiasIndexStore(tmp_path).itens() == {}
        assert (
            NoticiasSummaryStore(tmp_path).obter("NOTICIAS", relativo_nova)
            is None
        )
        assert (
            NoticiasTextStore(tmp_path).obter("NOTICIAS", relativo_nova) is None
        )

    def test_cancelamento_interrompe(self, tmp_path):
        _escrever(tmp_path / "noticias" / "2026" / "01" / "a.html", _CONTEUDO_A)
        token = CancellationToken()
        token.request()
        with pytest.raises(OperacaoCancelada):
            executar_housekeeping_noticias(tmp_path, token)
