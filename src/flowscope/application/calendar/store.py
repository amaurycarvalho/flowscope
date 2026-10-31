"""Garantia, leitura e fallback do cache do calendário."""

from __future__ import annotations

from datetime import date, datetime, timezone

from flowscope.application.calendar.models import (
    ESTADO_DEFASADO,
    ESTADO_INDISPONIVEL,
    ESTADO_OK,
)
from flowscope.application.calendar.ports import (
    HolidayYearUnavailable,
    YearHolidays,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class CalendarStoreMixin:
    """Mixin com a leitura, gravação e fallback do calendário."""

    def ensure_year(self: CalendarStoreMixin, year: int, force: bool = False) -> str:
        """Ensure the calendar of ``year`` using cache, source and fallback."""
        if not force and self.repository.is_fresh(year):
            return self._load_cached(year)
        try:
            data = self.source.fetch_year(year)
        except HolidayYearUnavailable:
            return self._handle_unavailable(year)
        except Exception:
            return self._handle_failure(year)
        stored = self._store(data, reuse_fresh=not force)
        self._housekeep(year)
        return self._state_for_data(stored)

    def ensure_reference(self: CalendarStoreMixin, reference: date) -> str:
        """Ensure the reference year and, in early January, the prior year."""
        state = self.ensure_year(reference.year)
        if reference.month == 1 and reference.day <= 7:
            try:
                self.ensure_year(reference.year - 1)
            except Exception:
                pass
        return state

    def _store(
        self: CalendarStoreMixin,
        data: YearHolidays,
        reuse_fresh: bool = True,
    ) -> YearHolidays:
        try:
            stored = self.repository.write(data, reuse_fresh=reuse_fresh)
        except Exception:
            stored = self.repository.read(data.year)
        if stored is None:
            stored = data
        self._years[data.year] = stored
        self._states[data.year] = self._state_for_data(stored)
        return stored

    def _housekeep(self: CalendarStoreMixin, year: int) -> None:
        try:
            self.repository.housekeeping(self._today().year, (year,))
        except Exception:
            pass

    def _load_cached(self: CalendarStoreMixin, year: int) -> str:
        data = self.repository.read(year)
        if data is None:
            self._years[year] = None
            self._states[year] = ESTADO_INDISPONIVEL
            return ESTADO_INDISPONIVEL
        self._years[year] = data
        state = self._state_for_data(data)
        self._states[year] = state
        return state

    def _handle_unavailable(self: CalendarStoreMixin, year: int) -> str:
        if year > self._today().year:
            marker = self._negative_marker(year)
            try:
                stored = self.repository.write(marker)
            except Exception:
                stored = None
            self._years[year] = stored or marker
            self._states[year] = ESTADO_INDISPONIVEL
            return ESTADO_INDISPONIVEL
        return self._handle_failure(year)

    def _negative_marker(self: CalendarStoreMixin, year: int) -> YearHolidays:
        return YearHolidays(
            year=year,
            holidays=(),
            published=False,
            fetched_at=_now_iso(),
            ttl_seconds=self.config.ttl_negativo_segundos,
        )

    def _handle_failure(self: CalendarStoreMixin, year: int) -> str:
        previous = self.repository.read(year)
        if previous is not None and previous.published:
            self._years[year] = previous
            self._states[year] = ESTADO_DEFASADO
            return ESTADO_DEFASADO
        self._years[year] = None
        self._states[year] = ESTADO_INDISPONIVEL
        return ESTADO_INDISPONIVEL

    def _state_for_data(self: CalendarStoreMixin, data: YearHolidays) -> str:
        return ESTADO_OK if data.published else ESTADO_INDISPONIVEL

    def _data(self: CalendarStoreMixin, year: int) -> YearHolidays | None:
        if year in self._years:
            return self._years[year]
        data = self.repository.read(year)
        self._years[year] = data
        self._states[year] = (
            self._state_for_data(data) if data is not None else ESTADO_INDISPONIVEL
        )
        return data

    def _state_for(self: CalendarStoreMixin, year: int) -> str:
        self._data(year)
        return self._states.get(year, ESTADO_INDISPONIVEL)

    def cached_years(self: CalendarStoreMixin) -> list[int]:
        """Return the years available in the local cache."""
        return self.repository.years()


__all__ = ["CalendarStoreMixin"]
