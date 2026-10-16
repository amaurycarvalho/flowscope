"""Testes do helper de download resiliente compartilhado."""

import pytest
import responses

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.infrastructure.download_resiliente import (
    baixar_conteudo,
    post_renovando_sessao,
    validar_pdf,
)

_PDF = b"%PDF-1.7\nconteudo"
_URL = "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=1"
_PAGE = "https://www.rad.cvm.gov.br/ENETWEB/frmExibirArquivoIPEExterno.aspx?ID=1"
_POST = (
    "https://www.rad.cvm.gov.br/ENETWEB/"
    "frmExibirArquivoIPEExterno.aspx/ExibirPDF"
)


class TestBaixarConteudo:
    @responses.activate
    def test_conteudo_valido_retorna_resposta(self):
        responses.get(_URL, body=_PDF, status=200)
        resposta = baixar_conteudo(_URL, validar=validar_pdf)
        assert resposta is not None
        assert resposta.content == _PDF

    @responses.activate
    def test_conteudo_invalido_retorna_none(self):
        responses.get(_URL, body="<html>challenge</html>", status=200)
        assert baixar_conteudo(_URL, validar=validar_pdf) is None

    @responses.activate
    def test_conteudo_invalido_repetido_ate_valido(self):
        responses.get(_URL, body="<html>challenge</html>", status=200)
        responses.get(_URL, body=_PDF, status=200)
        resposta = baixar_conteudo(_URL, validar=validar_pdf)
        assert resposta is not None
        assert resposta.content == _PDF
        assert len(responses.calls) == 2

    @responses.activate
    def test_override_403_repetido(self):
        responses.get(_URL, status=403)
        responses.get(_URL, body=_PDF, status=200)
        resposta = baixar_conteudo(
            _URL, validar=validar_pdf, transitorios_extra=frozenset({403})
        )
        assert resposta is not None
        assert len(responses.calls) == 2

    @responses.activate
    def test_sem_override_403_nao_repete(self):
        responses.get(_URL, status=403)
        assert baixar_conteudo(_URL, validar=validar_pdf) is None
        assert len(responses.calls) == 1

    @responses.activate
    def test_segue_iframe_quando_nao_e_pdf(self):
        iframe = "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=2"
        responses.get(
            _URL,
            body=(
                "<html><body>"
                f'<iframe src="{iframe}"></iframe>'
                "</body></html>"
            ),
            status=200,
        )
        responses.get(iframe, body=_PDF, status=200)
        resposta = baixar_conteudo(_URL, validar=validar_pdf, seguir_iframe=True)
        assert resposta is not None
        assert resposta.content == _PDF

    @responses.activate
    def test_orcamento_esgotado_nao_requisita(self):
        assert baixar_conteudo(_URL, timeout_total=0.0) is None
        assert len(responses.calls) == 0

    @responses.activate
    def test_cancelamento_propaga(self):
        def cancelar():
            raise OperacaoCancelada()

        with pytest.raises(OperacaoCancelada):
            baixar_conteudo(_URL, cancelar=cancelar)


class TestPostRenovandoSessao:
    @responses.activate
    def test_renova_pagina_apos_falha_do_post(self):
        responses.get(_PAGE, body="<html>1</html>", status=200)
        responses.get(_PAGE, body="<html>2</html>", status=200)
        responses.post(_POST, status=502)
        responses.post(_POST, json={"ok": True}, status=200)
        resposta = post_renovando_sessao(_PAGE, _POST, "{}")
        assert resposta is not None
        metodos = [chamada.request.method for chamada in responses.calls]
        assert metodos == ["GET", "POST", "GET", "POST"]

    @responses.activate
    def test_conteudo_invalido_renova_e_repet(self):
        responses.get(_PAGE, body="<html>x</html>", status=200)
        responses.get(_PAGE, body="<html>x</html>", status=200)
        responses.get(_PAGE, body="<html>x</html>", status=200)
        responses.post(_POST, json={"d": "invalido"}, status=200)
        responses.post(_POST, json={"d": "invalido"}, status=200)
        responses.post(_POST, json={"d": "invalido"}, status=200)
        assert (
            post_renovando_sessao(
                _PAGE, _POST, "{}", validar=lambda _r: False
            )
            is None
        )
        gets = [c for c in responses.calls if c.request.method == "GET"]
        posts = [c for c in responses.calls if c.request.method == "POST"]
        assert len(gets) == 3
        assert len(posts) == 3

    @responses.activate
    def test_pagina_rejeitada_retorna_none(self):
        responses.get(_PAGE, body="<html>captcha</html>", status=200)
        resultado = post_renovando_sessao(
            _PAGE, _POST, "{}", inspectar_pagina=lambda _r: False
        )
        assert resultado is None
        assert len(responses.calls) == 1

    @responses.activate
    def test_orcamento_esgotado_nao_requisita(self):
        assert post_renovando_sessao(_PAGE, _POST, "{}", timeout_total=0.0) is None
        assert len(responses.calls) == 0
