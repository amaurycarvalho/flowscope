"""Subpacote com as classificações dos indicadores do FlowScope."""

from flowscope.domain.strategies.classifiers.conviction import (
    ConvictionClassification,
    classify_conviction,
)
from flowscope.domain.strategies.classifiers.dominance import (
    DominanceClassification,
    classify_dominance,
)
from flowscope.domain.strategies.classifiers.money_flow import (
    MoneyFlowClassification,
    classify_money_flow,
)
from flowscope.domain.strategies.classifiers.quadrant import (
    QUADRANTES,
    classify_quadrant,
)

__all__ = [
    "QUADRANTES",
    "ConvictionClassification",
    "DominanceClassification",
    "MoneyFlowClassification",
    "classify_conviction",
    "classify_dominance",
    "classify_money_flow",
    "classify_quadrant",
]
