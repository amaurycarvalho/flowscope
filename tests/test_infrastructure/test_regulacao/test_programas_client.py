"""Testes do cliente dos programas de aquisição de ações da B3."""

import re
from datetime import date

import responses

from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.b3.funds_client import regulatorio
from flowscope.infrastructure.cache import CacheManager

_URL = re.compile(r".*/GetListedCompany/.*")

_REFERENCIA = date(2026, 9, 25)

_PAYLOAD = {
    "page": {"pageNumber": 1, "pageSize": 60, "totalRecords": 2, "totalPages": 1},
    "results": [
        {"company": "3TENTOS (NM)", "startDate": "13/08/2026", "quantity": "5.000.000 (ON)"},
        {"company": "ABC BRASIL (N2)", "startDate": "26/09/2025", "quantity": "7.500.000 (PN)"},
    ],
}


def _client(tmp_path):
    return B3FundosClient(cache=CacheManager(cache_dir=tmp_path))


class TestListarProgramas:
    @responses.activate
    def test_retry_apos_404(self, tmp_path, monkeypatch):
        monkeypatch.setattr(regulatorio, "_PROGRAMAS_ESPERA", 0)
        responses.add(responses.GET, _URL, status=404)
        responses.add(responses.GET, _URL, json=_PAYLOAD, status=200)

        programas = _client(tmp_path).listar_programas_aquisicao(_REFERENCIA)

        assert len(programas) == 2
        assert programas[0].empresa == "3TENTOS (NM)"
        assert len(responses.calls) == 2

    @responses.activate
    def test_falha_persistente_retorna_vazio(self, tmp_path, monkeypatch):
        monkeypatch.setattr(regulatorio, "_PROGRAMAS_ESPERA", 0)
        for _ in range(regulatorio._PROGRAMAS_TENTATIVAS):
            responses.add(responses.GET, _URL, status=404)

        assert _client(tmp_path).listar_programas_aquisicao(_REFERENCIA) == []

    @responses.activate
    def test_cache_evita_nova_requisicao(self, tmp_path):
        responses.add(responses.GET, _URL, json=_PAYLOAD, status=200)
        client = _client(tmp_path)

        primeira = client.listar_programas_aquisicao(_REFERENCIA)
        segunda = client.listar_programas_aquisicao(_REFERENCIA)

        assert len(primeira) == 2
        assert len(segunda) == 2
        assert len(responses.calls) == 1

    @responses.activate
    def test_pagina_multipla(self, tmp_path, monkeypatch):
        monkeypatch.setattr(regulatorio, "_PROGRAMAS_ESPERA", 0)
        pagina1 = {
            "page": {"pageNumber": 1, "pageSize": 1, "totalRecords": 2, "totalPages": 2},
            "results": [_PAYLOAD["results"][0]],
        }
        pagina2 = {
            "page": {"pageNumber": 2, "pageSize": 1, "totalRecords": 2, "totalPages": 2},
            "results": [_PAYLOAD["results"][1]],
        }
        responses.add(responses.GET, _URL, json=pagina1, status=200)
        responses.add(responses.GET, _URL, json=pagina2, status=200)

        programas = _client(tmp_path).listar_programas_aquisicao(_REFERENCIA)

        assert [p.empresa for p in programas] == ["3TENTOS (NM)", "ABC BRASIL (N2)"]
