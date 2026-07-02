from dataclasses import dataclass


@dataclass(frozen=True)
class MoneyFlowClassification:
    label: str
    short_label: str
    color: str
    score: int


_MFV_THRESHOLDS = [
    (float("-inf"), -0.15, "Fluxo Muito Forte (Vendedor)", "Muito Forte", "#B71C1C", -4),
    (-0.15, -0.08, "Fluxo Forte (Vendedor)", "Forte", "#D32F2F", -3),
    (-0.08, -0.03, "Fluxo Moderado (Vendedor)", "Moderada", "#EF9A9A", -2),
    (-0.03, -0.01, "Fluxo Fraco (Vendedor)", "Fraca", "#FFCDD2", -1),
    (-0.01, +0.01, "Neutro", "Neutro", "#BDBDBD", 0),
    (+0.01, +0.03, "Fluxo Fraco (Comprador)", "Fraca", "#C8E6C9", 1),
    (+0.03, +0.08, "Fluxo Moderado (Comprador)", "Moderada", "#A5D6A7", 2),
    (+0.08, +0.15, "Fluxo Forte (Comprador)", "Forte", "#388E3C", 3),
    (+0.15, float("inf"), "Fluxo Muito Forte (Comprador)", "Muito Forte", "#1B5E20", 4),
]


def classify_money_flow(score: float) -> MoneyFlowClassification:
    for lo, hi, label, short, color, level in _MFV_THRESHOLDS:
        if lo <= score < hi:
            return MoneyFlowClassification(label, short, color, level)
    lo, hi, label, short, color, level = _MFV_THRESHOLDS[-1]
    return MoneyFlowClassification(label, short, color, level)
