"""Adaptador somente-leitura de dia útil sobre o cache do calendário."""

from __future__ import annotations

from datetime import date

from flowscope.application.calendar.service import CalendarService
from flowscope.domain.calendar import HolidayCalendar


class CachedBusinessDayLookup:
    """Resolve dias úteis lendo apenas o cache compartilhado do calendário."""

    def __init__(
        self: CachedBusinessDayLookup, service: CalendarService
    ) -> None:
        """Store the calendar service used as read-only source."""
        self._service = service

    def calendar_for(
        self: CachedBusinessDayLookup, year: int
    ) -> HolidayCalendar:
        """Return the cached calendar around ``year``."""
        return self._service.calendar_for(year)

    def is_business_day(self: CachedBusinessDayLookup, value: date) -> bool:
        """Return whether ``value`` is a business day in the cached calendar."""
        return self._service.calendar_for(value.year).is_business_day(value)


__all__ = ["CachedBusinessDayLookup"]
