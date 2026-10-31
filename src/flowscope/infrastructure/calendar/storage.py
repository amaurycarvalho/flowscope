"""Codificação e decodificação dos payloads do cache de feriados."""

from __future__ import annotations

from datetime import datetime

from flowscope.application.calendar.ports import YearHolidays
from flowscope.domain.calendar import ORIGEM_ANBIMA, Holiday

SCHEMA_VERSION = 2


def _parse_holidays(raw: object) -> tuple[Holiday, ...] | None:
    if not isinstance(raw, list):
        return None
    holidays: list[Holiday] = []
    try:
        for item in raw:
            if not isinstance(item, dict):
                return None
            holidays.append(
                Holiday(
                    date=datetime.fromisoformat(str(item["date"])).date(),
                    name=str(item["name"]),
                    source=str(item.get("source", ORIGEM_ANBIMA)),
                )
            )
    except (KeyError, TypeError, ValueError):
        return None
    return tuple(holidays)


def decode_year(data: object, year: int) -> YearHolidays | None:
    """Decode one cached payload, returning ``None`` when invalid."""
    if not isinstance(data, dict):
        return None
    if data.get("schema_version") != SCHEMA_VERSION:
        return None
    if data.get("year") != year:
        return None
    holidays = _parse_holidays(data.get("holidays"))
    if holidays is None:
        return None
    published = data.get("published", True)
    if not isinstance(published, bool):
        return None
    ttl = data.get("ttl_seconds")
    return YearHolidays(
        year=year,
        holidays=holidays,
        source=str(data.get("source", "ANBIMA")),
        source_url=str(data.get("source_url", "")),
        fetched_at=str(data.get("fetched_at", "")),
        ttl_seconds=ttl if isinstance(ttl, int) else None,
        published=published,
    )


def encode_year(data: YearHolidays, ttl: int | None) -> dict[str, object]:
    """Encode one year into the persisted JSON payload."""
    return {
        "schema_version": SCHEMA_VERSION,
        "year": data.year,
        "source": data.source,
        "source_url": data.source_url,
        "fetched_at": data.fetched_at,
        "ttl_seconds": ttl,
        "published": data.published,
        "holidays": [
            {
                "date": holiday.date.isoformat(),
                "weekday": holiday.date.weekday(),
                "name": holiday.name,
                "source": holiday.source,
            }
            for holiday in data.holidays
        ],
    }


__all__ = ["SCHEMA_VERSION", "decode_year", "encode_year"]
