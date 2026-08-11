"""Configuração de amostragem de dados do domínio."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SamplingConfig:
    """Configuração de amostragem por período e método."""

    period_days: int = 30
    method: str = "fibonacci"
