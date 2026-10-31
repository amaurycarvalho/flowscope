"""Resolução de datas contra o calendário combinado."""

from __future__ import annotations

from datetime import date

from flowscope.application.calendar.models import BusinessDayResolution
from flowscope.domain.calendar import Holiday, HolidayCalendar


class CalendarResolverMixin:
    """Mixin com a resolução de datas e o calendário combinado."""

    def resolve_reference(
        self: CalendarResolverMixin, reference: date
    ) -> BusinessDayResolution:
        """Ensure the calendar and resolve ``reference`` to a business day."""
        self.ensure_reference(reference)
        return self.resolve_business_day(reference.isoformat())

    def _calendar(self: CalendarResolverMixin, year: int) -> HolidayCalendar:
        holidays: list[Holiday] = []
        for candidate in (year - 1, year, year + 1):
            data = self._data(candidate)
            if data is not None and data.published:
                holidays.extend(data.holidays)
        return HolidayCalendar(holidays=tuple(holidays))

    def calendar_for(self: CalendarResolverMixin, year: int) -> HolidayCalendar:
        """Return the combined calendar around ``year`` without network."""
        return self._calendar(year)

    def resolve_business_day(
        self: CalendarResolverMixin, date_str: str
    ) -> BusinessDayResolution:
        """Resolve ``date_str`` to the previous business day when needed."""
        requested = date.fromisoformat(date_str)
        calendar = self._calendar(requested.year)
        if calendar.is_business_day(requested):
            return self._resolution(
                date_str, date_str, False, None, None,
                self._state_for(requested.year),
            )
        motivo = (
            "fim_de_semana"
            if requested.weekday() in calendar.weekend
            else "feriado"
        )
        holiday = calendar.holiday_on(requested)
        resolved = calendar.previous_business_day(requested)
        return self._resolution(
            date_str,
            resolved.isoformat(),
            True,
            motivo,
            holiday,
            self._state_for(requested.year),
        )

    @staticmethod
    def _resolution(
        date_str: str,
        resolved: str,
        adjusted: bool,
        motivo: str | None,
        holiday: Holiday | None,
        state: str,
    ) -> BusinessDayResolution:
        return BusinessDayResolution(
            data_solicitada=date_str,
            data_resolvida=resolved,
            ajustada=adjusted,
            motivo=motivo,
            feriado=holiday.name if holiday is not None else None,
            calendario_estado=state,
            origem=holiday.source if holiday is not None else None,
        )


__all__ = ["CalendarResolverMixin"]
