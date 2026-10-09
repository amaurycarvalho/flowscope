"""Testes do ramo ``/documentos`` da árvore de conhecimento do chat."""

from flowscope.application.chat.arvore import ArvoreConhecimento, LIMITE_PAGINA_PADRAO
from flowscope.application.chat.documentos import (
    FonteDocumentos,
    chave_curta_documento,
)
from flowscope.application.documentos.catalogo import chave_documento
from flowscope.infrastructure.document_catalog import DocumentCatalog


def _adicionar(
    tmp_path, ticker: str, ano: int, mes: int, nome: str = "1.html"
) -> str:
    """Cria um arquivo de informe mensal e devolve a sua chave relativa."""
    pasta = tmp_path / "informe-mensal" / ticker / str(ano) / f"{mes:02d}"
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / nome
    arquivo.write_text(
        "<html><body><p>conteudo integral do informe</p></body></html>",
        encoding="utf-8",
    )
    return chave_documento(arquivo, tmp_path)


def _catalogo_com(tmp_path, ticker="PETR4") -> tuple[DocumentCatalog, str]:
    """Cria o catálogo com um documento e devolve catálogo e chave."""
    chave = _adicionar(tmp_path, ticker, 2026, 7)
    return DocumentCatalog(cache_dir=tmp_path), chave


