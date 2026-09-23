"""Testes do cliente de consulta da última release do FlowScope."""

import requests
import responses

from flowscope.infrastructure.releases import (
    LATEST_RELEASE_URL,
    RELEASES_BASE_URL,
    obter_ultima_release,
)

_TAG_URL = f"{RELEASES_BASE_URL}/tag/v1.2.0"


class TestObterUltimaRelease:
    @responses.activate
    def test_extrai_tag_do_redirecionamento(self):
        responses.get(LATEST_RELEASE_URL, status=302, headers={"Location": _TAG_URL})
        responses.get(_TAG_URL, status=200, body="")

        assert obter_ultima_release() == ("1.2.0", _TAG_URL)

    @responses.activate
    def test_tag_sem_prefixo_v(self):
        destino = f"{RELEASES_BASE_URL}/tag/1.2.0"
        responses.get(LATEST_RELEASE_URL, status=302, headers={"Location": destino})
        responses.get(destino, status=200, body="")

        assert obter_ultima_release() == ("1.2.0", destino)

    @responses.activate
    def test_sem_redirecionamento_para_tag(self):
        responses.get(LATEST_RELEASE_URL, status=200, body="")

        assert obter_ultima_release() is None

    @responses.activate
    def test_redirecionamento_para_tag_invalida(self):
        destino = f"{RELEASES_BASE_URL}/tag/nightly"
        responses.get(LATEST_RELEASE_URL, status=302, headers={"Location": destino})
        responses.get(destino, status=200, body="")

        assert obter_ultima_release() is None

    @responses.activate
    def test_timeout_retorna_none(self):
        responses.get(LATEST_RELEASE_URL, body=requests.Timeout("tempo esgotado"))

        assert obter_ultima_release() is None

    @responses.activate
    def test_falha_de_conexao_retorna_none(self):
        responses.get(LATEST_RELEASE_URL, body=requests.ConnectionError("offline"))

        assert obter_ultima_release() is None
