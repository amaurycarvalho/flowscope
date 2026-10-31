"""Modelos puros de calendário de feriados e dias úteis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

WEEKEND_DAYS = frozenset({5, 6})
ORIGEM_ANBIMA = "ANBIMA"
ORIGEM_RECESSO_B3 = "RECESSO_B3"


@dataclass(frozen=True)
class Holiday:
    """Um feriado em uma data específica, com a origem do dado."""

    date: date
    name: str
    source: str = ORIGEM_ANBIMA


@dataclass(frozen=True)
class HolidayCalendar:
    """Conjunto de feriados e regra de fim de semana."""

    holidays: tuple[Holiday, ...] = ()
    weekend: frozenset[int] = field(default_factory=lambda: WEEKEND_DAYS)

    def _holiday_map(self: HolidayCalendar) -> dict[date, Holiday]:
        return {holiday.date: holiday for holiday in self.holidays}

    def holiday_on(self: HolidayCalendar, value: date) -> Holiday | None:
        """Return the holiday on ``value``, or ``None``."""
        return self._holiday_map().get(value)

    def is_business_day(self: HolidayCalendar, value: date) -> bool:
        """Return whether ``value`` is a business day."""
        return (
            value.weekday() not in self.weekend
            and self.holiday_on(value) is None
        )

    def previous_business_day(self: HolidayCalendar, value: date) -> date:
        """Return ``value`` or the closest prior business day."""
        current = value
        while not self.is_business_day(current):
            current -= timedelta(days=1)
        return current

    def next_business_day(self: HolidayCalendar, value: date) -> date:
        """Return ``value`` or the closest later business day."""
        current = value
        while not self.is_business_day(current):
            current += timedelta(days=1)
        return current

    def business_days_between(
        self: HolidayCalendar, start: date, end: date
    ) -> int:
        """Return the number of business days in the inclusive interval."""
        if end < start:
            return 0
        total = 0
        current = start
        while current <= end:
            if self.is_business_day(current):
                total += 1
            current += timedelta(days=1)
        return total


__all__ = [
    "ORIGEM_ANBIMA",
    "ORIGEM_RECESSO_B3",
    "WEEKEND_DAYS",
    "Holiday",
    "HolidayCalendar",
]
