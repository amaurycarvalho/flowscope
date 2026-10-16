"""Testes do download de PDF no visualizador da CVM."""

import base64

import requests
import responses

from flowscope.infrastructure.cvm.pdf import (
    CVM_PDF_PAGE_URL,
    CVM_PDF_URL,
    baixar_pdf_cvm,
    conteudo_e_pdf,
    decodificar_pdf,
)

_PDF = b"%PDF-1.4\nconteudo"


def _pagina(protocolo: str = "1"):
    """Registra o GET da página do visualizador (renovação de sessão)."""
    return (
        f"{CVM_PDF_PAGE_URL}?ID={protocolo}",
        {"body": "<html><body></body></html>", "status": 200},
    )


class TestBaixarPdfCvm:
    @responses.activate
    def test_pdf_valido_retorna_bytes(self):
        conteudo = base64.b64encode(_PDF).decode("ascii")
        url, kwargs = _pagina("1510187")
        responses.get(url, **kwargs)
        responses.post(CVM_PDF_URL, json={"d": conteudo}, status=200)
        assert baixar_pdf_cvm("1510187") == _PDF

    @responses.activate
    def test_conteudo_nao_pdf_retorna_none(self):
        conteudo = base64.b64encode(b"<html>erro</html>").decode("ascii")
        url, kwargs = _pagina("1")
        responses.get(url, **kwargs)
        responses.post(CVM_PDF_URL, json={"d": conteudo}, status=200)
        assert baixar_pdf_cvm("1") is None

    @responses.activate
    def test_falha_de_rede_retorna_none(self):
        url, kwargs = _pagina("1")
        responses.get(url, **kwargs)
        responses.post(CVM_PDF_URL, body=requests.ConnectionError("offline"))
        assert baixar_pdf_cvm("1") is None

    @responses.activate
    def test_502_repete_e_retorna_pdf(self):
        conteudo = base64.b64encode(_PDF).decode("ascii")
        url, kwargs = _pagina("1")
        responses.get(url, **kwargs)
        responses.get(url, **kwargs)
        responses.post(CVM_PDF_URL, status=502)
        responses.post(CVM_PDF_URL, json={"d": conteudo}, status=200)
        assert baixar_pdf_cvm("1") == _PDF
        posts = [c for c in responses.calls if c.request.method == "POST"]
        assert len(posts) == 2

    @responses.activate
    def test_403_nao_repete(self):
        url, kwargs = _pagina("1")
        responses.get(url, **kwargs)
        responses.post(CVM_PDF_URL, status=403)
        assert baixar_pdf_cvm("1") is None
        posts = [c for c in responses.calls if c.request.method == "POST"]
        assert len(posts) == 1


class TestDecodificarPdf:
    def test_payload_valido(self):
        conteudo = base64.b64encode(_PDF).decode("ascii")
        assert decodificar_pdf({"d": conteudo}) == _PDF

    def test_sem_campo_retorna_none(self):
        assert decodificar_pdf({"outro": "x"}) is None

    def test_base64_invalido_retorna_none(self):
        assert decodificar_pdf({"d": "nao-base64"}) is None


class TestConteudoEPdf:
    def test_assinatura(self):
        assert conteudo_e_pdf(b"%PDF-1.4") is True
        assert conteudo_e_pdf(b"<html>") is False
