"""Testes headless do fluxo de texto/resumo dos documentos (mixin).

Exercitam ``preparar_texto``/``_texto_cacheado`` sem instanciar Tk: o cache de
texto, a conversão em caso de *miss* e a gravação do marcador de ausência.
"""

from pathlib import Path

from flowscope.application.document_preview import SEM_TEXTO
from flowscope.domain.documents import DocumentoArquivo
from flowscope.presentation.gui.charts.document_flow_mixin import DocumentFlowMixin


def _arquivo() -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=2,
        categoria="Aviso aos Acionistas",
        nome="10.pdf",
        tipo="pdf",
        caminho=Path("/tmp/10.pdf"),
    )


class _SummaryFake:
    def chave(self, arquivo: DocumentoArquivo) -> str:
        return f"{arquivo.ticker}/{arquivo.nome}"


class _StoreFake:
    def __init__(self) -> None:
        self.dados: dict[tuple[str, str], str] = {}
        self.salvos: list[tuple[str, str, str]] = []

    def obter(self, ticker: str, chave: str) -> str | None:
        return self.dados.get((ticker, chave))

    def salvar(self, ticker: str, chave: str, texto: str) -> None:
        self.dados[(ticker, chave)] = texto
        self.salvos.append((ticker, chave, texto))


class _FlowHost(DocumentFlowMixin):
    """Host headless que substitui a extração do arquivo por um fake."""

    def __init__(self, store: _StoreFake, texto_convertido: str = "extraído") -> None:
        self._text_store = store
        self._summary = _SummaryFake()
        self._preview_cache: dict[Path, str] = {}
        self._texto_convertido = texto_convertido
        self.chamadas: list[Path] = []

    def _texto_do_arquivo(self, arquivo: DocumentoArquivo) -> str:
        self.chamadas.append(arquivo.caminho)
        return self._texto_convertido


class TestPrepararTexto:
    def test_miss_converte_e_grava_no_cache(self):
        store = _StoreFake()
        host = _FlowHost(store)
        arquivo = _arquivo()

        assert host.preparar_texto(arquivo) == "extraído"
        assert host.chamadas == [arquivo.caminho]
        assert store.obter("ALZR11", "ALZR11/10.pdf") == "extraído"
        assert host._preview_cache[arquivo.caminho] == "extraído"

    def test_miss_sem_texto_grava_marcador(self):
        store = _StoreFake()
        host = _FlowHost(store, texto_convertido="")
        arquivo = _arquivo()

        assert host.preparar_texto(arquivo) == ""
        assert store.obter("ALZR11", "ALZR11/10.pdf") == SEM_TEXTO

    def test_hit_usa_cache_sem_converter(self):
        store = _StoreFake()
        store.salvar("ALZR11", "ALZR11/10.pdf", "do cache")
        host = _FlowHost(store)
        arquivo = _arquivo()

        assert host.preparar_texto(arquivo) == "do cache"
        assert host.chamadas == []

    def test_marcador_em_cache_nao_reconverte(self):
        store = _StoreFake()
        store.salvar("ALZR11", "ALZR11/10.pdf", SEM_TEXTO)
        store.salvos.clear()
        host = _FlowHost(store)
        arquivo = _arquivo()

        assert host.preparar_texto(arquivo) == SEM_TEXTO
        assert host.chamadas == []
        assert store.salvos == []
