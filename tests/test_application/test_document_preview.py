"""Testes da extração de texto de pré-visualização (camada de aplicação)."""

import base64
from io import BytesIO
from pathlib import Path

import pypdf

from flowscope.application import document_preview
from flowscope.application.document_preview import (
    SELETOR_CONTEUDO_DETALHE,
    SEM_TEXTO,
    ExtracaoTexto,
    StatusExtracao,
    extrair_pdf,
    tem_texto,
    texto_de_html,
    texto_de_pdf,
    texto_preview,
)

_FIXTURE_PDF = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "b3"
    / "bdr_aviso_exxo.pdf.b64"
)


def _pdf_com_texto() -> bytes:
    return base64.b64decode(_FIXTURE_PDF.read_text(encoding="ascii"))


def _pdf_cifrado(senha: str) -> bytes:
    leitor = pypdf.PdfReader(BytesIO(_pdf_com_texto()))
    escritor = pypdf.PdfWriter()
    for pagina in leitor.pages:
        escritor.add_page(pagina)
    escritor.encrypt(senha)
    buffer = BytesIO()
    escritor.write(buffer)
    return buffer.getvalue()


class _PaginaFake:
    def __init__(self, texto="", erro=False):
        self._texto = texto
        self._erro = erro

    def extract_text(self):
        if self._erro:
            raise RuntimeError("página ilegível")
        return self._texto


class _LeitorFake:
    is_encrypted = False

    def __init__(self, _dados):
        self.pages = [
            _PaginaFake("página boa"),
            _PaginaFake(erro=True),
        ]


class _LeitorVazio:
    is_encrypted = False

    def __init__(self, _dados):
        self.pages = [_PaginaFake("")]


class _LeitorTudoErro:
    is_encrypted = False

    def __init__(self, _dados):
        self.pages = [_PaginaFake(erro=True), _PaginaFake(erro=True)]


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
            document_preview,
            "extrair_pdf",
            lambda _dados, senha=None: ExtracaoTexto("texto do pdf", StatusExtracao.OK),
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


class TestExtracaoPdf:
    def test_pdf_com_texto_completo(self):
        resultado = extrair_pdf(_pdf_com_texto())
        assert resultado.status is StatusExtracao.OK
        assert resultado.paginas_com_falha == 0
        assert resultado.texto.strip()

    def test_pdf_invalido_e_falha(self):
        resultado = extrair_pdf(b"nao e pdf")
        assert resultado.status is StatusExtracao.FALHA
        assert resultado.texto == ""

    def test_pdf_vazio_nao_tem_texto(self):
        assert extrair_pdf(b"").status is StatusExtracao.SEM_TEXTO

    def test_pagina_ilegivel_preserva_as_demais(self, monkeypatch):
        monkeypatch.setattr(pypdf, "PdfReader", _LeitorFake)
        resultado = extrair_pdf(b"%PDF-1.4")
        assert resultado.status is StatusExtracao.PARCIAL
        assert resultado.paginas_com_falha == 1
        assert "página boa" in resultado.texto

    def test_todas_as_paginas_falham(self, monkeypatch):
        monkeypatch.setattr(pypdf, "PdfReader", _LeitorTudoErro)
        assert extrair_pdf(b"%PDF-1.4").status is StatusExtracao.FALHA

    def test_leitor_sem_texto(self, monkeypatch):
        monkeypatch.setattr(pypdf, "PdfReader", _LeitorVazio)
        assert extrair_pdf(b"%PDF-1.4").status is StatusExtracao.SEM_TEXTO

    def test_cifrado_com_senha_correta_extrai(self):
        dados = _pdf_cifrado("segredo")
        resultado = extrair_pdf(dados, "segredo")
        assert resultado.status is StatusExtracao.OK

    def test_cifrado_sem_senha_fica_protegido(self):
        dados = _pdf_cifrado("segredo")
        assert extrair_pdf(dados).status is StatusExtracao.PROTEGIDO

    def test_cifrado_com_senha_errada_fica_protegido(self):
        dados = _pdf_cifrado("segredo")
        assert extrair_pdf(dados, "errada").status is StatusExtracao.PROTEGIDO
