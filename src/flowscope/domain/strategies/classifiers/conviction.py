from dataclasses import dataclass


@dataclass(frozen=True)
class ConvictionClassification:
    label: str
    short_label: str
    color: str
    score: int


_EFFICIENCY_THRESHOLDS = [
    (0.00, 0.20, "Muito Baixa", "Muito Baixa", "#BDBDBD", -2),
    (0.20, 0.40, "Baixa", "Baixa", "#E0E0E0", -1),
    (0.40, 0.60, "Moderada", "Moderada", "#FFE082", 0),
    (0.60, 0.80, "Alta", "Alta", "#81C784", 1),
    (0.80, 1.00, "Muito Alta", "Muito Alta", "#2E7D32", 2),
]


def classify_conviction(efficiency: float) -> ConvictionClassification:
    if efficiency < _EFFICIENCY_THRESHOLDS[0][0]:
        lo, hi, label, short, color, score = _EFFICIENCY_THRESHOLDS[0]
        return ConvictionClassification(label, short, color, score)
    if efficiency >= _EFFICIENCY_THRESHOLDS[-1][1]:
        lo, hi, label, short, color, score = _EFFICIENCY_THRESHOLDS[-1]
        return ConvictionClassification(label, short, color, score)
    for lo, hi, label, short, color, score in _EFFICIENCY_THRESHOLDS:
        if lo <= efficiency < hi:
            return ConvictionClassification(label, short, color, score)
    lo, hi, label, short, color, score = _EFFICIENCY_THRESHOLDS[-1]
    return ConvictionClassification(label, short, color, score)
