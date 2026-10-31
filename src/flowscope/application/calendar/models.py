"""Modelos e formatação básica do calendário de aplicação."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

ESTADO_OK = "ok"
ESTADO_DEFASADO = "defasado"
ESTADO_INDISPONIVEL = "calendario_indisponivel"

_WEEKDAYS = ("seg", "ter", "qua", "qui", "sex", "sáb", "dom")


def weekday_abbreviation(value: date) -> str:
    """Return the Portuguese abbreviation of ``value``'s weekday."""
    return _WEEKDAYS[value.weekday()]


@dataclass(frozen=True)
class BusinessDayResolution:
    """Resultado estruturado da resolução de uma data."""

    data_solicitada: str
    data_resolvida: str
    ajustada: bool
    motivo: str | None
    feriado: str | None
    calendario_estado: str
    origem: str | None = None

    def as_dict(self: BusinessDayResolution) -> dict[str, object]:
        """Serialize the resolution for payloads."""
        return {
            "data_solicitada": self.data_solicitada,
            "data_resolvida": self.data_resolvida,
            "ajustada": self.ajustada,
            "motivo": self.motivo,
            "feriado": self.feriado,
            "calendario_estado": self.calendario_estado,
            "origem": self.origem,
        }


__all__ = [
    "ESTADO_DEFASADO",
    "ESTADO_INDISPONIVEL",
    "ESTADO_OK",
    "BusinessDayResolution",
    "weekday_abbreviation",
]
