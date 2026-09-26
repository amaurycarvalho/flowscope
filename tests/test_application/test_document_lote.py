"""Testes do gancho de persistência do resumo em lote."""

from pathlib import Path

from flowscope.application.documentos.lote import gerar_resumo_do_lote
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo


def _arquivo() -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=2,
        categoria="Aviso aos Acionistas",
        nome="10.pdf",
        tipo="pdf",
        caminho=Path("/cache/10.pdf"),
    )


class _PainelFake:
    def __init__(self, persistir: bool) -> None:
        self._persistir = persistir
        self.persistidos: list[str] = []
        self.gerados: list[str] = []

    def persistir_no_lote(self) -> bool:
        return self._persistir

    def gerar_e_persistir(self, arquivo, texto):
        self.persistidos.append(arquivo.nome)
        return ResumoDocumento("c", "l")

    def gerar_resumo_estrito(self, arquivo, texto):
        self.gerados.append(arquivo.nome)
        return ResumoDocumento("c", "l")


class TestGerarResumoDoLote:
    def test_painel_persistente_grava_no_worker(self):
        painel = _PainelFake(persistir=True)
        gerar_resumo_do_lote(painel, _arquivo(), "texto")
        assert painel.persistidos == ["10.pdf"]
        assert painel.gerados == []

    def test_painel_nao_persistente_apenas_gera(self):
        painel = _PainelFake(persistir=False)
        gerar_resumo_do_lote(painel, _arquivo(), "texto")
        assert painel.gerados == ["10.pdf"]
        assert painel.persistidos == []
