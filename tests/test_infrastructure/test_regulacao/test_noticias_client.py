from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest
import responses

from flowscope.domain.structured import NoticiaB3
from flowscope.infrastructure.b3 import funds_client as fc
from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.cache import CacheManager

_NOTICIAS = fc._NOTICIAS_URL


def _noticia(titulo: str = "PETROBRAS anuncia pagamento de dividendos") -> dict:
    return {
        "titulo": titulo,
        "dataPublicacao": "2026-07-28 10:00:00",
        "url": "https://sistemasweb.b3.com.br/PlantaoNoticias/Noticia/1",
        "agencia": "18",
    }


def _item_plantao(
    titulo: str = "PETROBRAS (PETR-N2) - Outros Comunicados ao Mercado",
    data: str = "2026-09-25 09:18:13",
    identificador: int | str = 3494020,
) -> dict:
    return {
        "NwsMsg": {
            "IdAgencia": 18,
            "content": None,
            "dateTime": data,
            "headline": titulo,
            "id": identificador,
        }
    }


class TestListarNoticias:
    @responses.activate
    def test_retorna_noticias_convertidas(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(
            _NOTICIAS,
            json=[_noticia(), _noticia("B3 publica balanço do 2º trimestre")],
            status=200,
        )
        noticias = client.listar_noticias(
            data_inicio=date(2026, 7, 1), data_fim=date(2026, 7, 29)
        )
        assert len(noticias) == 2
        assert all(isinstance(n, NoticiaB3) for n in noticias)
        assert noticias[0].titulo.startswith("PETROBRAS")
        assert noticias[0].data_publicacao == "2026-07-28 10:00:00"
        assert noticias[0].agencia == "18"

    @responses.activate
    def test_filtro_de_palavra_aplicado_na_consulta(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(_NOTICIAS, json=[_noticia()], status=200)
        client.listar_noticias(
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 12, 31),
            palavra="PETROBRAS",
        )
        url = responses.calls[0].request.url
        consulta = parse_qs(urlparse(url).query)
        assert consulta["palavra"] == ["PETROBRAS"]
        assert consulta["dataInicial"] == ["2026-01-01"]
        assert consulta["dataFinal"] == ["2026-12-31"]
        assert consulta["agencia"] == ["18"]

    @responses.activate
    def test_sem_noticias_retorna_lista_vazia(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(_NOTICIAS, json=[], status=200)
        noticias = client.listar_noticias(
            data_inicio=date(2026, 7, 1), data_fim=date(2026, 7, 29)
        )
        assert noticias == []

    @responses.activate
    def test_segunda_chamada_na_mesma_hora_usando_cache(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(_NOTICIAS, json=[_noticia()], status=200)
        client.listar_noticias(
            data_inicio=date(2026, 7, 1), data_fim=date(2026, 7, 29)
        )
        noticias = client.listar_noticias(
            data_inicio=date(2026, 7, 1), data_fim=date(2026, 7, 29)
        )
        assert len(noticias) == 1
        assert len(responses.calls) == 1

    @responses.activate
    def test_filtro_diferente_gera_nova_requisicao(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(_NOTICIAS, json=[_noticia()], status=200)
        client.listar_noticias(palavra="PETROBRAS")
        client.listar_noticias(palavra="VALE")
        assert len(responses.calls) == 2

    @responses.activate
    def test_sem_ticker_consulta_sem_erro(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(_NOTICIAS, json=[_noticia()], status=200)
        noticias = client.listar_noticias()
        assert len(noticias) == 1


class TestFormatoPlantaoB3:
    @responses.activate
    def test_formato_nwsmsg_extrai_campos_e_deriva_url(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(_NOTICIAS, json=[_item_plantao()], status=200)
        noticias = client.listar_noticias(
            data_inicio=date(2026, 9, 1), data_fim=date(2026, 9, 25)
        )
        assert len(noticias) == 1
        noticia = noticias[0]
        assert noticia.titulo.startswith("PETROBRAS")
        assert noticia.data_publicacao == "2026-09-25 09:18:13"
        assert noticia.url is not None
        assert "Detail" in noticia.url
        assert "idNoticia=3494020" in noticia.url
        assert "dataNoticia=2026-09-25" in noticia.url
        assert "agencia=18" in noticia.url

    @responses.activate
    def test_deriva_url_de_id_noticia_alternativo(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        item = {"NwsMsg": {"headline": "Aviso", "dateTime": "2026-09-25 09:18:13"}}
        item["NwsMsg"]["idNoticia"] = "123"
        responses.get(_NOTICIAS, json=[item], status=200)
        noticias = client.listar_noticias(
            data_inicio=date(2026, 9, 1), data_fim=date(2026, 9, 25)
        )
        assert "idNoticia=123" in noticias[0].url

    @responses.activate
    def test_url_explicita_tem_precedencia(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        item = _item_plantao()
        item["NwsMsg"]["url"] = "https://exemplo/noticia"
        responses.get(_NOTICIAS, json=[item], status=200)
        noticias = client.listar_noticias(
            data_inicio=date(2026, 9, 1), data_fim=date(2026, 9, 25)
        )
        assert noticias[0].url == "https://exemplo/noticia"

    @responses.activate
    def test_sem_id_nao_deriva_url(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        item = {"NwsMsg": {"headline": "Sem id", "dateTime": "2026-09-25 09:18:13"}}
        responses.get(_NOTICIAS, json=[item], status=200)
        noticias = client.listar_noticias(
            data_inicio=date(2026, 9, 1), data_fim=date(2026, 9, 25)
        )
        assert noticias[0].titulo == "Sem id"
        assert noticias[0].url is None
