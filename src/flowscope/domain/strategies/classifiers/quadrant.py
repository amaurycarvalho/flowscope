"""Classificação de quadrantes CLV x desvio do VWAP.

Identifica o quadrante de um ativo a partir do CLV e do desvio percentual do
preço ao VWAP. Pontos exatamente sobre um dos eixos não pertencem a nenhum
quadrante.
"""

#: Quadrantes na ordem de exibição (Q1 a Q4).
QUADRANTES: tuple[str, ...] = ("Q1", "Q2", "Q3", "Q4")


def classify_quadrant(clv: float, vwap_dist: float) -> str | None:
    """Identifica o quadrante do ponto com base em CLV e desvio do VWAP.

    Pontos exatamente sobre um dos eixos não pertencem a nenhum quadrante.
    """
    if clv > 0 and vwap_dist > 0:
        return "Q1"
    if clv < 0 and vwap_dist > 0:
        return "Q2"
    if clv < 0 and vwap_dist < 0:
        return "Q3"
    if clv > 0 and vwap_dist < 0:
        return "Q4"
    return None
