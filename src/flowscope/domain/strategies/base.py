"""Interface base das estratégias de indicadores."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from flowscope.domain.entities import TradeDay


class IndicatorStrategy(ABC):
    """Estratégia de indicador com identificador e dependências."""

    id: ClassVar[str]
    dependencies: ClassVar[list[str]] = []

    @abstractmethod
    def compute(
        self: "IndicatorStrategy",
        trades: list[TradeDay],
        dep_results: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Calcula o indicador a partir dos trades e dos resultados de dependências."""
        ...
