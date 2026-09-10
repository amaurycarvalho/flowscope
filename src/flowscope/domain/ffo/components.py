"""Componentes e tipos do motor determinístico de FFO (RFC-010)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class FFOComponentType(Enum):
    """Classificação econômica de um componente de resultado."""

    RECURRING = "RECURRING"
    FAIR_VALUE = "FAIR_VALUE"
    DISPOSAL = "DISPOSAL"
    NON_RECURRING = "NON_RECURRING"
    UNKNOWN = "UNKNOWN"


class FFOQuality(Enum):
    """Qualidade do FFO calculado."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class ComponentProvenance:
    """Origem de um componente usado no cálculo do FFO (RFC-010 §30)."""

    source: str = "CVM"
    dataset: str = "INF_TRIMESTRAL"
    file: str = ""
    cnpj: str = ""
    reference_date: date | None = None
    field: str = ""


@dataclass(frozen=True)
class FFOComponent:
    """Componente de resultado com valor, classificação e proveniência."""

    description: str
    value: Decimal
    classification: FFOComponentType = FFOComponentType.UNKNOWN
    provenance: ComponentProvenance | None = None
    code: str = ""

    @property
    def included_in_ffo(self: "FFOComponent") -> bool:
        """Indica se o componente entra no FFO (apenas recorrentes)."""
        return self.classification is FFOComponentType.RECURRING
