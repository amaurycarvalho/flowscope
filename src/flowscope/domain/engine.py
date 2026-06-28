from collections import defaultdict, deque
from typing import Any

from flowscope.domain.entities import TradeDay
from flowscope.domain.strategies.base import IndicatorStrategy


class IndicatorEngine:
    def __init__(self):
        self._registry: dict[str, IndicatorStrategy] = {}

    def register(self, *strategies: IndicatorStrategy) -> None:
        for s in strategies:
            if s.id in self._registry:
                raise ValueError(f"Indicator '{s.id}' already registered")
            self._registry[s.id] = s

    def execute(
        self, trades: list[TradeDay]
    ) -> dict[str, dict[str, Any]]:
        if not self._registry:
            return {}

        order = self._resolve_order()
        cache: dict[str, dict[str, Any]] = {}

        for indicator_id in order:
            strategy = self._registry[indicator_id]
            deps = {
                dep_id: cache[dep_id]
                for dep_id in strategy.dependencies
            }
            result = strategy.compute(trades, deps)
            cache[indicator_id] = result

        return cache

    def _resolve_order(self) -> list[str]:
        dependents: dict[str, set[str]] = defaultdict(set)
        in_degree: dict[str, int] = {}

        for sid, strategy in self._registry.items():
            in_degree.setdefault(sid, 0)
            for dep_id in strategy.dependencies:
                if dep_id not in self._registry:
                    raise ValueError(
                        f"Indicator '{sid}' depends on unknown '{dep_id}'"
                    )
                dependents[dep_id].add(sid)
                in_degree[sid] = in_degree.get(sid, 0) + 1

        queue = deque([n for n, deg in in_degree.items() if deg == 0])
        order = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for dependent in dependents.get(node, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(order) != len(self._registry):
            raise ValueError("Circular dependency detected among indicators")

        return order
