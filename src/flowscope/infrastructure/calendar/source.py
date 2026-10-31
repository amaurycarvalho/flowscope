"""Fonte HTML da ANBIMA para os feriados nacionais de cada ano."""

from __future__ import annotations

import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone

from flowscope.application.calendar.ports import (
    HolidaySourceError,
    HolidayYearUnavailable,
    YearHolidays,
)
from flowscope.infrastructure.calendar.source_parser import (
    normalize_text,
    parse_page,
)

BASE_URL = "https://www.anbima.com.br/"
_URL_TEMPLATE = BASE_URL + "feriados/fer_nacionais/{year}.asp"


def source_url(year: int) -> str:
    """Return the ANBIMA URL for ``year``."""
    return _URL_TEMPLATE.format(year=year)


def _open_page(
    opener: Callable[..., object], url: str, timeout: int
) -> bytes:
    try:
        with opener(url, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise HolidayYearUnavailable(url) from exc
        raise HolidaySourceError(str(exc)) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise HolidaySourceError(str(exc)) from exc


class AnbimaHolidaySource:
    """Fetch and normalize the ANBIMA national holiday page."""

    def __init__(
        self: AnbimaHolidaySource,
        opener: Callable[..., object] | None = None,
        timeout: int = 15,
    ) -> None:
        """Initialize the source with an injectable opener and timeout."""
        self._opener = opener or urllib.request.urlopen
        self._timeout = timeout

    def fetch_year(self: AnbimaHolidaySource, year: int) -> YearHolidays:
        """Fetch and normalize every holiday of ``year``."""
        url = source_url(year)
        raw = _open_page(self._opener, url, self._timeout)
        holidays = parse_page(raw, year)
        return YearHolidays(
            year=year,
            holidays=tuple(holidays),
            source="ANBIMA",
            source_url=url,
            fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )


__all__ = [
    "BASE_URL",
    "AnbimaHolidaySource",
    "normalize_text",
    "source_url",
]
