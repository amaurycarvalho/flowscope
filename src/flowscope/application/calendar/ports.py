"""Portas e modelos da camada de aplicação para o calendário."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from flowscope.domain.calendar import (
    WEEKEND_DAYS,
    Holiday,
    HolidayCalendar,
)


class HolidaySourceError(RuntimeError):
    """Falha ao obter o calendário de feriados da fonte."""


class HolidayYearUnavailable(HolidaySourceError):
    """O ano ainda não foi publicado pela fonte."""


@dataclass(frozen=True)
class YearHolidays:
    """Feriados de um ano com os metadados de origem."""

    year: int
    holidays: tuple[Holiday, ...]
    source: str = "ANBIMA"
    source_url: str = ""
    fetched_at: str = ""
    ttl_seconds: int | None = None
    published: bool = True
    stale: bool = False

    def to_calendar(self: YearHolidays) -> HolidayCalendar:
        """Return a pure calendar with this year's holidays."""
        return HolidayCalendar(holidays=self.holidays)


class HolidaySource(Protocol):
    """Fonte externa de feriados por ano."""

    def fetch_year(self: HolidaySource, year: int) -> YearHolidays:
        """Fetch the holidays of ``year`` or raise a source error."""


class HolidayRepository(Protocol):
    """Repositório local de feriados por ano."""

    def read(self: HolidayRepository, year: int) -> YearHolidays | None:
        """Read one year without modifying anything."""

    def years(self: HolidayRepository) -> list[int]:
        """Return the years available in the cache."""

    def is_fresh(
        self: HolidayRepository,
        year: int,
        now: datetime | None = None,
    ) -> bool:
        """Return whether the cached year is inside its TTL."""

    def write(
        self: HolidayRepository,
        data: YearHolidays,
        reuse_fresh: bool = True,
    ) -> YearHolidays | None:
        """Write one year atomically under the dedicated lock."""

    def housekeeping(
        self: HolidayRepository,
        reference_year: int,
        protected_years: tuple[int, ...] = (),
    ) -> None:
        """Remove cached years outside the retention window."""


class BusinessDayLookup(Protocol):
    """Consulta somente-leitura do calendário de dias úteis."""

    def calendar_for(
        self: BusinessDayLookup, year: int
    ) -> HolidayCalendar:
        """Return the cached calendar around ``year`` without network."""

    def is_business_day(
        self: BusinessDayLookup, value: date
    ) -> bool:
        """Return whether ``value`` is a business day."""


class WeekendBusinessDayLookup:
    """Fallback puro que considera não úteis apenas sábado e domingo."""

    def calendar_for(
        self: WeekendBusinessDayLookup, year: int
    ) -> HolidayCalendar:
        """Return an empty calendar, preserving only the weekend rule."""
        return HolidayCalendar()

    def is_business_day(
        self: WeekendBusinessDayLookup, value: date
    ) -> bool:
        """Return whether ``value`` is a weekday."""
        return value.weekday() not in WEEKEND_DAYS


__all__ = [
    "BusinessDayLookup",
    "HolidayRepository",
    "HolidaySource",
    "HolidaySourceError",
    "HolidayYearUnavailable",
    "WeekendBusinessDayLookup",
    "YearHolidays",
]
