"""Regras de aplicação da fatia de VWAP.

Reúne o read-model do gráfico de distribuição de preços em torno do VWAP: as
séries percentuais por ativo, os percentuais mínimo/máximo/último e as formas
acumuladas dos violinos. Depende apenas de ``domain``; a apresentação apenas
desenha.
"""

from flowscope.application.vwap.dados import (
    DadosVwap,
    FormasViolino,
    collect_ticker_data,
    compute_violin_shapes,
    estimate_bucket_size,
    to_pct,
)

__all__ = [
    "DadosVwap",
    "FormasViolino",
    "collect_ticker_data",
    "compute_violin_shapes",
    "estimate_bucket_size",
    "to_pct",
]
