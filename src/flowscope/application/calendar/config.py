"""Configuração headless do calendário de feriados."""

from __future__ import annotations

from dataclasses import dataclass

TTL_CORRENTE_SEGUNDOS = 24 * 60 * 60
TTL_FUTURO_SEGUNDOS = 24 * 60 * 60
TTL_NEGATIVO_SEGUNDOS = 6 * 60 * 60
RETENCAO_ANOS = 3
SOBREPOSICAO_DIAS = 5
FONTE_TIMEOUT_SEGUNDOS = 15


@dataclass(frozen=True)
class CalendarConfig:
    """TTLs, retenção e sobreposição do calendário."""

    ttl_corrente_segundos: int = TTL_CORRENTE_SEGUNDOS
    ttl_futuro_segundos: int = TTL_FUTURO_SEGUNDOS
    ttl_negativo_segundos: int = TTL_NEGATIVO_SEGUNDOS
    retencao_anos: int = RETENCAO_ANOS
    sobreposicao_dias: int = SOBREPOSICAO_DIAS
    fonte_timeout_segundos: int = FONTE_TIMEOUT_SEGUNDOS

    @classmethod
    def from_mapping(
        cls: type[CalendarConfig], data: dict | None = None
    ) -> CalendarConfig:
        """Build the configuration from a plain mapping with defaults."""
        values = data or {}
        return cls(
            ttl_corrente_segundos=int(
                values.get(
                    "ttl_corrente_segundos", TTL_CORRENTE_SEGUNDOS
                )
            ),
            ttl_futuro_segundos=int(
                values.get("ttl_futuro_segundos", TTL_FUTURO_SEGUNDOS)
            ),
            ttl_negativo_segundos=int(
                values.get("ttl_negativo_segundos", TTL_NEGATIVO_SEGUNDOS)
            ),
            retencao_anos=int(values.get("retencao_anos", RETENCAO_ANOS)),
            sobreposicao_dias=int(
                values.get("sobreposicao_dias", SOBREPOSICAO_DIAS)
            ),
            fonte_timeout_segundos=int(
                values.get(
                    "fonte_timeout_segundos", FONTE_TIMEOUT_SEGUNDOS
                )
            ),
        )


__all__ = [
    "FONTE_TIMEOUT_SEGUNDOS",
    "RETENCAO_ANOS",
    "SOBREPOSICAO_DIAS",
    "TTL_CORRENTE_SEGUNDOS",
    "TTL_FUTURO_SEGUNDOS",
    "TTL_NEGATIVO_SEGUNDOS",
    "CalendarConfig",
]
