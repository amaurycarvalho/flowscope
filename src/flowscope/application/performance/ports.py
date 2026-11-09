"""Portas da camada de aplicação para o cache de performance."""

from typing import Protocol

from flowscope.application.performance.modelos import PerformanceCacheKey


class PerformanceCache(Protocol):
    """Contrato do cache pré-calculado dos resultados de performance."""

    def obter(
        self: "PerformanceCache", chave: PerformanceCacheKey
    ) -> dict | None:
        """Retorna o resultado em cache, ou ``None`` quando ausente/corrompido."""
        ...

    def registrar(
        self: "PerformanceCache",
        chave: PerformanceCacheKey,
        resultado: dict,
    ) -> None:
        """Grava o resultado do benchmark de forma atômica."""
        ...
