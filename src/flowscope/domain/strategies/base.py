from abc import ABC, abstractmethod
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay


class IndicatorStrategy(ABC):
    id: ClassVar[str]
    dependencies: ClassVar[list[str]] = []

    @abstractmethod
    def compute(
        self,
        trades: list[TradeDay],
        dep_results: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        ...
