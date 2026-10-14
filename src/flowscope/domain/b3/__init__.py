"""Domínio da aquisição de dados da B3 (RFC-008)."""

from flowscope.domain.b3.calendario import FERIADOS_NACIONAIS, is_business_day
from flowscope.domain.b3.models import (
    AcquisitionMetadata,
    AcquisitionResult,
    B3Fund,
    B3InformeMensal,
    B3ReportReference,
)

__all__ = [
    "FERIADOS_NACIONAIS",
    "AcquisitionMetadata",
    "AcquisitionResult",
    "B3Fund",
    "B3InformeMensal",
    "B3ReportReference",
    "is_business_day",
]
