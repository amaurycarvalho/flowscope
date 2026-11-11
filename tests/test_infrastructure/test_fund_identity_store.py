import json

import requests

from flowscope.domain.b3 import B3Fund
from flowscope.infrastructure.b3.fund_identity_store import (
    SCHEMA_VERSION_IDENTIDADE,
    JsonFundIdentityStore,
)
from flowscope.infrastructure.b3.fund_repository import B3FundRepository
from flowscope.infrastructure.b3.funds_client import ResolucaoCandidato

_TICKER = "ALZR11"
_CNPJ = "28737771000185"


class TestJsonFundIdentityStore:
    def test_grava_e_le_identidade(self, tmp_path):
        store = JsonFundIdentityStore(cache_dir=tmp_path)
        store.salvar(
            _TICKER,
            id_fnet="20294",
            primary_id="870",
            name="ALIANZA TRUST",
            trading_name="28.737.771/0001-85",
            cnpj=_CNPJ,
            type_fund="FII",
        )
        registro = store.obter(_TICKER)
        assert registro is not None
        assert registro.ticker == _TICKER
        assert registro.id_fnet == "20294"
        assert registro.primary_id == "870"
        assert registro.name == "ALIANZA TRUST"
        assert registro.cnpj == _CNPJ
        assert registro.type_fund == "FII"
        assert registro.updated_at

    def test_caminho_por_ticker(self, tmp_path):
        store = JsonFundIdentityStore(cache_dir=tmp_path)
        assert store.caminho(_TICKER) == tmp_path / "fund_identity" / "ALZR11.json"

    def test_ausente_retorna_none(self, tmp_path):
        assert JsonFundIdentityStore(cache_dir=tmp_path).obter(_TICKER) is None

    def test_corrompido_retorna_none(self, tmp_path):
        store = JsonFundIdentityStore(cache_dir=tmp_path)
        caminho = store.caminho(_TICKER)
        caminho.parent.mkdir(parents=True)
        caminho.write_text("not-json", encoding="utf-8")
        assert store.obter(_TICKER) is None

    def test_versao_antiga_retorna_none(self, tmp_path):
        store = JsonFundIdentityStore(cache_dir=tmp_path)
        caminho = store.caminho(_TICKER)
        caminho.parent.mkdir(parents=True)
        caminho.write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION_IDENTIDADE - 1,
                    "ticker": _TICKER,
                    "id_fnet": "20294",
                }
            ),
            encoding="utf-8",
        )
        assert store.obter(_TICKER) is None

    def test_invalidar_remove_registro(self, tmp_path):
        store = JsonFundIdentityStore(cache_dir=tmp_path)
        store.salvar(_TICKER, id_fnet="20294")
        store.invalidar(_TICKER)
        assert store.obter(_TICKER) is None


class _Cliente:
    def __init__(self, resolucao=None, erro=None):
        self._resolucao = resolucao
        self._erro = erro

    def obter_candidato(self, ticker):
        if self._erro is not None:
            raise self._erro
        return self._resolucao

    def obter_nome_negociacao(self, ticker):
        return None


def _candidato(cnpj: str = "28.737.771/0001-85") -> dict:
    return {
        "id": "20294",
        "idMain": "870",
        "fundName": "ALIANZA TRUST",
        "tradingName": cnpj,
    }


def _store_com_identidade(tmp_path) -> JsonFundIdentityStore:
    store = JsonFundIdentityStore(cache_dir=tmp_path)
    store.salvar(
        _TICKER,
        id_fnet="20294",
        primary_id="870",
        name="ALIANZA TRUST",
        trading_name="28.737.771/0001-85",
        cnpj=_CNPJ,
        type_fund="FII",
    )
    return store


class TestB3FundRepositoryComIdentidade:
    def test_resolucao_bem_sucedida_grava_identidade(self, tmp_path):
        store = JsonFundIdentityStore(cache_dir=tmp_path)
        repo = B3FundRepository(
            client=_Cliente(ResolucaoCandidato(_candidato(), True, "FII")),
            identity_store=store,
        )
        fundo = repo.find_by_ticker(_TICKER)
        assert fundo == B3Fund(
            ticker=_TICKER,
            fnet_id="20294",
            primary_id="870",
            name="ALIANZA TRUST",
            trading_name="28.737.771/0001-85",
        )
        registro = store.obter(_TICKER)
        assert registro is not None
        assert registro.id_fnet == "20294"
        assert registro.cnpj == _CNPJ
        assert registro.type_fund == "FII"

    def test_listagem_incompleta_usa_identidade_persistida(self, tmp_path):
        store = _store_com_identidade(tmp_path)
        repo = B3FundRepository(
            client=_Cliente(ResolucaoCandidato(None, False)),
            identity_store=store,
        )
        fundo = repo.find_by_ticker(_TICKER)
        assert fundo is not None
        assert fundo.fnet_id == "20294"
        assert fundo.trading_name == _CNPJ

    def test_b3_indisponivel_usa_identidade_persistida(self, tmp_path):
        store = _store_com_identidade(tmp_path)
        repo = B3FundRepository(
            client=_Cliente(erro=requests.ConnectionError("fora do ar")),
            identity_store=store,
        )
        fundo = repo.find_by_ticker(_TICKER)
        assert fundo is not None
        assert fundo.fnet_id == "20294"
        assert fundo.trading_name == _CNPJ

    def test_listagem_completa_sem_ticker_nao_usa_identidade(self, tmp_path):
        store = _store_com_identidade(tmp_path)
        repo = B3FundRepository(
            client=_Cliente(ResolucaoCandidato(None, True)),
            identity_store=store,
        )
        assert repo.find_by_ticker(_TICKER) is None

    def test_falha_da_classe_apos_primario_usa_identidade(self, tmp_path):
        store = _store_com_identidade(tmp_path)
        repo = B3FundRepository(
            client=_Cliente(ResolucaoCandidato(None, False, "FII")),
            identity_store=store,
        )
        assert repo.find_by_ticker(_TICKER) is not None

    def test_ausencia_completa_nao_grava_negativo(self, tmp_path):
        store = JsonFundIdentityStore(cache_dir=tmp_path)
        repo = B3FundRepository(
            client=_Cliente(ResolucaoCandidato(None, True)),
            identity_store=store,
        )
        assert repo.find_by_ticker(_TICKER) is None
        assert store.obter(_TICKER) is None
