"""Resumo textual da distribuição dos ativos entre quadrantes.

Contém as funções puras de contagem por quadrante e de escolha da
interpretação de mercado exibida no gráfico de quadrantes.
"""

from flowscope.application.quadrant.dados import PontoQuadrante
from flowscope.domain.strategies.classifiers import QUADRANTES, classify_quadrant


def count_quadrants(trajectories: list[list[PontoQuadrante]]) -> dict[str, int]:
    """Conta a quantidade de ativos em cada quadrante do gráfico."""
    counts = {quadrante: 0 for quadrante in QUADRANTES}
    for points in trajectories:
        point = points[-1]
        quadrant = classify_quadrant(point.clv, point.vwap_dist)
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


def generate_summary(trajectories: list[list[PontoQuadrante]]) -> str:
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
