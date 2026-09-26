"""Normalização das pressões de compra e venda do pregão.

Calcula a participação relativa de cada lado da pressão sobre o total,
regra pura de domínio usada pelo painel de fluxo financeiro.
"""


def pressure_percentages(bp: float, sp: float) -> tuple[float, float]:
    """Calcula os percentuais de compra e venda sobre a pressão total.

    Quando não há pressão acumulada, retorna 50% para cada lado do range.
    """
    if bp + sp > 0:
        total = bp + sp
        return bp / total * 100, sp / total * 100
    return 50.0, 50.0
