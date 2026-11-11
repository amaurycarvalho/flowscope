import json
from datetime import datetime, timedelta, timezone

from flowscope.infrastructure.b3.funds_client import (
    B3FundosClient,
    _chave_cache,
)
from flowscope.infrastructure.cache import CacheManager


class _RespostaJson:
    def __init__(self, payload: object) -> None:
        self._payload = payload
        self.status_code = 200
        self.headers: dict[str, str] = {}

    def json(self) -> object:
        return self._payload

    def raise_for_status(self) -> None:
        pass


class _RespostaCorpoVazio(_RespostaJson):
    def __init__(self) -> None:
        super().__init__(None)

    def json(self) -> object:
        raise json.JSONDecodeError("corpo vazio", "", 0)


class _SessaoFake:
    def __init__(self, respostas: list) -> None:
        self._respostas = list(respostas)
        self.urls: list[str] = []

    def get(self, url: str, **kwargs) -> _RespostaJson:
        self.urls.append(url)
        indice = len(self.urls) - 1
        resposta = self._respostas[min(indice, len(self._respostas) - 1)]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def _client(tmp_path, respostas) -> B3FundosClient:
    return B3FundosClient(
        cache=CacheManager(cache_dir=tmp_path),
        session=_SessaoFake(respostas),
        retry_delays=(0, 0, 0),
    )


def _pagina(resultados: list[dict], total: int, paginas: int = 1) -> _RespostaJson:
    return _RespostaJson(
        {
            "page": {
                "pageNumber": 1,
                "totalRecords": total,
                "totalPages": paginas,
            },
            "results": resultados,
        }
    )


def _expirar(cache: CacheManager, chave: str) -> None:
    meta = cache.read_meta(chave)
    assert meta is not None
    meta["cached_at"] = (
        datetime.now(timezone.utc) - timedelta(days=31)
    ).isoformat()
    cache.write_meta(chave, meta)


class TestCorpoVazioGetListClassFund:
    def test_corpo_vazio_e_repetido_ate_resposta_valida(self, tmp_path):
        fundos = _pagina([{"acronym": "ALZR", "id": 870}], total=1)
        classes = _RespostaJson(
            [{"id": "20294", "idMain": "870", "tradingName": "28.737.771/0001-85"}]
        )
        sessao = _SessaoFake([fundos, _RespostaCorpoVazio(), classes])
        client = B3FundosClient(
            cache=CacheManager(cache_dir=tmp_path),
            session=sessao,
            retry_delays=(0, 0, 0),
        )
        candidato = client.selecionar_candidato("ALZR11")
        assert candidato is not None
        assert candidato["id"] == "20294"
        assert len(sessao.urls) == 3


class TestListagemResiliente:
    def test_pagina_vazia_intermitente_e_repetida(self, tmp_path):
        pagina1 = _pagina([{"acronym": "ALZR", "id": 870}], total=3, paginas=3)
        pagina2_vazia = _pagina([], total=3, paginas=3)
        pagina2 = _pagina([{"acronym": "HGLG", "id": 123}], total=3, paginas=3)
        pagina3 = _pagina([{"acronym": "VISC", "id": 456}], total=3, paginas=3)
        sessao = _SessaoFake([pagina1, pagina2_vazia, pagina2, pagina3])
        client = B3FundosClient(
            cache=CacheManager(cache_dir=tmp_path),
            session=sessao,
            retry_delays=(0, 0, 0),
        )
        listagem = client.obter_listagem("FII")
        assert listagem.completa is True
        assert listagem.total_records == 3
        assert [fundo["acronym"] for fundo in listagem.fundos] == [
            "ALZR",
            "HGLG",
            "VISC",
        ]
        assert len(sessao.urls) == 4

    def test_lista_vazia_por_tipo_sem_fundos_e_completa(self, tmp_path):
        client = _client(tmp_path, [_pagina([], total=0)])
        listagem = client.obter_listagem("FIAGRO")
        assert listagem.completa is True
        assert listagem.fundos == []
        assert listagem.total_records == 0

    def test_lista_parcial_nao_sobrescreve_cache_completo(self, tmp_path):
        cache = CacheManager(cache_dir=tmp_path)
        completa = _pagina([{"acronym": "ALZR", "id": 870}], total=1)
        parcial = _pagina([{"acronym": "ALZR", "id": 870}], total=3)
        sessao = _SessaoFake([completa, parcial])
        client = B3FundosClient(
            cache=cache, session=sessao, retry_delays=(0, 0, 0)
        )
        chave = _chave_cache("fundos_listados", "FII")
        assert client.obter_listagem("FII").completa is True
        _expirar(cache, chave)
        resultado = client.obter_listagem("FII")
        assert resultado.completa is False
        assert resultado.total_records == 3
        assert cache.read_meta(chave)["results"] == [{"acronym": "ALZR", "id": 870}]


class TestChavesVersionadas:
    def test_cache_legado_de_listagem_e_ignorado(self, tmp_path):
        cache = CacheManager(cache_dir=tmp_path)
        cache.write_meta(
            "fundos_listados_FII",
            {"cached_at": datetime.now(timezone.utc).isoformat(), "results": []},
        )
        sessao = _SessaoFake([_pagina([{"acronym": "ALZR", "id": 870}], total=1)])
        client = B3FundosClient(
            cache=cache, session=sessao, retry_delays=(0, 0, 0)
        )
        listagem = client.obter_listagem("FII")
        assert [fundo["acronym"] for fundo in listagem.fundos] == ["ALZR"]
        assert len(sessao.urls) == 1

    def test_cache_legado_de_resolucao_e_ignorado(self, tmp_path):
        cache = CacheManager(cache_dir=tmp_path)
        cache.write_meta(
            "fund_resolution_ALZR11",
            {"cached_at": datetime.now(timezone.utc).isoformat(), "idFNET": "999"},
        )
        fundos = _pagina([{"acronym": "ALZR", "id": 870}], total=1)
        classes = _RespostaJson(
            [{"id": "20294", "idMain": "870", "tradingName": "28.737.771/0001-85"}]
        )
        sessao = _SessaoFake([fundos, classes])
        client = B3FundosClient(
            cache=cache, session=sessao, retry_delays=(0, 0, 0)
        )
        assert client.resolver_ticker("ALZR11") == "20294"


class TestCompletudeNaResolucao:
    def test_listagem_completa_sem_ticker_indica_ausencia_conclusiva(self, tmp_path):
        client = _client(tmp_path, [_pagina([{"acronym": "HGLG", "id": 123}], total=1)])
        resolucao = client.obter_candidato("XPTO11")
        assert resolucao.candidato is None
        assert resolucao.completa is True

    def test_listagem_incompleta_indica_ausencia_nao_conclusiva(self, tmp_path):
        client = _client(tmp_path, [_pagina([], total=2)])
        resolucao = client.obter_candidato("XPTO11")
        assert resolucao.candidato is None
        assert resolucao.completa is False