class TestFonteDocumentos:
    def test_tickers_em_cache(self, tmp_path) -> None:
        catalogo, _ = _catalogo_com(tmp_path)
        ramo = FonteDocumentos(catalog=catalogo).construir()
        assert ramo.caminho == "/documentos"
        caminhos = {no.caminho for no in ramo.filhos}
        assert "/documentos/tickers" in caminhos

    def test_indice_do_ticker(self, tmp_path) -> None:
        catalogo, chave = _catalogo_com(tmp_path)
        catalogo.summary_store.salvar("PETR4", chave, "curto", "longo")
        ramo = FonteDocumentos(catalog=catalogo).construir()
        assert "/documentos/PETR4/indice" in _caminhos(ramo)

    def test_documento_tem_folhas(self, tmp_path) -> None:
        catalogo, chave = _catalogo_com(tmp_path)
        catalogo.summary_store.salvar("PETR4", chave, "curto", "longo")
        catalogo.text_store.salvar("PETR4", chave, "texto integral")
        ramo = FonteDocumentos(catalog=catalogo).construir()
        doc = _no(ramo, f"/documentos/PETR4/{chave_curta_documento(chave)}")
        assert doc is not None and not doc.folha
        assert {n.nome for n in doc.filhos} == {"curto", "longo", "texto"}
        rotulos = {n.nome: n.metadado for n in doc.filhos}
        assert rotulos["curto"] == "resumo curto"
        assert rotulos["longo"] == "resumo longo"
        assert rotulos["texto"] == "texto integral"

    def test_texto_do_documento_sob_demanda(self, tmp_path) -> None:
        catalogo, chave = _catalogo_com(tmp_path)
        catalogo.text_store.salvar("PETR4", chave, "texto integral")
        ramo = FonteDocumentos(catalog=catalogo).construir()
        texto = _no(
            ramo, f"/documentos/PETR4/{chave_curta_documento(chave)}/texto"
        )
        assert texto is not None
        assert texto.campo_pesado == "texto"

    def test_documento_sem_resumo_omite_folhas(self, tmp_path) -> None:
        catalogo, chave = _catalogo_com(tmp_path)
        catalogo.text_store.salvar("PETR4", chave, "texto integral")
        ramo = FonteDocumentos(catalog=catalogo).construir()
        doc = _no(ramo, f"/documentos/PETR4/{chave_curta_documento(chave)}")
        assert doc is not None
        assert {n.nome for n in doc.filhos} == {"texto"}

    def test_texto_e_do_documento(self, tmp_path) -> None:
        catalogo, chave_jul = _catalogo_com(tmp_path)
        chave_ago = _adicionar(tmp_path, "PETR4", 2026, 8)
        catalogo.text_store.salvar("PETR4", chave_jul, "TEXTO_JULHO")
        catalogo.text_store.salvar("PETR4", chave_ago, "TEXTO_AGOSTO")
        arvore = ArvoreConhecimento(
            FonteDocumentos(catalog=catalogo).construir()
        )
        julho = arvore.obter(
            f"/documentos/PETR4/{chave_curta_documento(chave_jul)}/texto"
        )
        agosto = arvore.obter(
            f"/documentos/PETR4/{chave_curta_documento(chave_ago)}/texto"
        )
        assert julho["texto"] == "TEXTO_JULHO"
        assert agosto["texto"] == "TEXTO_AGOSTO"

    def test_pagina_padrao_sem_campos(self, tmp_path) -> None:
        catalogo, chave = _catalogo_com(tmp_path)
        catalogo.text_store.salvar("PETR4", chave, "texto curto")
        arvore = ArvoreConhecimento(FonteDocumentos(catalog=catalogo).construir())
        caminho = f"/documentos/PETR4/{chave_curta_documento(chave)}/texto"
        pagina = arvore.obter(caminho)
        assert pagina["texto"] == "texto curto"
        assert pagina["total"] == len("texto curto")
        assert pagina["offset"] == 0
        assert pagina["limite"] == LIMITE_PAGINA_PADRAO
        assert pagina["continua"] is False

    def test_pagina_por_offset_e_limite(self, tmp_path) -> None:
        catalogo, chave = _catalogo_com(tmp_path)
        texto = "0123456789" * 10
        catalogo.text_store.salvar("PETR4", chave, texto)
        arvore = ArvoreConhecimento(FonteDocumentos(catalog=catalogo).construir())
        caminho = f"/documentos/PETR4/{chave_curta_documento(chave)}/texto"
        pagina = arvore.obter(caminho, offset=10, limite=20)
        assert pagina["texto"] == texto[10:30]
        assert pagina["total"] == len(texto)
        assert pagina["offset"] == 10
        assert pagina["limite"] == 20
        assert pagina["continua"] is True
        ultima = arvore.obter(caminho, offset=90, limite=20)
        assert ultima["texto"] == texto[90:]
        assert ultima["continua"] is False

    def test_offset_alem_do_fim_devolve_vazio(self, tmp_path) -> None:
        catalogo, chave = _catalogo_com(tmp_path)
        catalogo.text_store.salvar("PETR4", chave, "texto")
        arvore = ArvoreConhecimento(FonteDocumentos(catalog=catalogo).construir())
        caminho = f"/documentos/PETR4/{chave_curta_documento(chave)}/texto"
        pagina = arvore.obter(caminho, offset=500, limite=10)
        assert pagina["texto"] == ""
        assert pagina["continua"] is False

    def test_indice_mais_recente_primeiro(self, tmp_path) -> None:
        catalogo, chave_jul = _catalogo_com(tmp_path)
        chave_ago = _adicionar(tmp_path, "PETR4", 2026, 8)
        catalogo.summary_store.salvar("PETR4", chave_jul, "c", "l")
        catalogo.summary_store.salvar("PETR4", chave_ago, "c", "l")
        ramo = FonteDocumentos(catalog=catalogo).construir()
        indice = _conteudo(ramo, "/documentos/PETR4/indice")
        assert indice.splitlines()[0].startswith("2026/08")

    def test_metadados_do_documento(self, tmp_path) -> None:
        catalogo, chave = _catalogo_com(tmp_path)
        catalogo.summary_store.salvar("PETR4", chave, "c", "l")
        ramo = FonteDocumentos(catalog=catalogo).construir()
        doc = _no(ramo, f"/documentos/PETR4/{chave_curta_documento(chave)}")
        assert doc is not None
        assert "Informe Mensal" in doc.metadado
        assert doc.campos["categoria"] == "Informe Mensal"
        assert doc.campos["periodo"] == "2026/07"
        assert doc.campos["nome"] == "1.html"

    def test_indice_traz_trecho_e_marca_rg(self, tmp_path) -> None:
        catalogo, chave = _catalogo_com(tmp_path)
        catalogo.summary_store.salvar(
            "PETR4", chave, "Resumo curto sobre o PL.", "longo"
        )
        ramo = FonteDocumentos(
            catalog=catalogo, rg_chaves=lambda _t: {chave}
        ).construir()
        linha = _conteudo(ramo, "/documentos/PETR4/indice").splitlines()[0]
        assert "RG mensal" in linha
        assert "prévia:" in linha
        assert "Resumo curto sobre o PL." in linha

    def test_indice_marca_nao_rg_como_documento(self, tmp_path) -> None:
        catalogo, chave = _catalogo_com(tmp_path)
        catalogo.summary_store.salvar("PETR4", chave, "c", "l")
        ramo = FonteDocumentos(catalog=catalogo).construir()
        linha = _conteudo(ramo, "/documentos/PETR4/indice").splitlines()[0]
        assert "documento" in linha
        assert "RG mensal" not in linha

    def test_indice_sinaliza_duplicados_no_mes(self, tmp_path) -> None:
        catalogo, chave_1 = _catalogo_com(tmp_path)
        chave_2 = _adicionar(tmp_path, "PETR4", 2026, 7, "2.html")
        catalogo.summary_store.salvar("PETR4", chave_1, "c", "l")
        catalogo.summary_store.salvar("PETR4", chave_2, "c", "l")
        ramo = FonteDocumentos(catalog=catalogo).construir()
        indice = _conteudo(ramo, "/documentos/PETR4/indice")
        assert "1/2" in indice and "2/2" in indice

    def test_ticker_sem_conteudo_nao_e_listado(self, tmp_path) -> None:
        catalogo, _ = _catalogo_com(tmp_path)
        ramo = FonteDocumentos(catalog=catalogo).construir()
        assert "/documentos/PETR4" not in _caminhos(ramo)
        assert "/documentos/tickers/PETR4" not in _caminhos(ramo)

    def test_pendente_omitido(self, tmp_path) -> None:
        catalogo, _ = _catalogo_com(tmp_path)
        ramo = FonteDocumentos(catalog=catalogo).construir()
        assert "/documentos/PETR4/indice" not in _caminhos(ramo)

    def test_sem_catalogo(self) -> None:
        ramo = FonteDocumentos(catalog=None).construir()
        assert ramo.caminho == "/documentos"


def _caminhos(raiz) -> set[str]:
    return {no.caminho for no in _percorrer(raiz)}


def _no(raiz, caminho: str):
    return next((no for no in _percorrer(raiz) if no.caminho == caminho), None)


def _conteudo(raiz, caminho: str) -> str:
    no = _no(raiz, caminho)
    assert no is not None
    return no.conteudo


def _percorrer(no):
    yield no
    for filho in no.filhos:
        yield from _percorrer(filho)
