from dataclasses import dataclass


@dataclass(frozen=True)
class DominanceClassification:
    label: str
    short_label: str
    color: str
    score: int


_CLV_THRESHOLDS = [
    (-1.00, -0.70, "Venda Muito Forte", "Muito Forte", "#B71C1C", -3),
    (-0.70, -0.40, "Venda Forte", "Forte", "#D32F2F", -2),
    (-0.40, -0.15, "Venda Moderada", "Moderada", "#EF9A9A", -1),
    (-0.15, +0.15, "Equilíbrio", "Equilíbrio", "#BDBDBD", 0),
    (+0.15, +0.40, "Compra Moderada", "Moderada", "#A5D6A7", 1),
    (+0.40, +0.70, "Compra Forte", "Forte", "#388E3C", 2),
    (+0.70, +1.00, "Compra Muito Forte", "Muito Forte", "#1B5E20", 3),
]


def classify_dominance(clv: float) -> DominanceClassification:
    if clv < _CLV_THRESHOLDS[0][0]:
        lo, hi, label, short, color, score = _CLV_THRESHOLDS[0]
        return DominanceClassification(label, short, color, score)
    if clv >= _CLV_THRESHOLDS[-1][1]:
        lo, hi, label, short, color, score = _CLV_THRESHOLDS[-1]
        return DominanceClassification(label, short, color, score)
    for lo, hi, label, short, color, score in _CLV_THRESHOLDS:
        if lo <= clv < hi:
            return DominanceClassification(label, short, color, score)
    lo, hi, label, short, color, score = _CLV_THRESHOLDS[-1]
    return DominanceClassification(label, short, color, score)
