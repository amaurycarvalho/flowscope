"""Preparação dos dados e resumo do gráfico de quadrantes do FlowScope.

Contém as funções puras responsáveis por transformar os dados brutos dos
ativos nas trajetórias CLV x desvio do VWAP e por gerar o resumo textual
da distribuição entre os quadrantes.
"""

import math


def build_trajectories(data: dict) -> list[list[dict]]:
    """Constroi as trajetórias de cada ativo a partir dos dados brutos.

    Para cada ativo com dados diários, agrega os pontos CLV x desvio do
    VWAP ordenados por data, ignorando os registros sem indicadores.
    """
    trajectories: list[list[dict]] = []
    for ticker, info in data.items():
        daily = info.get("daily_data", [])
        if not daily:
            continue
        clv_by_date = info.get("all_indicators", {}).get("clv") or {}
        vwap_dist_by_date = info.get("all_indicators", {}).get("vwap_distance") or {}
        points = []
        for d in sorted(daily, key=lambda x: x["date"]):
            dt = d["date"]
            clv = clv_by_date.get(dt)
            vd = vwap_dist_by_date.get(dt)
            if clv is None or vd is None:
                continue
            points.append({
                "ticker": ticker,
                "date": dt,
                "clv": float(clv),
                "vwap_dist": float(vd) * 100,
                "fin_instr_qty": d["fin_instr_qty"],
            })
        if points:
            trajectories.append(points)
    return trajectories


def max_trajectory_qty(trajectories: list[list[dict]]) -> float:
    """Devolve a maior quantidade financeira entre todas as trajetórias.

    Usada como referência para normalizar o tamanho dos marcadores
    dos pontos finais de cada ativo.
    """
    return max(
        max(p["fin_instr_qty"] for p in pts)
        for pts in trajectories
    )


def point_size(point: dict, max_qty: float) -> float:
    """Calcula o tamanho do marcador do ponto final de uma trajetória.

    A escala é proporcional à raiz quadrada da quantidade normalizada,
    respeitando um tamanho mínimo para garantir a visibilidade.
    """
    norm = math.sqrt(point["fin_instr_qty"] / max_qty) if max_qty > 0 else 0.1
    return max(norm * 200, 10)


def compute_scatter_data(trajectories: list[list[dict]]) -> tuple:
    """Reúne coordenadas e pontos finais para desenhar o gráfico.

    Returns:
        Tupla com os eixos x/y de todos os pontos, eixos dos pontos finais,
        tamanhos, cores e a lista de pontos finais usada no hover.
    """
    all_x: list[float] = []
    all_y: list[float] = []
    for points in trajectories:
        for p in points:
            all_x.append(p["clv"])
            all_y.append(p["vwap_dist"])

    last_points = [points[-1] for points in trajectories]
    max_qty = max_trajectory_qty(trajectories)
    last_x = [p["clv"] for p in last_points]
    last_y = [p["vwap_dist"] for p in last_points]
    last_sizes = [point_size(p, max_qty) for p in last_points]
    last_colors = [p["clv"] for p in last_points]
    return last_x, last_y, last_sizes, last_colors, all_y, last_points


def classify_quadrant(point: dict) -> str | None:
    """Identifica o quadrante do ponto com base em CLV e desvio do VWAP.

    Pontos exatamente sobre um dos eixos não pertencem a nenhum quadrante.
    """
    clv = point["clv"]
    vwap = point["vwap_dist"]
    if clv > 0 and vwap > 0:
        return "Q1"
    if clv < 0 and vwap > 0:
        return "Q2"
    if clv < 0 and vwap < 0:
        return "Q3"
    if clv > 0 and vwap < 0:
        return "Q4"
    return None


def count_quadrants(trajectories: list[list[dict]]) -> dict[str, int]:
    """Conta a quantidade de ativos em cada quadrante do gráfico."""
    counts = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    for points in trajectories:
        quadrant = classify_quadrant(points[-1])
        if quadrant:
            counts[quadrant] += 1
    return counts


def pick_interpretation(counts: dict[str, int]) -> str:
    """Escolhe a interpretação de mercado conforme a distribuição.

    Prioriza leituras dominantes e, na ausência de um sinal claro,
    devolve uma mensagem de equilíbrio entre os quadrantes.
    """
    total = sum(counts.values())
    if total == 0:
        return ""
    q1 = counts["Q1"] / total
    q3 = counts["Q3"] / total
    q2 = counts["Q2"] / total
    q4 = counts["Q4"] / total
    if q1 > 0.5:
        return (
            "Predominância de ativos com fechamento acima do VWAP e forte "
            "pressão compradora, indicando um pregão amplamente construtivo."
        )
    if q3 > 0.5:
        return (
            "Maioria dos ativos encerrou abaixo do VWAP com pressão vendedora "
            "dominante, caracterizando um pregão de distribuição."
        )
    if q2 > 0.4 and q2 > q4:
        return (
            "Apesar de muitos ativos permanecerem acima do VWAP, houve "
            "enfraquecimento no fechamento, sugerindo realização de lucros."
        )
    if q4 > 0.4 and q4 > q2:
        return (
            "Diversos ativos reagiram no fechamento, mas ainda terminaram "
            "abaixo do VWAP, indicando possível início de recuperação, "
            "ainda sem confirmação."
        )
    return (
        "Distribuição equilibrada entre os quadrantes, "
        "sem sinal direcional claro."
    )


def generate_summary(trajectories: list[list[dict]]) -> str:
    """Gera o resumo textual da distribuição dos ativos entre quadrantes.

    Returns:
        Texto com a distribuição e a interpretação, ou vazio quando não
        há pontos válidos para análise.
    """
    counts = count_quadrants(trajectories)
    total = sum(counts.values())
    if total == 0:
        return ""
    distribution = (
        f"Distribuição: Q1={counts['Q1']}, Q2={counts['Q2']}, "
        f"Q3={counts['Q3']}, Q4={counts['Q4']} (total: {total})"
    )
    return "\n\n".join([distribution, pick_interpretation(counts)])
