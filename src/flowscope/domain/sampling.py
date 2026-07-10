from dataclasses import dataclass


@dataclass(frozen=True)
class SamplingConfig:
    period_days: int = 30
    method: str = "fibonacci"
