"""Preparação dos dados do gráfico de quadrantes.

Contém as funções puras responsáveis por transformar os dados brutos dos
ativos nas trajetórias CLV x desvio do VWAP e nos pontos de dispersão
prontos para o desenho.
"""

import math
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PontoQuadrante:
    """Ponto CLV x desvio do VWAP de um ativo em uma data."""

    ticker: str
    date: date
    clv: float
    vwap_dist: float
    fin_instr_qty: int


def build_trajectories(data: dict) -> list[list[PontoQuadrante]]:
    """Constroi as trajetórias de cada ativo a partir dos dados brutos.

    Para cada ativo com dados diários, agrega os pontos CLV x desvio do
    VWAP ordenados por data, ignorando os registros sem indicadores.
    """
    trajectories: list[list[PontoQuadrante]] = []
    for ticker, info in data.items():
        daily = info.get("daily_data", [])
        if not daily:
            continue
        clv_by_date = info.get("all_indicators", {}).get("clv") or {}
        vwap_dist_by_date = info.get("all_indicators", {}).get("vwap_distance") or {}
        points: list[PontoQuadrante] = []
        for d in sorted(daily, key=lambda x: x["date"]):
            dt = d["date"]
            clv = clv_by_date.get(dt)
            vd = vwap_dist_by_date.get(dt)
            if clv is None or vd is None:
                continue
            points.append(PontoQuadrante(
                ticker=ticker,
                date=dt,
                clv=float(clv),
                vwap_dist=float(vd) * 100,
                fin_instr_qty=d["fin_instr_qty"],
            ))
        if points:
            trajectories.append(points)
    return trajectories


def max_trajectory_qty(trajectories: list[list[PontoQuadrante]]) -> float:
    """Devolve a maior quantidade financeira entre todas as trajetórias.

    Usada como referência para normalizar o tamanho dos marcadores
    dos pontos finais de cada ativo.
    """
    return max(
        max(p.fin_instr_qty for p in pts)
        for pts in trajectories
    )


def point_size(point: PontoQuadrante, max_qty: float) -> float:
    """Calcula o tamanho do marcador do ponto final de uma trajetória.

    A escala é proporcional à raiz quadrada da quantidade normalizada,
    respeitando um tamanho mínimo para garantir a visibilidade.
    """
    norm = math.sqrt(point.fin_instr_qty / max_qty) if max_qty > 0 else 0.1
    return max(norm * 200, 10)


def compute_scatter_data(trajectories: list[list[PontoQuadrante]]) -> tuple:
    """Reúne coordenadas e pontos finais para desenhar o gráfico.

    Returns:
        Tupla com os eixos x/y de todos os pontos, eixos dos pontos finais,
        tamanhos, cores e a lista de pontos finais usada no hover.
    """
    all_x: list[float] = []
    all_y: list[float] = []
    for points in trajectories:
        for p in points:
            all_x.append(p.clv)
            all_y.append(p.vwap_dist)

    last_points = [points[-1] for points in trajectories]
    max_qty = max_trajectory_qty(trajectories)
    last_x = [p.clv for p in last_points]
    last_y = [p.vwap_dist for p in last_points]
    last_sizes = [point_size(p, max_qty) for p in last_points]
    last_colors = [p.clv for p in last_points]
    return last_x, last_y, last_sizes, last_colors, all_y, last_points
