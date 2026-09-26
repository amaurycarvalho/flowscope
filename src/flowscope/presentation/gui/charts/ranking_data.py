"""Desenho dos rótulos do gráfico de ranking de dominância.

Mantém apenas o posicionamento dos rótulos dos tickers ao lado de cada
barra; a construção das linhas e as hastes vêm de
:mod:`flowscope.application.dominance.ranking`.
"""


def draw_ticker_labels(
    axes: object,
    tickers: list[str],
    clvs: list[float],
    stem_lens: list[float],
    y_pos: list[int],
) -> None:
    """Desenha os rótulos dos tickers ao lado de cada barra do ranking.

    O rótulo é posicionado na extremidade livre da haste e limitado
    aos extremos do eixo para não ultrapassar a área útil do gráfico.
    """
    for i, (ticker, clv) in enumerate(zip(tickers, clvs)):
        stem_len = stem_lens[i]
        if clv >= 0:
            label_x = clv + stem_len + 0.02
            ha = "left"
        else:
            label_x = clv - stem_len - 0.02
            ha = "right"
        if label_x > 1.18:
            label_x = 1.18
            ha = "right"
        elif label_x < -1.18:
            label_x = -1.18
            ha = "left"
        axes.text(
            label_x, y_pos[i], ticker,
            ha=ha, va="center", fontsize=8, zorder=4,
        )
