"""Provedores de identidade fiscal e indexadores a partir da CVM.

O Informe Anual Estruturado (INF_ANUAL) fornece gestor e administrador do FII;
o Formulário Cadastral (FCA) resolve o CNPJ de companhias abertas (Papel); e o
Informe Trimestral (INF_TRIMESTRAL) fornece os percentuais por indexador.
Todos atuam como fallback das fontes primárias, preservando a proveniência.
"""

import logging
from collections.abc import Callable
from datetime import date
from decimal import Decimal

from flowscope.application.fundamental_ports import (
    CAMPO_ADMINISTRADOR,
    CAMPO_CNPJ,
    CAMPO_CNPJ_ADMINISTRADOR,
    CAMPO_CNPJ_GESTOR,
    CAMPO_GESTOR,
    CampoFundamental,
)
from flowscope.domain.cvm import AnnualReport, FundIdentity
from flowscope.infrastructure.cvm.annual import CvmAnnualRepository
from flowscope.infrastructure.cvm.identity import resolver_identidade
from flowscope.infrastructure.cvm.quarterly import CvmQuarterlyRepository

logger = logging.getLogger("flowscope")

#: Fonte registrada nos valores produzidos por estes provedores.
FONTE_CVM = "CVM"


class CvmAnnualFundDataProvider:
    """Emite gestor e administrador a partir do Informe Anual da CVM."""

    def __init__(
        self: "CvmAnnualFundDataProvider",
        repository: CvmAnnualRepository | None = None,
        resolver: Callable[[str], FundIdentity | None] | None = None,
    ) -> None:
        """Inicializa o provedor com o repositório anual e o resolvedor."""
        self._repository = repository or CvmAnnualRepository()
        self._resolver = resolver or resolver_identidade

    def obter(
        self: "CvmAnnualFundDataProvider", ticker: str, reference_date: date
    ) -> dict[str, CampoFundamental]:
        """Retorna a identidade fiscal do fundo, ou vazio quando indisponível."""
        relatorio = self._obter_relatorio(ticker, reference_date)
        if relatorio is None:
            return {}
        campos: dict[str, CampoFundamental] = {}
        _adicionar(campos, CAMPO_CNPJ, relatorio.cnpj_fundo_classe)
        _adicionar(campos, CAMPO_GESTOR, relatorio.nome_gestor)
        _adicionar(campos, CAMPO_CNPJ_GESTOR, relatorio.cnpj_gestor)
        _adicionar(campos, CAMPO_ADMINISTRADOR, relatorio.nome_administrador)
        _adicionar(
            campos, CAMPO_CNPJ_ADMINISTRADOR, relatorio.cnpj_administrador
        )
        return campos

    def _obter_relatorio(
        self: "CvmAnnualFundDataProvider", ticker: str, reference_date: date
    ) -> AnnualReport | None:
        """Resolve o CNPJ do fundo e busca o Informe Anual, tolerando falhas."""
        try:
            identidade = self._resolver(ticker)
            if identidade is None:
                return None
            return self._repository.get(
                identidade.cnpj_fundo_classe, reference_date, ticker
            )
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter informe anual CVM de %s", ticker, exc_info=True
            )
            return None


class CvmPapelCnpjProvider:
    """Emite o CNPJ de companhias abertas (Papel) resolvido no FCA."""

    def __init__(
        self: "CvmPapelCnpjProvider",
        resolver: Callable[[str, date], str | None] | None = None,
    ) -> None:
        """Inicializa o provedor com o resolvedor de CNPJ por ticker."""
        self._resolver = resolver

    def obter(
        self: "CvmPapelCnpjProvider", ticker: str, reference_date: date
    ) -> dict[str, CampoFundamental]:
        """Retorna o CNPJ do Papel, ou vazio quando indisponível."""
        if self._resolver is None:
            return {}
        try:
            cnpj = self._resolver(ticker, reference_date)
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao resolver CNPJ CVM de %s", ticker, exc_info=True
            )
            return {}
        if not cnpj:
            return {}
        return {CAMPO_CNPJ: CampoFundamental(cnpj, FONTE_CVM)}


class CvmIndexadoresProvider:
    """Emite os percentuais de patrimônio por indexador do FII."""

    def __init__(
        self: "CvmIndexadoresProvider",
        repository: CvmQuarterlyRepository | None = None,
        resolver: Callable[[str], FundIdentity | None] | None = None,
    ) -> None:
        """Inicializa o provedor com o repositório trimestral e o resolvedor."""
        self._repository = repository or CvmQuarterlyRepository()
        self._resolver = resolver or resolver_identidade

    def obter_indexadores(
        self: "CvmIndexadoresProvider", ticker: str, reference_date: date
    ) -> dict[str, Decimal]:
        """Retorna os percentuais por indexador, ou vazio quando indisponível."""
        try:
            identidade = self._resolver(ticker)
            if identidade is None:
                return {}
            return self._repository.get_indexadores(
                identidade.cnpj_fundo_classe, reference_date
            )
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter indexadores CVM de %s", ticker, exc_info=True
            )
            return {}


def _adicionar(
    campos: dict[str, CampoFundamental], chave: str, valor: object
) -> None:
    """Adiciona um campo com a fonte CVM quando o valor existe."""
    if valor is not None:
        campos[chave] = CampoFundamental(valor, FONTE_CVM)
