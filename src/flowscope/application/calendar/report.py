"""Formatação de consultas e exportações do calendário."""

from __future__ import annotations

import json

from flowscope.application.calendar.models import (
    BusinessDayResolution,
    weekday_abbreviation,
)
from flowscope.application.calendar.ports import YearHolidays
from flowscope.domain.calendar import Holiday


def _holiday_payload(holiday: Holiday) -> dict[str, object]:
    return {
        "data": holiday.date.isoformat(),
        "dia_semana": weekday_abbreviation(holiday.date),
        "nome": holiday.name,
        "origem": holiday.source,
    }


def year_payload(
    year: int, data: YearHolidays | None, state: str
) -> dict[str, object]:
    """Build the public year payload with metadata and ordered holidays."""
    payload: dict[str, object] = {
        "ano": year,
        "estado": state,
        "origem": data.source if data is not None else None,
        "url": data.source_url if data is not None else "",
        "extraido_em": data.fetched_at if data is not None else "",
        "publicado": bool(data is not None and data.published),
        "feriados": [],
    }
    if data is not None and data.published:
        payload["feriados"] = [
            _holiday_payload(holiday) for holiday in data.holidays
        ]
    return payload


def classify_payload(resolution: BusinessDayResolution) -> dict[str, object]:
    """Build the public classification payload."""
    payload = resolution.as_dict()
    payload["dia_util"] = not resolution.ajustada
    return payload


def export_year(payload: dict[str, object], formato: str) -> str:
    """Return the year as CSV or JSON content without writing files."""
    if formato == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2)
    if formato == "csv":
        return _as_csv(payload)
    raise ValueError(f"Formato inválido: {formato!r}.")


def _as_csv(payload: dict[str, object]) -> str:
    lines = ["data;dia_semana;nome;origem"]
    for item in payload.get("feriados", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            ";".join(
                str(item.get(key, ""))
                for key in ("data", "dia_semana", "nome", "origem")
            )
        )
    return "\n".join(lines) + "\n"


__all__ = ["classify_payload", "export_year", "year_payload"]
