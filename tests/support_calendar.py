"""Apoio de testes para calendários de dia útil sem I/O."""

from __future__ import annotations

from datetime import date

from flowscope.domain.calendar import Holiday, HolidayCalendar


class FakeBusinessDayLookup:
    """Lookup em memória com feriados explícitos."""

    def __init__(self: "FakeBusinessDayLookup", holidays: list[date]) -> None:
        """Store the holiday dates used by the fake calendar."""
        self._calendar = HolidayCalendar(
            holidays=tuple(Holiday(item, "Feriado") for item in holidays)
        )

    def calendar_for(self: "FakeBusinessDayLookup", year: int) -> HolidayCalendar:
        """Return the in-memory calendar."""
        return self._calendar

    def is_business_day(self: "FakeBusinessDayLookup", value: date) -> bool:
        """Return whether ``value`` is a business day in the fake calendar."""
        return self._calendar.is_business_day(value)
