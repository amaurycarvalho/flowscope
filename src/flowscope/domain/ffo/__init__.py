"""Domínio do motor determinístico de FFO (RFC-010)."""

from flowscope.domain.ffo.components import (
    ComponentProvenance,
    FFOComponent,
    FFOComponentType,
    FFOQuality,
)
from flowscope.domain.ffo.engine import (
    FFO_CALCULATION_VERSION,
    LIMITE_MATERIALIDADE_BAIXO,
    LIMITE_MATERIALIDADE_MEDIO,
    LIMITE_RECONCILIACAO,
    FFOResult,
    calcular_ffo,
    calculate_ffo,
    media_ponderada_cotas,
)
from flowscope.domain.ffo.rules import (
    FFO_RULES_VERSION,
    classificar_componente,
)

__all__ = [
    "FFO_CALCULATION_VERSION",
    "FFO_RULES_VERSION",
    "LIMITE_MATERIALIDADE_BAIXO",
    "LIMITE_MATERIALIDADE_MEDIO",
    "LIMITE_RECONCILIACAO",
    "ComponentProvenance",
    "FFOComponent",
    "FFOComponentType",
    "FFOQuality",
    "FFOResult",
    "calcular_ffo",
    "calculate_ffo",
    "classificar_componente",
    "media_ponderada_cotas",
]
