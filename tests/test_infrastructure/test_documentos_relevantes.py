"""Testes da aquisição e do cache de documentos relevantes da B3."""

import base64
import json
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import requests
import responses

from flowscope.domain.structured import DocumentoRelevante
from flowscope.infrastructure.b3.documentos_relevantes import (
    DocumentosRelevantesCache,
    DocumentosRelevantesProvider,
    resolver_data_referencia,
)
from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.b3.funds_client.constants import _TIMEOUT_DOCUMENTO
from flowscope.infrastructure.cache import CacheManager

_BASE = B3FundosClient._BASE_URL
_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "b3"
_PDF = b"%PDF-1.4\nconteudo"
_URL_PDF = "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento"


def _fixture(nome: str) -> dict:
    return json.loads((_FIXTURES / nome).read_text(encoding="utf-8"))


def _token(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"))
    return base64.b64encode(raw.encode()).decode()


def _payload(
    category: int, page: int = 1, id_fnet: str = "20294"
) -> dict:
    return {
        "language": "pt-br",
        "dataInicial": "2026-01-01",
        "dataFinal": "2026-07-29",
        "pageNumber": page,
        "pageSize": 20,
        "idFNET": id_fnet,
        "typeFund": "FII",
        "category": category,
    }


def _item(
    id_: int = 1252542,
    *,
    categoria: int = 2,
    referencia: str | None = "2026-07-17T00:00:00-03:00",
    entrega: str | None = "17/07/2026",
) -> dict:
    return {
        "urlViewerFundosNet": (
            "https://fnet.bmfbovespa.com.br/fnet/publico/"
            f"visualizarDocumento?id={id_}"
        ),
        "category": str(categoria),
        "referenceDate": referencia,
        "deliveryDateFormat": entrega,
        "describleKind": "Ata de Assembleia Geral Ordinária",
        "status": "1 (Ativo)",
    }


class _ClienteFake:
    def __init__(self, itens: list[dict], respostas: dict) -> None:
        self._itens = itens
        self._respostas = respostas
        self.chamadas: list[str] = []

    def listar_todos_documentos_relevantes(self, id_fnet, data_inicio, data_fim):
        return list(self._itens)

    def baixar_pdf_documento(self, id_documento: str):
        self.chamadas.append(id_documento)
        resultado = self._respostas.get(id_documento)
        if isinstance(resultado, Exception):
            raise resultado
        return resultado


class TestListarDocumentosRelevantes:
    @responses.activate
    def test_categoria_unica(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(
            f"{_BASE}/GetReportsRelevants/{_token(_payload(2))}",
            json=_fixture("relevant_reports_alzr.json"),
            status=200,
        )
        docs = client.listar_documentos_relevantes(
            "20294", date(2026, 1, 1), date(2026, 7, 29), 2
        )
        assert len(docs) == 2
        assert all(doc["category"] == "2" for doc in docs)
        assert len(responses.calls) == 1

    @responses.activate
    def test_paginacao_multiplas_paginas(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        for page in (1, 2, 3):
            responses.get(
                f"{_BASE}/GetReportsRelevants/{_token(_payload(2, page))}",
                json={"page": {"totalPages": 3}, "results": [{"id": page}]},
                status=200,
            )
        docs = client.listar_documentos_relevantes(
            "20294", date(2026, 1, 1), date(2026, 7, 29), 2
        )
        assert len(docs) == 3
        assert len(responses.calls) == 3

    @responses.activate
    def test_resultado_cacheado_por_um_dia(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(
            f"{_BASE}/GetReportsRelevants/{_token(_payload(2))}",
            json=_fixture("relevant_reports_alzr.json"),
            status=200,
        )
        client.listar_documentos_relevantes(
            "20294", date(2026, 1, 1), date(2026, 7, 29), 2
        )
        client.listar_documentos_relevantes(
            "20294", date(2026, 1, 1), date(2026, 7, 29), 2
        )
        assert len(responses.calls) == 1

    def test_id_fnet_none_retorna_vazio(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        docs = client.listar_documentos_relevantes(
            None, date(2026, 1, 1), date(2026, 7, 29), 2
        )
        assert docs == []


class TestListarTodasCategorias:
    @responses.activate
    def test_consolida_quatro_categorias(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        for codigo in (1, 2, 3, 7):
            responses.get(
                f"{_BASE}/GetReportsRelevants/{_token(_payload(codigo))}",
                json={
                    "page": {"totalPages": 1},
                    "results": [
                        {"urlViewerFundosNet": f"https://fnet?id={codigo}"}
                    ],
                },
                status=200,
            )
        docs = client.listar_todos_documentos_relevantes(
            "20294", date(2026, 1, 1), date(2026, 7, 29)
        )
        assert len(docs) == 4
        assert {doc["category"] for doc in docs} == {"1", "2", "3", "7"}

    @responses.activate
    def test_falha_isolada_por_categoria(self, tmp_path):
        client = B3FundosClient(
            cache=CacheManager(cache_dir=tmp_path), retry_delays=(0,)
        )
        for codigo in (1, 2, 3, 7):
            if codigo == 2:
                responses.get(
                    f"{_BASE}/GetReportsRelevants/{_token(_payload(codigo))}",
                    status=500,
                )
            else:
                responses.get(
                    f"{_BASE}/GetReportsRelevants/{_token(_payload(codigo))}",
                    json={
                        "page": {"totalPages": 1},
                        "results": [
                            {"urlViewerFundosNet": f"https://fnet?id={codigo}"}
                        ],
                    },
                    status=200,
                )
        docs = client.listar_todos_documentos_relevantes(
            "20294", date(2026, 1, 1), date(2026, 7, 29)
        )
        assert len(docs) == 3
        assert "2" not in {doc["category"] for doc in docs}


class TestBaixarPdfDocumento:
    @responses.activate
    def test_pdf_valido(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(f"{_URL_PDF}?id=1252542", body=_PDF, status=200)
        assert client.baixar_pdf_documento("1252542") == _PDF

    @responses.activate
    def test_conteudo_nao_pdf_e_rejeitado(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(
            f"{_URL_PDF}?id=1", body="<html>erro</html>", status=200
        )
        assert client.baixar_pdf_documento("1") is None

    def test_usa_timeout_curto_para_nao_travar(self, tmp_path, monkeypatch):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        capturado: dict[str, object] = {}

        def _fake(url, timeout=30, **kwargs):
            capturado["timeout"] = timeout
            resposta = MagicMock()
            resposta.content = _PDF
            return resposta

        monkeypatch.setattr(client, "_requisicao_get", _fake)
        assert client.baixar_pdf_documento("1") == _PDF
        assert capturado["timeout"] == _TIMEOUT_DOCUMENTO

    @responses.activate
    def test_timeout_e_retentado_ate_sucesso(self, tmp_path):
        client = B3FundosClient(
            cache=CacheManager(cache_dir=tmp_path), retry_delays=(0, 0)
        )
        chamadas: list[int] = []

        def _callback(_request):
            chamadas.append(1)
            if len(chamadas) == 1:
                raise requests.exceptions.ReadTimeout("sem resposta")
            return (200, {}, _PDF)

        responses.add_callback(
            responses.GET, f"{_URL_PDF}?id=1252542", callback=_callback
        )
        assert client.baixar_pdf_documento("1252542") == _PDF
        assert len(chamadas) == 2


class TestCacheArvore:
    def test_caminho_por_ticker_ano_mes_categoria(self, tmp_path):
        cache = DocumentosRelevantesCache(tmp_path)
        caminho = cache.caminho(
            "alzr11", date(2026, 7, 1), "assembleia", "1252542"
        )
        assert caminho == (
            tmp_path / "ALZR11" / "2026" / "07" / "assembleia" / "1252542.pdf"
        )

    def test_grava_le_e_existe(self, tmp_path):
        cache = DocumentosRelevantesCache(tmp_path)
        cache.gravar("ALZR11", date(2026, 7, 1), "assembleia", "1", _PDF)
        assert cache.existe("ALZR11", date(2026, 7, 1), "assembleia", "1")
        assert cache.ler("ALZR11", date(2026, 7, 1), "assembleia", "1") == _PDF
        assert cache.ler("ALZR11", date(2026, 7, 1), "assembleia", "9") is None

    def test_grava_sem_deixar_temporario(self, tmp_path):
        cache = DocumentosRelevantesCache(tmp_path)
        caminho = cache.gravar(
            "ALZR11", date(2026, 7, 1), "assembleia", "1", _PDF
        )
        assert caminho.is_file()
        assert list(tmp_path.rglob("*.tmp")) == []

    def test_listar_ordenado_do_mais_recente(self, tmp_path):
        cache = DocumentosRelevantesCache(tmp_path)
        cache.gravar("ALZR11", date(2026, 6, 1), "assembleia", "10", _PDF)
        cache.gravar("ALZR11", date(2026, 7, 1), "assembleia", "11", _PDF)
        cache.gravar("ALZR11", date(2025, 12, 1), "relatorio", "12", _PDF)
        arquivos = cache.listar("ALZR11")
        assert [arquivo.document_id for arquivo in arquivos] == ["11", "10", "12"]
        assert arquivos[2].categoria == "Relatorio"

    def test_listar_ticker_sem_cache_vazio(self, tmp_path):
        cache = DocumentosRelevantesCache(tmp_path)
        assert cache.listar("ALZR11") == []

    def test_listar_ignora_categoria_desconhecida(self, tmp_path):
        cache = DocumentosRelevantesCache(tmp_path)
        pasta = tmp_path / "ALZR11" / "2026" / "07" / "outra"
        pasta.mkdir(parents=True)
        (pasta / "1.pdf").write_bytes(_PDF)
        assert cache.listar("ALZR11") == []


class TestDataReferencia:
    def test_usa_data_de_referencia(self):
        assert resolver_data_referencia(_item()) == date(2026, 7, 17)

    def test_usa_data_de_entrega_quando_sem_referencia(self):
        assert resolver_data_referencia(_item(referencia=None)) == date(
            2026, 7, 17
        )

    def test_usa_data_corrente_como_fallback(self):
        documento = _item(referencia=None, entrega=None)
        assert resolver_data_referencia(documento) == datetime.now(
            timezone.utc
        ).date()


class TestProvider:
    def test_persiste_pdf_valido(self, tmp_path):
        cliente = _ClienteFake([_item()], {"1252542": _PDF})
        provider = DocumentosRelevantesProvider(
            client=cliente, cache_dir=tmp_path
        )
        documento = provider.persistir("ALZR11", "20294", _item())
        assert isinstance(documento, DocumentoRelevante)
        assert documento.ticker == "ALZR11"
        assert documento.categoria == "Assembleia"
        assert documento.descricao == "Ata de Assembleia Geral Ordinária"
        assert documento.data_referencia == date(2026, 7, 17)
        assert documento.data_entrega == "17/07/2026"
        assert documento.tamanho_bytes == len(_PDF)
        caminho = (
            tmp_path / "ALZR11" / "2026" / "07" / "assembleia" / "1252542.pdf"
        )
        assert caminho.read_bytes() == _PDF
        assert cliente.chamadas == ["1252542"]

    def test_cache_hit_nao_baixa_novamente(self, tmp_path):
        cliente = _ClienteFake([_item()], {"1252542": _PDF})
        provider = DocumentosRelevantesProvider(
            client=cliente, cache_dir=tmp_path
        )
        provider.persistir("ALZR11", "20294", _item())
        provider.persistir("ALZR11", "20294", _item())
        assert cliente.chamadas == ["1252542"]

    def test_conteudo_nao_pdf_rejeitado_sem_arquivo(self, tmp_path):
        cliente = _ClienteFake([_item(id_=1)], {"1": None})
        provider = DocumentosRelevantesProvider(
            client=cliente, cache_dir=tmp_path
        )
        assert provider.persistir("ALZR11", "20294", _item(id_=1)) is None
        assert list(tmp_path.rglob("*.pdf")) == []

    def test_falha_de_download_nao_cria_arquivo(self, tmp_path):
        cliente = _ClienteFake(
            [_item(id_=1)], {"1": requests.ConnectionError("fora do ar")}
        )
        provider = DocumentosRelevantesProvider(
            client=cliente, cache_dir=tmp_path
        )
        assert provider.persistir("ALZR11", "20294", _item(id_=1)) is None
        assert list(tmp_path.rglob("*.pdf")) == []

    def test_item_sem_id_e_ignorado(self, tmp_path):
        cliente = _ClienteFake([], {})
        provider = DocumentosRelevantesProvider(
            client=cliente, cache_dir=tmp_path
        )
        assert provider.persistir("ALZR11", "20294", {"urlViewerFundosNet": ""}) is None
        assert cliente.chamadas == []

    def test_sincronizar_tolera_falhas_individuais(self, tmp_path):
        itens = [_item(id_=1), _item(id_=2)]
        cliente = _ClienteFake(
            itens,
            {"1": requests.ConnectionError("fora do ar"), "2": _PDF},
        )
        provider = DocumentosRelevantesProvider(
            client=cliente, cache_dir=tmp_path
        )
        documentos = provider.sincronizar(
            "ALZR11", "20294", date(2026, 1, 1), date(2026, 7, 29)
        )
        assert [doc.id_documento for doc in documentos] == ["2"]

    def test_usa_cache_manager_quando_sem_cache_dir(self, tmp_path):
        cliente = _ClienteFake([_item()], {"1252542": _PDF})
        provider = DocumentosRelevantesProvider(
            client=cliente, cache=CacheManager(tmp_path)
        )
        provider.persistir("ALZR11", "20294", _item())
        assert provider.cache.base_dir == tmp_path / "documentos-relevantes"
