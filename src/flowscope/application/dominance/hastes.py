"""Geometria e cores das hastes de volume dos gráficos de dominância.

Concentra as funções puras compartilhadas pelo ranking e pela linha do tempo:
o comprimento normalizado da haste, a montagem das hastes com posição,
extensão e intensidade de cor conforme a classificação de dominância, e as
cores das barras por CLV.
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


def compute_stems(
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
