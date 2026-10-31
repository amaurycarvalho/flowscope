"""Serviço de garantia do calendário e resolução de dias úteis."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from flowscope.application.calendar.config import CalendarConfig
from flowscope.application.calendar.models import (
    ESTADO_DEFASADO,
    ESTADO_INDISPONIVEL,
    ESTADO_OK,
    BusinessDayResolution,
)
from flowscope.application.calendar.ports import HolidayRepository, HolidaySource
from flowscope.application.calendar.report import (
    classify_payload,
    export_year,
    year_payload,
)
from flowscope.application.calendar.resolver import CalendarResolverMixin
from flowscope.application.calendar.store import CalendarStoreMixin


def _today() -> date:
    return date.today()


class CalendarService(CalendarStoreMixin, CalendarResolverMixin):
    """Garante o calendário por ano e resolve datas não úteis."""

    def __init__(
        self: CalendarService,
        source: HolidaySource,
        repository: HolidayRepository,
        config: CalendarConfig | None = None,
        today: Callable[[], date] | None = None,
    ) -> None:
        """Store the injected source, repository and configuration."""
        self.source = source
        self.repository = repository
        self.config = config or CalendarConfig()
        self._today = today or _today
        self._years: dict[int, object] = {}
        self._states: dict[int, str] = {}

    def listar_ano(self: CalendarService, year: int) -> dict[str, object]:
        """Return the stored year with metadata and ordered holidays."""
        return year_payload(year, self._data(year), self._state_for(year))

    def classificar(self: CalendarService, date_str: str) -> dict[str, object]:
        """Return whether ``date_str`` is a business day and the reason."""
        return classify_payload(self.resolve_business_day(date_str))

    def exportar_ano(self: CalendarService, year: int, formato: str) -> str:
        """Return the year as CSV or JSON content without writing files."""
        return export_year(self.listar_ano(year), formato)


__all__ = [
    "ESTADO_DEFASADO",
    "ESTADO_INDISPONIVEL",
    "ESTADO_OK",
    "BusinessDayResolution",
    "CalendarService",
]
