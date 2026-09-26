"""Testes puros do serviço de resumo e das portas de persistência."""

from pathlib import Path

import pytest

from flowscope.application.document_text_port import DocumentTextStore
from flowscope.application.documentos.catalogo import chave_documento
from flowscope.application.documentos.document_summary import DocumentSummaryService
from flowscope.application.documentos.document_summary_port import (
    DocumentSummaryStore,
)
from flowscope.application.documentos.mensagens import mensagem_indisponivel
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.llm import LLMCommunicationError
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.infrastructure.document_texts import JsonDocumentTextStore


def _arquivo(tmp_path: Path, nome: str = "10.pdf") -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=2,
        categoria="Aviso aos Acionistas",
        nome=nome,
        tipo="pdf",
        caminho=tmp_path / nome,
    )


class _LLMFake:
    def __init__(self, resposta: str = "CURTO: c\nLONGO: l") -> None:
        self.resposta = resposta

    def complete(self, messages, system_prompt=None):
        return self.resposta


class TestGerarEstrito:
    def _servico(self, tmp_path, llm):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        return DocumentSummaryService(
            store, tmp_path, llm_factory=lambda: llm, llm_available=lambda: True
        )

    def test_propaga_llm_error(self, tmp_path):
        class _Falha:
            def complete(self, messages, system_prompt=None):
                raise LLMCommunicationError("timeout")

        servico = self._servico(tmp_path, _Falha())
        with pytest.raises(LLMCommunicationError):
            servico.gerar_estrito(_arquivo(tmp_path), "texto")

    def test_propaga_excecao_inesperada(self, tmp_path):
        class _Falha:
            def complete(self, messages, system_prompt=None):
                raise RuntimeError("boom")

        servico = self._servico(tmp_path, _Falha())
        with pytest.raises(RuntimeError):
            servico.gerar_estrito(_arquivo(tmp_path), "texto")

    def test_gerar_continua_tolerante(self, tmp_path):
        class _Falha:
            def complete(self, messages, system_prompt=None):
                raise LLMCommunicationError("timeout")

        servico = self._servico(tmp_path, _Falha())
        assert servico.gerar(_arquivo(tmp_path), "texto") is None


class TestPersistencia:
    def _servico(self, tmp_path):
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        return store, DocumentSummaryService(
            store,
            tmp_path,
            llm_factory=lambda: _LLMFake(),
            llm_available=lambda: True,
        )

    def test_gerar_e_persistir_grava_e_devolve(self, tmp_path):
        store, servico = self._servico(tmp_path)
        arquivo = _arquivo(tmp_path)
        resumo = servico.gerar_e_persistir(arquivo, "texto")
        assert resumo is not None
        salvo = store.obter("ALZR11", chave_documento(arquivo.caminho, tmp_path))
        assert salvo.long_summary == resumo.long_summary

    def test_atualizar_nao_grava(self, tmp_path):
        store, servico = self._servico(tmp_path)
        arquivo = _arquivo(tmp_path)
        atualizado = servico.atualizar(arquivo, ResumoDocumento("c", "l"))
        assert atualizado.long_summary == "l"
        assert store.obter("ALZR11", chave_documento(arquivo.caminho, tmp_path)) is None

    def test_precisa_resumo_com_llm_e_texto(self, tmp_path):
        _store, servico = self._servico(tmp_path)
        assert servico.precisa_resumo(_arquivo(tmp_path), "texto") is True
        assert servico.precisa_resumo(_arquivo(tmp_path), "") is False


class TestMensagemIndisponibilidade:
    def test_dois_sufixos(self):
        assert mensagem_indisponivel(True) == (
            "Resumo indisponível. Clique no documento para análise."
        )
        assert mensagem_indisponivel(False) == (
            "Resumo indisponível. Configure a LLM via o botão I.A. e teste "
            "a comunicação."
        )


class TestContratoDasPortas:
    def test_summary_store_satisfaz_a_porta(self, tmp_path):
        assert isinstance(
            JsonDocumentSummaryStore(cache_dir=tmp_path), DocumentSummaryStore
        )

    def test_text_store_satisfaz_a_porta(self, tmp_path):
        assert isinstance(
            JsonDocumentTextStore(cache_dir=tmp_path), DocumentTextStore
        )
