"""Testes do registro de URLs baixadas com sucesso por escopo."""

import json
from pathlib import Path

from flowscope.infrastructure.url_downloads import (
    DIRETORIO_URLS,
    JsonUrlStore,
    _CARACTERES_INSEGUROS,
    caminho_urls_documentos,
    caminho_urls_noticias,
    normalizar_url,
    url_store_documentos,
    url_store_noticias,
)


class TestCaminhos:
    def test_documentos_por_ticker(self):
        caminho = caminho_urls_documentos("/base", "alzr11")
        assert caminho == Path("/base", DIRETORIO_URLS, "ALZR11.json")

    def test_documentos_sanitiza_ticker(self):
        caminho = caminho_urls_documentos("/base", "../x")
        assert _CARACTERES_INSEGUROS.search(caminho.name) is None

    def test_noticias_global(self):
        caminho = caminho_urls_noticias("/base")
        assert caminho.parts[-2:] == ("noticias", "url-downloads.json")

    def test_factories_apontam_para_o_escopo(self, tmp_path):
        assert url_store_documentos(tmp_path, "ALZR11").path == (
            caminho_urls_documentos(tmp_path, "ALZR11")
        )
        assert url_store_noticias(tmp_path).path == caminho_urls_noticias(
            tmp_path
        )


class TestNormalizacao:
    def test_espacos_sao_descartados(self):
        assert normalizar_url("  https://x/1  ") == "https://x/1"

    def test_vazio(self):
        assert normalizar_url("") == ""


class TestJsonUrlStore:
    def test_round_trip(self, tmp_path):
        store = JsonUrlStore(tmp_path / "urls.json")
        assert store.registrados() == {}
        store.registrar("https://x/1", "noticias/2026/09/a.html")
        store.registrar("https://x/2", "noticias/2026/09/b.html")
        assert store.canonico("https://x/1") == "noticias/2026/09/a.html"
        assert store.canonico("https://x/2") == "noticias/2026/09/b.html"
        recarregado = JsonUrlStore(tmp_path / "urls.json")
        assert recarregado.registrados() == {
            "https://x/1": "noticias/2026/09/a.html",
            "https://x/2": "noticias/2026/09/b.html",
        }

    def test_registrar_normaliza_a_chave(self, tmp_path):
        store = JsonUrlStore(tmp_path / "urls.json")
        store.registrar("  https://x/1 ", "a.html")
        assert store.canonico("https://x/1") == "a.html"
        assert store.canonico("  https://x/1  ") == "a.html"

    def test_registrar_url_vazia_nao_grava(self, tmp_path):
        caminho = tmp_path / "urls.json"
        store = JsonUrlStore(caminho)
        store.registrar("   ", "a.html")
        assert not caminho.exists()
        assert store.registrados() == {}

    def test_arquivo_ausente(self, tmp_path):
        store = JsonUrlStore(tmp_path / "nao_existe.json")
        assert store.registrados() == {}
        assert store.canonico("https://x/1") is None

    def test_arquivo_corrompido(self, tmp_path):
        caminho = tmp_path / "urls.json"
        caminho.write_text("{invalido", encoding="utf-8")
        assert JsonUrlStore(caminho).registrados() == {}

    def test_formato_invalido_e_tolerado(self, tmp_path):
        caminho = tmp_path / "urls.json"
        caminho.write_text(json.dumps({"urls": ["x"]}), encoding="utf-8")
        assert JsonUrlStore(caminho).registrados() == {}

    def test_remover(self, tmp_path):
        store = JsonUrlStore(tmp_path / "urls.json")
        store.registrar("https://x/1", "a.html")
        store.registrar("https://x/2", "b.html")
        store.remover("https://x/1")
        assert store.registrados() == {"https://x/2": "b.html"}

    def test_remover_inexistente_nao_grava(self, tmp_path):
        caminho = tmp_path / "urls.json"
        store = JsonUrlStore(caminho)
        store.remover("https://x/1")
        assert not caminho.exists()

    def test_remover_relativo_preserva_as_demais(self, tmp_path):
        store = JsonUrlStore(tmp_path / "urls.json")
        store.registrar("https://x/1", "a.html")
        store.registrar("https://x/2", "b.html")
        store.registrar("https://x/3", "a.html")
        store.remover_relativo("a.html")
        assert store.registrados() == {"https://x/2": "b.html"}

    def test_nao_deixa_temporario(self, tmp_path):
        store = JsonUrlStore(tmp_path / "urls.json")
        store.registrar("https://x/1", "a.html")
        assert list(tmp_path.rglob("*.tmp")) == []

    def test_compartilhado_entre_instancias(self, tmp_path):
        caminho = tmp_path / "urls.json"
        JsonUrlStore(caminho).registrar("https://x/1", "a.html")
        assert JsonUrlStore(caminho).canonico("https://x/1") == "a.html"
