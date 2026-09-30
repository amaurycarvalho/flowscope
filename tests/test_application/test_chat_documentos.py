"""Testes do ramo ``/documentos`` da árvore de conhecimento do chat."""

from flowscope.application.chat.documentos import FonteDocumentos
from flowscope.application.documentos.catalogo import chave_documento
from flowscope.infrastructure.document_catalog import DocumentCatalog


def _catalogo(tmp_path, ticker="PETR4") -> tuple[DocumentCatalog, str]:
    """Cria um informe mensal HTML em cache e devolve catálogo e chave."""
    pasta = tmp_path / "informe-mensal" / ticker / "2026" / "07"
    pasta.mkdir(parents=True)
    arquivo = pasta / "1.html"
    arquivo.write_text(
        "<html><body><p>conteudo integral do informe</p></body></html>",
        encoding="utf-8",
    )
    return DocumentCatalog(cache_dir=tmp_path), chave_documento(arquivo, tmp_path)


class TestFonteDocumentos:
    def test_tickers_em_cache(self, tmp_path) -> None:
        catalogo, _ = _catalogo(tmp_path)
        ramo = FonteDocumentos(catalog=catalogo).construir()
        assert ramo.caminho == "/documentos"
        caminhos = {no.caminho for no in ramo.filhos}
        assert "/documentos/tickers" in caminhos

    def test_resumos_viram_nos(self, tmp_path) -> None:
        catalogo, chave = _catalogo(tmp_path)
        catalogo.summary_store.salvar("PETR4", chave, "curto", "longo")
        ramo = FonteDocumentos(catalog=catalogo).construir()
        caminhos = _caminhos(ramo)
        assert "/documentos/PETR4/curto" in caminhos
        assert "/documentos/PETR4/longo" in caminhos

    def test_texto_em_cache_vira_no(self, tmp_path) -> None:
        catalogo, chave = _catalogo(tmp_path)
        catalogo.text_store.salvar("PETR4", chave, "texto integral")
        ramo = FonteDocumentos(catalog=catalogo).construir()
        texto = _no(ramo, "/documentos/PETR4/texto")
        assert texto is not None
        assert texto.campo_pesado == "texto"

    def test_ticker_tem_no_interno(self, tmp_path) -> None:
        catalogo, chave = _catalogo(tmp_path)
        catalogo.summary_store.salvar("PETR4", chave, "curto", "longo")
        ramo = FonteDocumentos(catalog=catalogo).construir()
        ticker = _no(ramo, "/documentos/PETR4")
        assert ticker is not None and not ticker.folha
        assert {n.nome for n in ticker.filhos} == {"curto", "longo"}

    def test_ticker_sem_conteudo_nao_e_listado(self, tmp_path) -> None:
        catalogo, _ = _catalogo(tmp_path)
        ramo = FonteDocumentos(catalog=catalogo).construir()
        assert "/documentos/PETR4" not in _caminhos(ramo)
        assert "/documentos/tickers/PETR4" not in _caminhos(ramo)

    def test_pendente_omitido(self, tmp_path) -> None:
        catalogo, _ = _catalogo(tmp_path)
        ramo = FonteDocumentos(catalog=catalogo).construir()
        caminhos = _caminhos(ramo)
        assert "/documentos/PETR4/curto" not in caminhos
        assert "/documentos/PETR4/texto" not in caminhos

    def test_sem_catalogo(self) -> None:
        ramo = FonteDocumentos(catalog=None).construir()
        assert ramo.caminho == "/documentos"


def _caminhos(raiz) -> set[str]:
    return {no.caminho for no in _percorrer(raiz)}


def _no(raiz, caminho: str):
    return next((no for no in _percorrer(raiz) if no.caminho == caminho), None)


def _percorrer(no):
    yield no
    for filho in no.filhos:
        yield from _percorrer(filho)
