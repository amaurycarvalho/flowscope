from datetime import date
from decimal import Decimal

from flowscope.domain.cvm import AnnualReport, FundIdentity
from flowscope.infrastructure.fii.cvm_fund_data_provider import (
    CvmAnnualFundDataProvider,
    CvmIndexadoresProvider,
    CvmPapelCnpjProvider,
)

REFERENCIA = date(2026, 9, 10)
IDENTIDADE = FundIdentity(ticker="CYCR11", cnpj_fundo_classe="36501233000115")
RELATORIO = AnnualReport(
    ticker="CYCR11",
    cnpj_fundo_classe="36501233000115",
    reference_date=date(2025, 12, 31),
    nome_gestor="CY.CAPITAL GESTORA DE RECURSOS LTDA",
    cnpj_gestor="18.596.891/0001-56",
    nome_administrador="BANCO GENIAL S.A.",
    cnpj_administrador="45.246.410/0001-55",
)


class _AnnualRepo:
    def __init__(self, relatorio=RELATORIO):
        self._relatorio = relatorio
        self.chamadas = []

    def get(self, cnpj, reference_date, ticker=""):
        self.chamadas.append((cnpj, reference_date, ticker))
        return self._relatorio


class TestCvmAnnualFundDataProvider:
    def test_emite_gestor_administrador_e_cnpj(self):
        provider = CvmAnnualFundDataProvider(
            repository=_AnnualRepo(), resolver=lambda ticker: IDENTIDADE
        )
        campos = provider.obter("CYCR11", REFERENCIA)
        assert campos["cnpj"].valor == "36501233000115"
        assert campos["gestor"].valor == "CY.CAPITAL GESTORA DE RECURSOS LTDA"
        assert campos["cnpj_gestor"].valor == "18.596.891/0001-56"
        assert campos["administrador"].valor == "BANCO GENIAL S.A."
        assert campos["cnpj_administrador"].valor == "45.246.410/0001-55"
        assert campos["cnpj"].fonte == "CVM"

    def test_resolve_pelo_cnpj_da_identidade(self):
        repo = _AnnualRepo()
        provider = CvmAnnualFundDataProvider(
            repository=repo, resolver=lambda ticker: IDENTIDADE
        )
        provider.obter("CYCR11", REFERENCIA)
        assert repo.chamadas == [("36501233000115", REFERENCIA, "CYCR11")]

    def test_identidade_ausente_retorna_vazio(self):
        provider = CvmAnnualFundDataProvider(
            repository=_AnnualRepo(), resolver=lambda ticker: None
        )
        assert provider.obter("PETR4", REFERENCIA) == {}

    def test_relatorio_ausente_retorna_vazio(self):
        provider = CvmAnnualFundDataProvider(
            repository=_AnnualRepo(relatorio=None),
            resolver=lambda ticker: IDENTIDADE,
        )
        assert provider.obter("CYCR11", REFERENCIA) == {}

    def test_falha_do_repositorio_e_tolerada(self):
        class Explode:
            def get(self, *args, **kwargs):
                raise RuntimeError("indisponível")

        provider = CvmAnnualFundDataProvider(
            repository=Explode(), resolver=lambda ticker: IDENTIDADE
        )
        assert provider.obter("CYCR11", REFERENCIA) == {}

    def test_campos_ausentes_omitidos(self):
        relatorio = AnnualReport(
            ticker="X",
            cnpj_fundo_classe="36501233000115",
            reference_date=REFERENCIA,
            nome_gestor="GESTOR SEM CNPJ",
        )
        provider = CvmAnnualFundDataProvider(
            repository=_AnnualRepo(relatorio), resolver=lambda ticker: IDENTIDADE
        )
        campos = provider.obter("X", REFERENCIA)
        assert campos["gestor"].valor == "GESTOR SEM CNPJ"
        assert "cnpj_gestor" not in campos


class TestCvmPapelCnpjProvider:
    def test_emite_cnpj_do_papel(self):
        provider = CvmPapelCnpjProvider(
            resolver=lambda ticker, ref: "33000167000101"
        )
        campos = provider.obter("PETR4", REFERENCIA)
        assert campos["cnpj"].valor == "33000167000101"
        assert campos["cnpj"].fonte == "CVM"

    def test_sem_cnpj_retorna_vazio(self):
        provider = CvmPapelCnpjProvider(resolver=lambda ticker, ref: None)
        assert provider.obter("PETR4", REFERENCIA) == {}

    def test_sem_resolver_retorna_vazio(self):
        assert CvmPapelCnpjProvider().obter("PETR4", REFERENCIA) == {}

    def test_falha_tolerada(self):
        def explode(ticker, ref):
            raise RuntimeError("indisponível")

        assert CvmPapelCnpjProvider(resolver=explode).obter(
            "PETR4", REFERENCIA
        ) == {}


class TestCvmIndexadoresProvider:
    def test_emite_indexadores(self):
        class Repo:
            def get_indexadores(self, cnpj, reference_date):
                return {"IPCA": Decimal("0.220667")}

        provider = CvmIndexadoresProvider(
            repository=Repo(), resolver=lambda ticker: IDENTIDADE
        )
        assert provider.obter_indexadores("CYCR11", REFERENCIA) == {
            "IPCA": Decimal("0.220667")
        }

    def test_identidade_ausente_retorna_vazio(self):
        provider = CvmIndexadoresProvider(
            repository=object(), resolver=lambda ticker: None
        )
        assert provider.obter_indexadores("PETR4", REFERENCIA) == {}

    def test_falha_tolerada(self):
        class Explode:
            def get_indexadores(self, *args):
                raise RuntimeError("indisponível")

        provider = CvmIndexadoresProvider(
            repository=Explode(), resolver=lambda ticker: IDENTIDADE
        )
        assert provider.obter_indexadores("CYCR11", REFERENCIA) == {}
