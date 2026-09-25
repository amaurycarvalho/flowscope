"""Testes do download do documento vinculado às notícias "Geral"."""

import base64
import json

import responses

from flowscope.infrastructure.b3 import noticias_vinculo
from flowscope.infrastructure.b3.noticias_vinculo import (
    baixar_conteudo_vinculado,
    extrair_url_vinculada,
)

_VIEWER_URL = (
    "https://www.rad.cvm.gov.br/ENETWEB/frmExibirArquivoIPEExterno.aspx"
    "?ID=1570300&flnk"
)
_POST_URL = (
    "https://www.rad.cvm.gov.br/ENETWEB/frmExibirArquivoIPEExterno.aspx/ExibirPDF"
)
_CORPO = (
    "VALE (VALE-NM) - Esclarecimentos de questionamentos CVM/B3- 22/09/26\n\n"
    f"{_VIEWER_URL}\n\n(R) = Reapresentacao"
)


def _viewer(captcha: str = "N") -> str:
    return (
        "<html><body>"
        f'<input type="hidden" id="hdnHabilitaCaptcha" value="{captcha}">'
        '<iframe id="pdfViewer"></iframe>'
        "</body></html>"
    )


def _pdf_b64() -> str:
    return base64.b64encode(b"%PDF-1.7\nconteudo").decode()


class TestExtrairUrl:
    def test_encontra_url_cvm(self):
        assert extrair_url_vinculada(_CORPO) == _VIEWER_URL

    def test_ignora_url_nao_suportada(self):
        assert extrair_url_vinculada("veja https://exemplo.com/doc.pdf") is None

    def test_sem_url(self):
        assert extrair_url_vinculada("texto simples") is None

    def test_texto_vazio(self):
        assert extrair_url_vinculada("") is None


class TestBaixarConteudoVinculado:
    def test_baixa_e_extrai_o_pdf(self, monkeypatch):
        monkeypatch.setattr(
            noticias_vinculo,
            "extrair_texto_pdf",
            lambda _dados: "texto do documento",
        )
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, _VIEWER_URL, body=_viewer("N"), status=200)
            rsps.add(
                responses.POST,
                _POST_URL,
                body=json.dumps({"d": _pdf_b64()}),
                status=200,
            )
            resultado = baixar_conteudo_vinculado(_CORPO)
        assert resultado == "texto do documento"

    def test_envia_o_payload_do_webmethod(self):
        capturado: list = []

        def _post_cb(request):
            capturado.append(json.loads(request.body))
            return (200, {}, json.dumps({"d": _pdf_b64()}))

        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, _VIEWER_URL, body=_viewer("N"), status=200)
            rsps.add_callback(
                responses.POST, _POST_URL, callback=_post_cb
            )
            baixar_conteudo_vinculado(_CORPO)
        assert capturado == [
            {
                "codigoInstituicao": "2",
                "numeroProtocolo": "1570300",
                "token": "",
                "versaoCaptcha": "",
            }
        ]

    def test_captcha_habilitado_retorna_none(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, _VIEWER_URL, body=_viewer("S"), status=200)
            assert baixar_conteudo_vinculado(_CORPO) is None
            assert len(rsps.calls) == 1

    def test_erro_de_rede_retorna_none(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, _VIEWER_URL, status=500)
            assert baixar_conteudo_vinculado(_CORPO) is None

    def test_resposta_erro_do_webmethod_retorna_none(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, _VIEWER_URL, body=_viewer("N"), status=200)
            rsps.add(
                responses.POST,
                _POST_URL,
                body=json.dumps({"d": ":ERRO:protocolo invalido"}),
                status=200,
            )
            assert baixar_conteudo_vinculado(_CORPO) is None

    def test_resposta_captcha_v2_retorna_none(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, _VIEWER_URL, body=_viewer("N"), status=200)
            rsps.add(
                responses.POST, _POST_URL, body=json.dumps({"d": "V2"}), status=200
            )
            assert baixar_conteudo_vinculado(_CORPO) is None

    def test_sem_url_suportada_retorna_none(self):
        assert baixar_conteudo_vinculado("sem link") is None
