"""Testes do store de resumos de documentos em JSON por ticker."""

import json
from pathlib import Path

from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.infrastructure.document_summaries import (
    JsonDocumentSummaryStore,
    chave_documento,
)

CHAVE_A = "bdr/ALZR11/2026/02/10.pdf"
CHAVE_B = "informe-mensal/ALZR11/2026/02/20.html"


class TestRoundTrip:
    def test_salva_e_recupera_por_documento(self, tmp_path):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        store.salvar("ALZR11", CHAVE_A, "curto", "longo")
        assert store.obter("ALZR11", CHAVE_A) == ResumoDocumento("curto", "longo")
        assert store.resumos("ALZR11") == {CHAVE_A: ResumoDocumento("curto", "longo")}

    def test_arquivo_fica_no_subdiretorio_do_ticker(self, tmp_path):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        store.salvar("alzr11", CHAVE_A, "curto", "longo")
        assert (tmp_path / "document-summaries" / "ALZR11.json").exists()


class TestTolerancia:
    def test_arquivo_ausente_retorna_vazio(self, tmp_path):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        assert store.resumos("ALZR11") == {}
        assert store.obter("ALZR11", CHAVE_A) is None

    def test_json_corrompido_retorna_vazio(self, tmp_path):
        pasta = tmp_path / "document-summaries"
        pasta.mkdir(parents=True)
        (pasta / "ALZR11.json").write_text("{nao e json", encoding="utf-8")
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        assert store.resumos("ALZR11") == {}

    def test_payload_sem_resumos_retorna_vazio(self, tmp_path):
        pasta = tmp_path / "document-summaries"
        pasta.mkdir(parents=True)
        (pasta / "ALZR11.json").write_text(
            json.dumps({"schema_version": 1}), encoding="utf-8"
        )
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        assert store.resumos("ALZR11") == {}


class TestPreservacao:
    def test_salvar_um_documento_preserva_os_demais(self, tmp_path):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        store.salvar("ALZR11", CHAVE_A, "curto A", "longo A")
        store.salvar("ALZR11", CHAVE_B, "curto B", "longo B")
        resumos = store.resumos("ALZR11")
        assert resumos[CHAVE_A] == ResumoDocumento("curto A", "longo A")
        assert resumos[CHAVE_B] == ResumoDocumento("curto B", "longo B")

    def test_sobrescrever_resumo_existente(self, tmp_path):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        store.salvar("ALZR11", CHAVE_A, "antigo", "antigo")
        store.salvar("ALZR11", CHAVE_A, "novo", "novo")
        assert store.obter("ALZR11", CHAVE_A) == ResumoDocumento("novo", "novo")


class TestChaveDocumento:
    def test_caminho_relativo_estavel(self, tmp_path):
        base = tmp_path
        caminho = base / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf"
        assert chave_documento(caminho, base) == "bdr/ALZR11/2026/02/10.pdf"

    def test_caminho_fora_da_base_usa_nome(self, tmp_path):
        assert chave_documento(Path("/outro/10.pdf"), tmp_path) == "10.pdf"
