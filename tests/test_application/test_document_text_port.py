"""Testes da porta do cache de texto extraído dos documentos."""

import flowscope.application.document_text_port as modulo
from flowscope.application.document_text_port import DocumentTextStore


class _StoreFake:
    def __init__(self):
        self._dados: dict[tuple[str, str], str] = {}

    def obter(self, ticker, chave):
        return self._dados.get((ticker, chave))

    def salvar(self, ticker, chave, texto):
        self._dados[(ticker, chave)] = texto


class TestPorta:
    def test_protocolo_expoe_leitura_e_gravacao(self):
        assert hasattr(DocumentTextStore, "obter")
        assert hasattr(DocumentTextStore, "salvar")

    def test_implementacao_satisfaz_a_porta(self):
        store: DocumentTextStore = _StoreFake()
        store.salvar("ALZR11", "bdr/ALZR11/2026/02/10.pdf", "texto")
        assert store.obter("ALZR11", "bdr/ALZR11/2026/02/10.pdf") == "texto"

    def test_modulo_nao_importa_infraestrutura(self):
        origens = {
            getattr(valor, "__module__", "")
            for valor in vars(modulo).values()
        }
        assert not any(
            origem.startswith("flowscope.infrastructure") for origem in origens
        )
