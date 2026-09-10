"""Adapter de patrimônio do Informe Mensal da CVM por ticker (RFC-009 §23)."""

import logging
from collections.abc import Callable
from datetime import date
from decimal import InvalidOperation

from flowscope.domain.cvm import FundIdentity, MonthlyReport
from flowscope.domain.fii.analysis import PatrimonioFii
from flowscope.infrastructure.cvm.identity import resolver_identidade
from flowscope.infrastructure.cvm.repository import CvmMonthlyReportRepository
from flowscope.infrastructure.fii.parsing import moeda_para_decimal

logger = logging.getLogger("flowscope")

#: Fonte registrada nos objetos de patrimônio produzidos pelo adapter.
FONTE_CVM = "CVM"


class CvmMonthlyPatrimonioSource:
    """Fornece ``PatrimonioFii`` a partir do Informe Mensal Estruturado."""

    def __init__(
        self: "CvmMonthlyPatrimonioSource",
        repository: CvmMonthlyReportRepository | None = None,
        resolver: Callable[[str], FundIdentity | None] | None = None,
    ) -> None:
        """Inicializa o adapter com o repositório e o resolvedor de identidade."""
        self._repository = repository or CvmMonthlyReportRepository()
        self._resolver = resolver or resolver_identidade

    def patrimonio(
        self: "CvmMonthlyPatrimonioSource", ticker: str, reference_date: date
    ) -> PatrimonioFii | None:
        """Resolve o patrimônio mais recente do ticker até a referência."""
        try:
            identidade = self._resolver(ticker)
            if identidade is None:
                return None
            report = self._repository.get(
                identidade.cnpj_fundo_classe, reference_date, ticker=ticker
            )
        except Exception:  # aquisição tolerante
            logger.warning(
                "Falha ao obter informe CVM de %s", ticker, exc_info=True
            )
            return None
        if report is None:
            return None
        return para_patrimonio(report)


def para_patrimonio(report: MonthlyReport) -> PatrimonioFii | None:
    """Retorna uma observação de patrimônio a partir de um registro do informe."""
    try:
        patrimonio = moeda_para_decimal(str(report.raw_rows.get("patrimonio")))
        cotas = moeda_para_decimal(str(report.raw_rows.get("cotas")))
    except (InvalidOperation, TypeError):
        return None
    return PatrimonioFii(
        reference_date=report.reference_date,
        net_asset_value=patrimonio,
        shares_outstanding=cotas,
        cotistas=_cotistas(report.raw_rows.get("cotistas")),
        fonte=FONTE_CVM,
    )


def _cotistas(valor: object) -> int | None:
    """Interpreta o número de cotistas, retornando ``None`` quando inválido."""
    if valor is None:
        return None
    try:
        return int(str(valor).strip())
    except ValueError:
        return None
