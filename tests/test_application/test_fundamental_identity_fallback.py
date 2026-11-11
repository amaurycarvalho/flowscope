from datetime import date

import requests

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.application.fundamental_fallback import CompositeFundamentalProvider
from flowscope.domain.cvm import AnnualReport
from flowscope.infrastructure.b3.fund_identity_store import JsonFundIdentityStore
from flowscope.infrastructure.b3.fund_repository import B3FundRepository
from flowscope.infrastructure.cvm.identity import resolver_identidade
from flowscope.infrastructure.fii.cvm_fund_data_provider import (
    CvmAnnualFundDataProvider,
)

REFERENCIA = date(2026, 9, 4)
_TICKER = "ALZR11"
_CNPJ = "28737771000185"


class _B3Indisponivel:
    def obter_candidato(self, ticker):
        raise requests.ConnectionError("B3 fora do ar")


class _AnnualRepo:
    def get(self, cnpj, reference_date, ticker=""):
        return AnnualReport(
            ticker=ticker,
            cnpj_fundo_classe=cnpj,
            reference_date=date(2025, 12, 31),
            nome_gestor="GESTORA ALZR",
            cnpj_gestor="18.596.891/0001-56",
            nome_administrador="ADMINISTRADORA ALZR",
            cnpj_administrador="45.246.410/0001-55",
        )


class _RepoFundamental:
    def obter_nome(self, ticker):
        return None

    def obter_proventos(self, ticker, reference_date):
        return []

    def obter_patrimonio(self, ticker, reference_date):
        return None


def _store(tmp_path) -> JsonFundIdentityStore:
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


def test_identidade_persistida_alimenta_dados_fiscais_sem_b3(tmp_path):
    store = _store(tmp_path)
    fund_repository = B3FundRepository(
        client=_B3Indisponivel(), identity_store=store
    )
    fundo = fund_repository.find_by_ticker(_TICKER)
    assert fundo is not None
    assert fundo.fnet_id == "20294"
    assert fundo.trading_name == _CNPJ

    annual = CvmAnnualFundDataProvider(
        repository=_AnnualRepo(),
        resolver=lambda ticker: resolver_identidade(ticker, fund_repository),
    )
    caso = FundamentalAnalysisUseCase(
        _RepoFundamental(),
        fundamental_provider=CompositeFundamentalProvider([annual]),
    )
    resultado = caso.execute([_TICKER], REFERENCIA)[0]

    assert resultado.cnpj == _CNPJ
    assert resultado.nome_administrador == "ADMINISTRADORA ALZR"
    assert resultado.nome_gestor == "GESTORA ALZR"
