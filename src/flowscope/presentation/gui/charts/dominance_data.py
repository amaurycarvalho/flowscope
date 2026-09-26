"""Desenho e hover compartilhados pelos gráficos de dominância do pregão.

Mantém as funções que dependem dos eixos matplotlib (desenho das hastes) e a
localização da linha mais próxima do cursor; a geometria das hastes vem de
:mod:`flowscope.application.dominance.hastes`.
"""

from flowscope.application.dominance.hastes import compute_stems
from flowscope.application.dominance.ranking import RankingRow
from flowscope.application.dominance.timeline import TimelineRow


def draw_stems(
    axes: object,
    mfvs: list[float],
    clvs: list[float],
    y_pos: list[int],
    max_val: float,
    scale: float = 0.10,
) -> None:
    """Desenha as hastes de volume sobre as barras do gráfico.

    Quando nenhuma haste é produzida, a chamada é ignorada para
    evitar desenhar coleções vazias sobre a figura.
    """
    stem_ys, stem_xmins, stem_xmaxs, stem_colors = compute_stems(
        mfvs, clvs, y_pos, max_val, scale=scale,
    )
    if stem_ys:
        axes.hlines(
            stem_ys, stem_xmins, stem_xmaxs,
            colors=stem_colors, linewidth=2, zorder=5,
        )


def bar_hit(clv: float, x: float) -> bool:
    """Indica se a posição x está dentro da barra do CLV informado."""
    if clv >= 0:
        return 0.0 <= x <= clv
    return clv <= x <= 0.0


def find_closest_row(
    rows: list[RankingRow | TimelineRow], x: float, y: float
) -> RankingRow | TimelineRow | None:
    """Localiza a linha mais próxima do cursor no gráfico.

    Retorna o registro cuja barra contém a posição (x, y) e que esteja
    dentro da distância mínima de tolerância em relação ao eixo vertical.
    """
    closest = None
    min_dist = 0.3
    for idx, pt in enumerate(rows):
        dy = abs(y - idx)
        if dy > min_dist:
            continue
        if not bar_hit(pt.clv, x):
            continue
        if dy < min_dist:
            min_dist = dy
            closest = pt
    return closest
