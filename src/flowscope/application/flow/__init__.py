"""Regras de aplicação da fatia de Fluxo Financeiro.

Reúne o view-model com as métricas do último pregão e o resumo textual do
fluxo. Depende apenas de ``domain``; a apresentação apenas formata e desenha.
"""

from flowscope.application.flow.metrics import (
    SessionFlowMetrics,
    build_session_metrics,
)
from flowscope.application.flow.summary import (
    close_position_part,
    conviction_part,
    dominance_part,
    flow_intensity_part,
    generate_summary,
)

__all__ = [
    "SessionFlowMetrics",
    "build_session_metrics",
    "close_position_part",
    "conviction_part",
    "dominance_part",
    "flow_intensity_part",
    "generate_summary",
]
