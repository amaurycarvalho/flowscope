"""Testes do store de texto extraído de documentos em JSON por ticker."""

import json
from pathlib import Path

from flowscope.infrastructure.document_summaries import chave_documento
from flowscope.infrastructure.document_texts import JsonDocumentTextStore

CHAVE_A = "bdr/ALZR11/2026/02/10.pdf"
CHAVE_B = "informe-mensal/ALZR11/2026/02/20.html"


class TestRoundTrip:
    def test_salva_e_recupera_por_documento(self, tmp_path):
        store = JsonDocumentTextStore(cache_dir=tmp_path)
        store.salvar("ALZR11", CHAVE_A, "texto do documento")
        assert store.obter("ALZR11", CHAVE_A) == "texto do documento"
        assert store.textos("ALZR11") == {CHAVE_A: "texto do documento"}

    def test_arquivo_fica_no_subdiretorio_do_ticker(self, tmp_path):
        store = JsonDocumentTextStore(cache_dir=tmp_path)
        store.salvar("alzr11", CHAVE_A, "texto")
        assert (tmp_path / "document-texts" / "ALZR11.json").exists()


class TestTolerancia:
    def test_arquivo_ausente_retorna_vazio(self, tmp_path):
        store = JsonDocumentTextStore(cache_dir=tmp_path)
        assert store.textos("ALZR11") == {}
        assert store.obter("ALZR11", CHAVE_A) is None

    def test_json_corrompido_retorna_vazio(self, tmp_path):
        pasta = tmp_path / "document-texts"
        pasta.mkdir(parents=True)
        (pasta / "ALZR11.json").write_text("{nao e json", encoding="utf-8")
        store = JsonDocumentTextStore(cache_dir=tmp_path)
        assert store.textos("ALZR11") == {}

    def test_payload_sem_textos_retorna_vazio(self, tmp_path):
        pasta = tmp_path / "document-texts"
        pasta.mkdir(parents=True)
        (pasta / "ALZR11.json").write_text(
            json.dumps({"schema_version": 1}), encoding="utf-8"
        )
        store = JsonDocumentTextStore(cache_dir=tmp_path)
        assert store.textos("ALZR11") == {}

    def test_valor_nao_string_e_ignorado(self, tmp_path):
        pasta = tmp_path / "document-texts"
        pasta.mkdir(parents=True)
        (pasta / "ALZR11.json").write_text(
            json.dumps({"textos": {CHAVE_A: 42}}), encoding="utf-8"
        )
        store = JsonDocumentTextStore(cache_dir=tmp_path)
        assert store.textos("ALZR11") == {}


class TestPreservacao:
    def test_salvar_um_documento_preserva_os_demais(self, tmp_path):
        store = JsonDocumentTextStore(cache_dir=tmp_path)
        store.salvar("ALZR11", CHAVE_A, "texto A")
        store.salvar("ALZR11", CHAVE_B, "texto B")
        textos = store.textos("ALZR11")
        assert textos[CHAVE_A] == "texto A"
        assert textos[CHAVE_B] == "texto B"

    def test_sobrescrever_texto_existente(self, tmp_path):
        store = JsonDocumentTextStore(cache_dir=tmp_path)
        store.salvar("ALZR11", CHAVE_A, "antigo")
        store.salvar("ALZR11", CHAVE_A, "novo")
        assert store.obter("ALZR11", CHAVE_A) == "novo"


class TestChaveCompartilhadaComResumos:
    def test_chave_do_texto_coincide_com_a_dos_resumos(self, tmp_path):
        base = tmp_path
        caminho = base / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf"
        chave = chave_documento(caminho, base)
        store = JsonDocumentTextStore(cache_dir=base)
        store.salvar("ALZR11", chave, "texto")
        assert store.obter("ALZR11", CHAVE_A) == "texto"

    def test_caminho_fora_da_base_usa_nome(self, tmp_path):
        assert chave_documento(Path("/outro/10.pdf"), tmp_path) == "10.pdf"
