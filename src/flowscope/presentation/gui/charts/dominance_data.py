"""Funções compartilhadas pelos gráficos de dominância do pregão.

Reúne a construção das hastes de volume, as cores das barras e a
localização da linha mais próxima do cursor, usadas tanto no ranking
de dominância quanto na linha do tempo de um ativo.
"""

import math

from flowscope.domain.strategies.classifiers import classify_dominance


def stem_length(value: float, max_val: float, scale: float) -> float:
    """Calcula o comprimento normalizado da haste de um valor.

    Valores nulos não geram haste e o comprimento mínimo é garantido
    para manter a haste visível em escalas pequenas.
    """
    if value == 0.0:
        return 0.0
    norm = abs(value) / max_val if max_val > 0 else 0
    return max(math.sqrt(norm) * scale, 0.015)


def _compute_stems(
    values: list[float],
    clvs: list[float],
    y_pos: list[int],
    max_val: float,
    scale: float = 0.10,
) -> tuple[list[int], list[float], list[float], list[str]]:
    """Computa as hastes de volume com posição, extensão e cor por linha.

    As hastes partem do eixo zero em direção ao CLV, com intensidade
    da cor crescente conforme o grau de dominância da classificação.
    """
    stem_ys: list[int] = []
    stem_xmins: list[float] = []
    stem_xmaxs: list[float] = []
    stem_colors: list[str] = []
    for i, (clv, val) in enumerate(zip(clvs, values)):
        if val == 0.0 or abs(clv) < 0.05:
            continue
        stem_len = stem_length(val, max_val, scale)
        cls = classify_dominance(clv)
        stem_ys.append(y_pos[i])
        intensity = abs(cls.score)
        if intensity == 0:
            gray = "#C0C0C0"
        elif intensity == 1:
            gray = "#555555"
        elif intensity == 2:
            gray = "#222222"
        else:
            gray = "#0A0A0A"
        stem_colors.append(gray)
        if clv >= 0:
            stem_xmins.append(0.0)
            stem_xmaxs.append(clv + stem_len)
        else:
            stem_xmins.append(clv - stem_len)
            stem_xmaxs.append(0.0)
    return stem_ys, stem_xmins, stem_xmaxs, stem_colors


def bar_colors(clvs: list[float]) -> list[str]:
    """Devolve a cor de classificação de dominância para cada CLV."""
    return [classify_dominance(clv).color for clv in clvs]


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
    stem_ys, stem_xmins, stem_xmaxs, stem_colors = _compute_stems(
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


def find_closest_row(rows: list[dict], x: float, y: float) -> dict | None:
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
        if not bar_hit(pt["clv"], x):
            continue
        if dy < min_dist:
            min_dist = dy
            closest = pt
    return closest
