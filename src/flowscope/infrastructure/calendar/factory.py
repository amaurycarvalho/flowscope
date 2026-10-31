"""Composição dos adaptadores do calendário de feriados."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from flowscope.application.calendar.config import CalendarConfig
from flowscope.application.calendar.service import CalendarService
from flowscope.infrastructure.calendar.cache import HolidayCache
from flowscope.infrastructure.calendar.lookup import CachedBusinessDayLookup
from flowscope.infrastructure.calendar.source import AnbimaHolidaySource


@dataclass
class CalendarServices:
    """Cache, fonte, serviço e lookup compartilhados por GUI, CLI e MCP."""

    config: CalendarConfig
    cache: HolidayCache
    source: AnbimaHolidaySource
    service: CalendarService
    lookup: CachedBusinessDayLookup


def build_calendar_services(
    cache_dir: str | Path | None = None,
    config: CalendarConfig | None = None,
) -> CalendarServices:
    """Build the calendar adapters without touching the network."""
    calendar_config = config or CalendarConfig()
    cache = HolidayCache(cache_dir, calendar_config)
    source = AnbimaHolidaySource(timeout=calendar_config.fonte_timeout_segundos)
    service = CalendarService(source, cache, calendar_config)
    return CalendarServices(
        config=calendar_config,
        cache=cache,
        source=source,
        service=service,
        lookup=CachedBusinessDayLookup(service),
    )


__all__ = ["CalendarServices", "build_calendar_services"]
