"""Regras de aplicação da fatia de Quadrantes.

Reúne os view-models do gráfico de quadrantes: as trajetórias CLV x desvio do
VWAP por ativo, os pontos de dispersão prontos e o resumo textual da
distribuição. Depende apenas de ``domain``; a apresentação apenas desenha.
"""

from flowscope.application.quadrant.dados import (
    PontoQuadrante,
    build_trajectories,
    compute_scatter_data,
    max_trajectory_qty,
    point_size,
)
from flowscope.application.quadrant.resumo import (
    count_quadrants,
    generate_summary,
    pick_interpretation,
)

__all__ = [
    "PontoQuadrante",
    "build_trajectories",
    "compute_scatter_data",
    "count_quadrants",
    "generate_summary",
    "max_trajectory_qty",
    "pick_interpretation",
    "point_size",
]
