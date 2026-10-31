"""Parsing e normalização do HTML de feriados da ANBIMA."""

from __future__ import annotations

import html
import re
import unicodedata
from datetime import date
from html.parser import HTMLParser

from flowscope.application.calendar.ports import (
    HolidaySourceError,
    HolidayYearUnavailable,
)
from flowscope.domain.calendar import ORIGEM_ANBIMA, ORIGEM_RECESSO_B3, Holiday

_DATE_PATTERN = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})$")
_TAG_PATTERN = re.compile(r"<[^>]+>")
_WEEKDAYS = {
    "segunda": 0,
    "segunda-feira": 0,
    "terca": 1,
    "terca-feira": 1,
    "quarta": 2,
    "quarta-feira": 2,
    "quinta": 3,
    "quinta-feira": 3,
    "sexta": 4,
    "sexta-feira": 4,
    "sabado": 5,
    "domingo": 6,
}
_B3_RECESSOS = {
    (12, 24): "Vespera de Natal",
    (12, 31): "Vespera de Ano-Novo",
}


class TableParser(HTMLParser):
    """Collect the text cells of each HTML table row."""

    def __init__(self: TableParser) -> None:
        """Initialize the parser state."""
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self: TableParser, tag: str, attrs: object) -> None:
        """Start a row or a table cell."""
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_data(self: TableParser, data: str) -> None:
        """Collect cell text."""
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self: TableParser, tag: str) -> None:
        """Finish a row or a table cell."""
        if tag in ("td", "th") and self._cell is not None:
            self._row.append("".join(self._cell))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None


def normalize_text(value: str) -> str:
    """Remove tags, HTML entities and accents, collapsing whitespace."""
    unescaped = html.unescape(_TAG_PATTERN.sub(" ", value))
    decomposed = unicodedata.normalize("NFKD", unescaped)
    ascii_only = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", ascii_only).strip()


def _parse_date(value: str, year: int) -> date:
    match = _DATE_PATTERN.match(value.strip())
    if match is None:
        raise HolidaySourceError(f"Data inválida: {value!r}.")
    day, month, raw_year = match.groups()
    parsed_year = int(raw_year)
    if len(raw_year) == 2:
        parsed_year += 2000
    try:
        parsed = date(parsed_year, int(month), int(day))
    except ValueError as exc:
        raise HolidaySourceError(f"Data inválida: {value!r}.") from exc
    if parsed.year != year:
        raise HolidaySourceError(
            f"Ano divergente na página de {year}: {value!r}."
        )
    return parsed


def _parse_weekday(value: str, parsed: date) -> None:
    weekday = _WEEKDAYS.get(normalize_text(value).lower())
    if weekday is None or weekday != parsed.weekday():
        raise HolidaySourceError(
            f"Dia da semana divergente para {parsed.isoformat()}."
        )


def _is_header(row: list[str]) -> bool:
    first = normalize_text(row[0]).lower() if row else ""
    return first in ("", "data")


def _rows_to_holidays(rows: list[list[str]], year: int) -> list[Holiday]:
    holidays: list[Holiday] = []
    for row in rows:
        if len(row) < 3 or _is_header(row):
            continue
        parsed = _parse_date(row[0], year)
        _parse_weekday(row[1], parsed)
        name = normalize_text(row[2])
        if not name:
            raise HolidaySourceError("Feriado sem nome.")
        holidays.append(Holiday(parsed, name, ORIGEM_ANBIMA))
    if not holidays:
        raise HolidayYearUnavailable(f"Página sem feriados para {year}.")
    return holidays


def _add_recessos(holidays: list[Holiday], year: int) -> None:
    existing = {holiday.date for holiday in holidays}
    for (month, day), name in _B3_RECESSOS.items():
        try:
            parsed = date(year, month, day)
        except ValueError:
            continue
        if parsed.weekday() >= 5 or parsed in existing:
            continue
        holidays.append(Holiday(parsed, name, ORIGEM_RECESSO_B3))
        existing.add(parsed)


def parse_page(raw: bytes, year: int) -> list[Holiday]:
    """Decode and validate a complete ANBIMA page, never partially."""
    try:
        text = raw.decode("iso-8859-1")
    except UnicodeDecodeError as exc:
        raise HolidaySourceError("HTML inválido na ANBIMA.") from exc
    parser = TableParser()
    try:
        parser.feed(text)
        parser.close()
    except HolidaySourceError:
        raise
    except Exception as exc:
        raise HolidaySourceError("HTML inválido na ANBIMA.") from exc
    holidays = _rows_to_holidays(parser.rows, year)
    _add_recessos(holidays, year)
    holidays.sort(key=lambda holiday: holiday.date)
    return holidays


__all__ = ["TableParser", "normalize_text", "parse_page"]
