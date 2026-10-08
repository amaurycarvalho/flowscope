"""Testes do hash SHA-256 e do registro de hashes em JSON."""

import json
from pathlib import Path

from flowscope.infrastructure.content_hashes import (
    DIRETORIO_HASHES,
    JsonHashStore,
    _CARACTERES_INSEGUROS,
    caminho_hashes_documentos,
    caminho_hashes_noticias,
    deduplicacao_documentos,
    deduplicacao_noticias,
    hash_de_caminho,
    hash_sha256,
    raiz_cache,
)

_ESPERADO_VAZIO = (
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)
_ESPERADO_ABC = (
    "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
)


class TestHashSha256:
    def test_digest_conhecido_vazio(self):
        assert hash_sha256(b"") == _ESPERADO_VAZIO

    def test_digest_conhecido_abc(self):
        assert hash_sha256(b"abc") == _ESPERADO_ABC

    def test_estavel(self):
        assert hash_sha256(b"conteudo") == hash_sha256(b"conteudo")


class TestCaminhos:
    def test_documentos_por_ticker(self):
        caminho = caminho_hashes_documentos("/base", "alzr11")
        assert caminho == Path("/base", DIRETORIO_HASHES, "ALZR11.json")

    def test_documentos_sanitiza_ticker(self):
        caminho = caminho_hashes_documentos("/base", "../x")
        assert _CARACTERES_INSEGUROS.search(caminho.name) is None

    def test_noticias_global(self):
        caminho = caminho_hashes_noticias("/base")
        assert caminho.parts[-2:] == ("noticias", "hashes.json")


class TestRaizCache:
    def test_subpasta_nomeada_sobe_um_nivel(self):
        assert raiz_cache(Path("/base/bdr")) == Path("/base")

    def test_raiz_explicita_permanece(self):
        assert raiz_cache(Path("/tmp/xyz")) == Path("/tmp/xyz")


class TestJsonHashStore:
    def test_round_trip(self, tmp_path):
        store = JsonHashStore(tmp_path / "hashes.json")
        assert store.registrados() == {}
        store.registrar("h1", "a.pdf")
        store.registrar("h2", "b.pdf")
        assert store.canonico("h1") == "a.pdf"
        assert store.registrados() == {"h1": "a.pdf", "h2": "b.pdf"}
        recarregado = JsonHashStore(tmp_path / "hashes.json")
        assert recarregado.registrados() == {"h1": "a.pdf", "h2": "b.pdf"}

    def test_arquivo_ausente(self, tmp_path):
        store = JsonHashStore(tmp_path / "nao_existe.json")
        assert store.registrados() == {}
        assert store.canonico("h") is None

    def test_arquivo_corrompido(self, tmp_path):
        caminho = tmp_path / "hashes.json"
        caminho.write_text("{invalido", encoding="utf-8")
        assert JsonHashStore(caminho).registrados() == {}

    def test_formato_invalido_e_tolerado(self, tmp_path):
        caminho = tmp_path / "hashes.json"
        caminho.write_text(json.dumps({"hashes": ["x"]}), encoding="utf-8")
        assert JsonHashStore(caminho).registrados() == {}

    def test_remover(self, tmp_path):
        store = JsonHashStore(tmp_path / "hashes.json")
        store.registrar("h1", "a.pdf")
        store.registrar("h2", "b.pdf")
        store.remover("h1")
        assert store.registrados() == {"h2": "b.pdf"}

    def test_remover_inexistente_nao_grava(self, tmp_path):
        caminho = tmp_path / "hashes.json"
        store = JsonHashStore(caminho)
        store.remover("nada")
        assert not caminho.exists()

    def test_remover_relativo(self, tmp_path):
        store = JsonHashStore(tmp_path / "hashes.json")
        store.registrar("h1", "a.pdf")
        store.registrar("h2", "b.pdf")
        store.remover_relativo("a.pdf")
        assert store.registrados() == {"h2": "b.pdf"}

    def test_nao_deixa_temporario(self, tmp_path):
        store = JsonHashStore(tmp_path / "hashes.json")
        store.registrar("h1", "a.pdf")
        assert list(tmp_path.rglob("*.tmp")) == []

    def test_compartilhado_entre_instancias(self, tmp_path):
        caminho = tmp_path / "hashes.json"
        JsonHashStore(caminho).registrar("h1", "a.pdf")
        assert JsonHashStore(caminho).canonico("h1") == "a.pdf"


class TestServicos:
    def test_documentos_apontam_para_ticker(self, tmp_path):
        servico = deduplicacao_documentos(tmp_path, "ALZR11")
        assert servico._registry.path == caminho_hashes_documentos(
            tmp_path, "ALZR11"
        )

    def test_noticias_apontam_para_global(self, tmp_path):
        servico = deduplicacao_noticias(tmp_path)
        assert servico._registry.path == caminho_hashes_noticias(tmp_path)


class TestHashDeCaminho:
    def test_encontra_hash_do_caminho_relativo(self, tmp_path):
        JsonHashStore(
            caminho_hashes_documentos(tmp_path, "ALZR11")
        ).registrar("abc123", "documentos-relevantes/ALZR11/2026/08/relatorio/10.pdf")
        assert (
            hash_de_caminho(
                tmp_path,
                "ALZR11",
                "documentos-relevantes/ALZR11/2026/08/relatorio/10.pdf",
            )
            == "abc123"
        )

    def test_sem_registro_retorna_none(self, tmp_path):
        assert hash_de_caminho(tmp_path, "ALZR11", "x/y.pdf") is None
