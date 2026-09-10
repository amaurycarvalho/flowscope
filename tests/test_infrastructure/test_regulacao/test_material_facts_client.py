import base64
import json
from datetime import date, datetime, timezone

import pytest
import responses

from flowscope.domain.structured import (
    Assembleia,
    CategoriaMaterialFact,
    DocumentoMaterialFact,
    FatoRelevante,
)
from flowscope.infrastructure.b3 import funds_client as fc
from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.cache import CacheManager

_LISTED = fc._LISTED_BASE_URL


def _token(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"))
    return base64.b64encode(raw.encode()).decode()


def _pagina(pagina: int, total_paginas: int, itens: list[dict]) -> dict:
    return {
        "page": {
            "pageNumber": pagina,
            "pageSize": 20,
            "totalRecords": len(itens),
            "totalPages": total_paginas,
        },
        "results": itens,
    }


def _item_fato_relevante() -> dict:
    return {
        "company": {
            "codeCVM": "009512",
            "companyName": "PETROLEO BRASILEIRO S.A. PETROBRAS",
            "tradingName": "PETROBRAS",
        },
        "dateReference": "16/04/2026 14:16",
        "delivery": "Apresentação",
        "deliveryDate": "28/04/2026 19:19:42",
        "status": "Ativo",
        "category": "Fatos Relevantes",
        "type": "",
        "kind": "",
        "version": "1",
        "subject": "Tomada de Contas-Votação do Relatório da Administração",
        "urlSearch": "https://www.rad.cvm.gov.br/ENETWEB/frmExibirArquivoIPEExterno.aspx?ID=1510187",
        "urlDownload": "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext",
    }


def _registrar_pagina(itens: list[dict], pagina: int = 1, total_paginas: int = 1):
    payload = {
        "linguagem": "pt-br",
        "codeCVM": "9512",
        "year": 2026,
        "dataInicial": "2026-01-01",
        "dataFinal": "2026-12-31",
        "categoria": "4",
        "pageNumber": pagina,
        "pageSize": 20,
    }
    responses.get(
        f"{_LISTED}/GetMaterialFacts/{_token(payload)}",
        json=_pagina(pagina, total_paginas, itens),
        status=200,
    )


class TestListarFatosRelevantes:
    @responses.activate
    def test_pagina_unica_converte_documentos(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        _registrar_pagina([_item_fato_relevante()])
        documentos = client.listar_fatos_relevantes(
            "9512",
            CategoriaMaterialFact.FATOS_RELEVANTES,
            date(2026, 1, 1),
            date(2026, 12, 31),
            ticker="PETR4",
        )
        assert len(documentos) == 1
        documento = documentos[0]
        assert isinstance(documento, FatoRelevante)
        assert documento.code_cvm == "9512"
        assert documento.empresa.startswith("PETROLEO")
        assert documento.ticker == "PETR4"
        assert documento.categoria == "Fatos Relevantes"
        assert documento.data_referencia == "16/04/2026 14:16"
        assert documento.to_text()
        assert len(responses.calls) == 1

    @responses.activate
    def test_categoria_assembleia_vira_entidade_assembleia(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        item = _item_fato_relevante()
        item["category"] = "Assembleia"
        item["type"] = "AGO"
        item["kind"] = "Ata"
        payload = {
            "linguagem": "pt-br",
            "codeCVM": "9512",
            "year": 2026,
            "dataInicial": "2026-01-01",
            "dataFinal": "2026-12-31",
            "categoria": "1",
            "pageNumber": 1,
            "pageSize": 20,
        }
        responses.get(
            f"{_LISTED}/GetMaterialFacts/{_token(payload)}",
            json=_pagina(1, 1, [item]),
            status=200,
        )
        documento = client.listar_fatos_relevantes(
            "9512",
            CategoriaMaterialFact.ASSEMBLEIAS,
            date(2026, 1, 1),
            date(2026, 12, 31),
            ticker="PETR4",
        )[0]
        assert isinstance(documento, Assembleia)
        assert documento.tipo_assembleia == "AGO"
        assert documento.especie_documento == "Ata"

    @responses.activate
    def test_paginacao_automatica(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        for pagina in (1, 2, 3):
            _registrar_pagina([_item_fato_relevante()], pagina=pagina, total_paginas=3)
        documentos = client.listar_fatos_relevantes(
            "9512", "4", date(2026, 1, 1), date(2026, 12, 31), ticker="PETR4"
        )
        assert len(documentos) == 3
        assert len(responses.calls) == 3

    @responses.activate
    def test_segunda_chamada_no_mesmo_dia_usando_cache(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        _registrar_pagina([_item_fato_relevante()])
        client.listar_fatos_relevantes(
            "9512", "4", date(2026, 1, 1), date(2026, 12, 31), ticker="PETR4"
        )
        documentos = client.listar_fatos_relevantes(
            "9512", "4", date(2026, 1, 1), date(2026, 12, 31), ticker="PETR4"
        )
        assert len(documentos) == 1
        assert len(responses.calls) == 1

    @responses.activate
    def test_cache_expira_apos_um_dia(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        chave = "matfacts_9512_4_2026-01-01_2026-12-31"
        meta = tmp_path / f"{chave}.json"
        meta.write_text(
            json.dumps(
                {
                    "cached_at": "2020-01-01T00:00:00+00:00",
                    "results": [],
                }
            ),
            encoding="utf-8",
        )
        _registrar_pagina([_item_fato_relevante()])
        documentos = client.listar_fatos_relevantes(
            "9512", "4", date(2026, 1, 1), date(2026, 12, 31), ticker="PETR4"
        )
        assert len(documentos) == 1
        assert len(responses.calls) == 1

    @responses.activate
    def test_categoria_invalida_rejeitada_antes_da_requisicao(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        with pytest.raises(ValueError):
            client.listar_fatos_relevantes(
                "9512", "99", date(2026, 1, 1), date(2026, 12, 31)
            )
        assert len(responses.calls) == 0

    @responses.activate
    def test_api_indisponivel_retorna_lista_vazia(self, tmp_path):
        client = B3FundosClient(
            cache=CacheManager(cache_dir=tmp_path), retry_delays=(0,)
        )
        payload = {
            "linguagem": "pt-br",
            "codeCVM": "9512",
            "year": 2026,
            "dataInicial": "2026-01-01",
            "dataFinal": "2026-12-31",
            "categoria": "4",
            "pageNumber": 1,
            "pageSize": 20,
        }
        responses.get(
            f"{_LISTED}/GetMaterialFacts/{_token(payload)}", status=500
        )
        documentos = client.listar_fatos_relevantes(
            "9512", "4", date(2026, 1, 1), date(2026, 12, 31), ticker="PETR4"
        )
        assert documentos == []


class TestSemResultados:
    @responses.activate
    def test_sem_resultados_retorna_lista_vazia(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        _registrar_pagina([])
        documentos = client.listar_fatos_relevantes(
            "9512", "4", date(2026, 1, 1), date(2026, 12, 31), ticker="PETR4"
        )
        assert documentos == []
