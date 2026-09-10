"""Provedor de FFO calculado pelo motor determinístico (RFC-010).

Satisfaz o contrato ``FfoProvider`` usando os componentes do Informe Trimestral
da CVM, atuando como fallback quando o Fundamentus não fornece o FFO.
"""

import logging
from collections.abc import Callable
from datetime import date

from flowscope.domain.cvm import FundIdentity
from flowscope.domain.ffo import calcular_ffo
from flowscope.domain.fii.analysis import FfoObservacao
from flowscope.infrastructure.cvm.identity import resolver_identidade
from flowscope.infrastructure.cvm.quarterly import CvmQuarterlyRepository

logger = logging.getLogger("flowscope")

#: Fonte registrada nos objetos de FFO produzidos pelo motor.
FONTE_CVM = "CVM"

#: Metodologia do FFO derivado internamente pelo FlowScope.
METODOLOGIA = "FLOWSCOPE_DERIVED"


class FFOEngineProvider:
    """Calcula o FFO a partir de componentes estruturados da CVM."""

    def __init__(
        self: "FFOEngineProvider",
        quarterly_repository: CvmQuarterlyRepository | None = None,
        resolver: Callable[[str], FundIdentity | None] | None = None,
    ) -> None:
        """Inicializa o provedor com o repositório trimestral e o resolvedor."""
        self._quarterly = quarterly_repository or CvmQuarterlyRepository()
        self._resolver = resolver or resolver_identidade

    def obter_ffo(
        self: "FFOEngineProvider", ticker: str, reference_date: date
    ) -> FfoObservacao | None:
        """Calcula o FFO 12m/3m do ticker, ou ``None`` quando indisponível."""
        try:
            identidade = self._resolver(ticker)
            if identidade is None:
                return None
            componentes = self._quarterly.get_components(
                identidade.cnpj_fundo_classe, reference_date, ticker
            )
        except Exception:  # aquisição tolerante
            logger.warning(
                "Falha ao calcular FFO de %s", ticker, exc_info=True
            )
            return None
        if not componentes:
            return None
        resultado = calcular_ffo(componentes, reference_date)
        if resultado.ffo_12m is None or resultado.ffo_3m is None:
            return None
        return FfoObservacao(
            ffo_12m=resultado.ffo_12m,
            ffo_3m=resultado.ffo_3m,
            fonte=FONTE_CVM,
            metodologia=METODOLOGIA,
        )
