"""Testes da extração de texto de pré-visualização (camada de aplicação)."""

from pathlib import Path

from flowscope.application import document_preview
from flowscope.application.document_preview import (
    SELETOR_CONTEUDO_DETALHE,
    SEM_TEXTO,
    tem_texto,
    texto_de_html,
    texto_de_pdf,
    texto_preview,
)


class TestPreview:
    def test_texto_de_html(self):
        assert "Título" in texto_de_html("<html><body><h1>Título</h1></body></html>")

    def test_texto_de_html_vazio(self):
        assert texto_de_html("") == ""

    def test_texto_de_html_com_seletor_isola_conteudo(self):
        html = (
            "<html><body>"
            "<div id='topo'>Moldura da pagina</div>"
            "<pre id='conteudoDetalhe'>Corpo do artigo</pre>"
            "<footer>Rodape</footer>"
            "</body></html>"
        )
        texto = texto_de_html(html, SELETOR_CONTEUDO_DETALHE)
        assert texto == "Corpo do artigo"
        assert "Moldura" not in texto
        assert "Rodape" not in texto

    def test_texto_de_html_seletor_ausente_usa_pagina(self):
        texto = texto_de_html(
            "<html><body><h1>Titulo</h1></body></html>",
            SELETOR_CONTEUDO_DETALHE,
        )
        assert "Titulo" in texto

    def test_texto_de_pdf_invalido_retorna_vazio(self):
        assert texto_de_pdf(b"nao e pdf") == ""

    def test_texto_preview_html(self):
        assert texto_preview(Path("doc.html")) == ""

    def test_texto_preview_despacha_pdf(self, tmp_path, monkeypatch):
        caminho = tmp_path / "doc.pdf"
        caminho.write_bytes(b"%PDF-1.4")
        monkeypatch.setattr(
            document_preview, "texto_de_pdf", lambda _dados: "texto do pdf"
        )
        assert texto_preview(caminho) == "texto do pdf"

    def test_texto_preview_extensao_desconhecida(self, tmp_path):
        caminho = tmp_path / "doc.txt"
        caminho.write_text("x", encoding="utf-8")
        assert texto_preview(caminho) == ""

    def test_tem_texto_vazio(self):
        assert tem_texto("") is False

    def test_tem_texto_apenas_espacos(self):
        assert tem_texto("   \n\t ") is False

    def test_tem_texto_marcador(self):
        assert tem_texto(SEM_TEXTO) is False

    def test_tem_texto_com_conteudo(self):
        assert tem_texto("conteudo do documento") is True
