"""Testes do cache de arquivos do Informe Mensal Estruturado da B3."""

from datetime import date, datetime, timezone

import requests

from flowscope.infrastructure.b3.informe_mensal_cache import (
    InformeMensalArquivoProvider,
    InformeMensalCache,
    resolver_data_referencia,
)
from flowscope.infrastructure.cache import CacheManager

_HTML = "<html><body>informe</body></html>"


def _documento(
    id_: int = 1293566,
    *,
    referencia: str | None = "2026-07-01T00:00:00-03:00",
    entrega: str | None = "14/08/2026",
) -> dict:
    return {
        "urlViewerFundosNet": (
            "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento"
            f"?id={id_}"
        ),
        "referenceDate": referencia,
        "referenceDateFormat": "07/2026",
        "deliveryDateFormat": entrega,
        "status": "1 (Ativo)",
    }


class _ClienteFake:
    def __init__(self, html: str = _HTML, erro_por_id: dict | None = None) -> None:
        self._html = html
        self._erro_por_id = erro_por_id or {}
        self.chamadas: list[str] = []

    def buscar_html_documento(self, id_documento: str) -> str:
        self.chamadas.append(id_documento)
        erro = self._erro_por_id.get(id_documento)
        if erro is not None:
            raise erro
        return self._html


class TestCache:
    def test_arvore_por_ticker_ano_mes(self, tmp_path):
        cache = InformeMensalCache(tmp_path)
        caminho = cache.caminho("alzr11", date(2026, 7, 1), 1293566)
        assert caminho == tmp_path / "ALZR11" / "2026" / "07" / "1293566.html"

    def test_grava_le_e_existe(self, tmp_path):
        cache = InformeMensalCache(tmp_path)
        cache.gravar("ALZR11", date(2026, 7, 1), 1293566, _HTML)
        assert cache.existe("ALZR11", date(2026, 7, 1), 1293566)
        assert cache.ler("ALZR11", date(2026, 7, 1), 1293566) == _HTML
        assert cache.ler("ALZR11", date(2026, 7, 1), 999) is None

    def test_grava_sem_deixar_temporario(self, tmp_path):
        cache = InformeMensalCache(tmp_path)
        caminho = cache.gravar("ALZR11", date(2026, 7, 1), 1, _HTML)
        assert caminho.is_file()
        assert list(tmp_path.rglob("*.tmp")) == []

    def test_listar_ordenado_do_mais_recente(self, tmp_path):
        cache = InformeMensalCache(tmp_path)
        cache.gravar("ALZR11", date(2026, 6, 1), 10, "junho")
        cache.gravar("ALZR11", date(2026, 7, 1), 11, "julho")
        cache.gravar("ALZR11", date(2025, 12, 1), 12, "dezembro")
        ids = [arquivo.document_id for arquivo in cache.listar("ALZR11")]
        assert ids == [11, 10, 12]

    def test_listar_ticker_sem_cache_retorna_vazio(self, tmp_path):
        cache = InformeMensalCache(tmp_path)
        assert cache.listar("ALZR11") == []

    def test_listar_ignora_arquivo_invalido(self, tmp_path):
        cache = InformeMensalCache(tmp_path)
        pasta = tmp_path / "ALZR11" / "2026" / "07"
        pasta.mkdir(parents=True)
        (pasta / "nao-numerico.html").write_text("x", encoding="utf-8")
        (pasta / "nota.txt").write_text("x", encoding="utf-8")
        assert cache.listar("ALZR11") == []


class TestDataReferencia:
    def test_usa_data_de_referencia(self):
        assert resolver_data_referencia(_documento()) == date(2026, 7, 1)

    def test_usa_data_de_entrega_quando_sem_referencia(self):
        documento = _documento(referencia=None)
        assert resolver_data_referencia(documento) == date(2026, 8, 14)

    def test_usa_data_corrente_como_fallback(self):
        documento = _documento(referencia=None, entrega=None)
        assert resolver_data_referencia(documento) == datetime.now(
            timezone.utc
        ).date()


class TestProvider:
    def test_persiste_html_em_disco(self, tmp_path):
        cliente = _ClienteFake()
        provider = InformeMensalArquivoProvider(client=cliente, cache_dir=tmp_path)
        arquivo = provider.persistir("ALZR11", _documento())
        assert arquivo is not None
        assert arquivo.caminho == (
            tmp_path / "ALZR11" / "2026" / "07" / "1293566.html"
        )
        assert arquivo.caminho.read_text(encoding="utf-8") == _HTML
        assert cliente.chamadas == ["1293566"]

    def test_cache_hit_nao_baixa_novamente(self, tmp_path):
        cliente = _ClienteFake()
        provider = InformeMensalArquivoProvider(client=cliente, cache_dir=tmp_path)
        provider.persistir("ALZR11", _documento())
        provider.persistir("ALZR11", _documento())
        assert cliente.chamadas == ["1293566"]

    def test_falha_de_download_nao_cria_arquivo(self, tmp_path):
        cliente = _ClienteFake(
            erro_por_id={"1": requests.ConnectionError("fora do ar")}
        )
        provider = InformeMensalArquivoProvider(client=cliente, cache_dir=tmp_path)
        assert provider.persistir("ALZR11", _documento(id_=1)) is None
        assert list(tmp_path.rglob("*.html")) == []

    def test_documento_sem_id_e_ignorado(self, tmp_path):
        cliente = _ClienteFake()
        provider = InformeMensalArquivoProvider(client=cliente, cache_dir=tmp_path)
        assert provider.persistir("ALZR11", {"urlViewerFundosNet": ""}) is None
        assert cliente.chamadas == []

    def test_falha_nao_interrompe_outros_documentos(self, tmp_path):
        cliente = _ClienteFake(
            erro_por_id={"1": requests.ConnectionError("fora do ar")}
        )
        provider = InformeMensalArquivoProvider(client=cliente, cache_dir=tmp_path)
        arquivos = provider.persistir_todos(
            "ALZR11", [_documento(id_=1), _documento(id_=2)]
        )
        assert [arquivo.document_id for arquivo in arquivos] == [2]

    def test_usa_cache_manager_quando_sem_cache_dir(self, tmp_path):
        cliente = _ClienteFake()
        provider = InformeMensalArquivoProvider(
            client=cliente, cache=CacheManager(tmp_path)
        )
        arquivo = provider.persistir("ALZR11", _documento())
        assert arquivo is not None
        assert provider.cache.base_dir == tmp_path / "informe-mensal"
