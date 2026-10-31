"""Cache em disco dos feriados por ano, com lock e escrita atômica."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from flowscope.application.calendar.config import CalendarConfig
from flowscope.application.calendar.ports import YearHolidays
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.calendar.cache_write import HolidayCacheWriteMixin
from flowscope.infrastructure.calendar.storage import SCHEMA_VERSION, decode_year

_LOCK_WAIT_SECONDS = 5.0


def calendar_cache_dir() -> Path:
    """Return the default calendar cache directory."""
    return CacheManager().get_cache_dir() / "calendar"


def default_calendar_lock_path() -> Path:
    """Return the dedicated calendar lock path."""
    return calendar_cache_dir() / "locks" / "calendar.lock"


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _as_utc(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc)


def _local_date(now: datetime | None) -> date:
    if now is None:
        return date.today()
    if now.tzinfo is None:
        return now.date()
    return now.astimezone().date()


class HolidayCache(HolidayCacheWriteMixin):
    """Stores one JSON file per year with TTL and provenance metadata."""

    def __init__(
        self: HolidayCache,
        cache_dir: str | Path | None = None,
        config: CalendarConfig | None = None,
    ) -> None:
        """Initialize the cache directory and TTL configuration."""
        self.cache_dir = Path(cache_dir) if cache_dir else calendar_cache_dir()
        self.config = config or CalendarConfig()
        self.holidays_dir = self.cache_dir / "holidays"
        self.lock_path = self.cache_dir / "locks" / "calendar.lock"

    def _local_date(self: HolidayCache) -> date:
        return _local_date(None)

    def path(self: HolidayCache, year: int) -> Path:
        """Return the JSON path of ``year``."""
        return self.holidays_dir / f"{year}.json"

    def read(self: HolidayCache, year: int) -> YearHolidays | None:
        """Read one year without creating or changing any file."""
        target = self.path(year)
        if not target.exists():
            return None
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return decode_year(data, year)

    def years(self: HolidayCache) -> list[int]:
        """Return years with valid, published holiday data."""
        if not self.holidays_dir.exists():
            return []
        years: list[int] = []
        for path in sorted(self.holidays_dir.glob("*.json")):
            try:
                year = int(path.stem)
            except ValueError:
                continue
            data = self.read(year)
            if data is not None and data.published and data.holidays:
                years.append(year)
        return sorted(years)

    def is_fresh(
        self: HolidayCache, year: int, now: datetime | None = None
    ) -> bool:
        """Return whether the cached year is inside its recency TTL."""
        data = self.read(year)
        if data is None:
            return False
        current_date = _local_date(now)
        if data.published and year < current_date.year:
            return True
        fetched = _parse_datetime(data.fetched_at)
        if fetched is None:
            return False
        current = _as_utc(now)
        return (current - fetched).total_seconds() < self._ttl(data, current_date)

    def _ttl(self: HolidayCache, data: YearHolidays, current: date) -> int:
        if data.ttl_seconds is not None:
            return data.ttl_seconds
        if data.published:
            return self._ttl_for(data.year, current)
        return self.config.ttl_negativo_segundos

    def _ttl_for(self: HolidayCache, year: int, current: date) -> int:
        if year > current.year:
            return self.config.ttl_futuro_segundos
        return self.config.ttl_corrente_segundos



__all__ = [
    "SCHEMA_VERSION",
    "HolidayCache",
    "calendar_cache_dir",
    "default_calendar_lock_path",
]
