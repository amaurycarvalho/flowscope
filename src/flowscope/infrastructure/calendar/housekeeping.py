"""Housekeeping do cache de feriados por ano."""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

RETENCAO_ANOS = 3
RETENCAO_FUTURA = 1

logger = logging.getLogger(__name__)


def is_retained(
    year: int,
    reference_year: int,
    years_before: int = RETENCAO_ANOS,
    years_after: int = RETENCAO_FUTURA,
) -> bool:
    """Return whether ``year`` is inside the retention window."""
    return reference_year - years_before <= year <= reference_year + years_after


def _valid_year(scratched: Path) -> int | None:
    try:
        year = int(scratched.stem)
    except (TypeError, ValueError):
        return None
    return year if year > 0 else None


def _is_readable(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return isinstance(data, dict)


def run_housekeeping(
    holidays_dir: Path,
    reference_year: int | None = None,
    protected_years: tuple[int, ...] = (),
) -> list[int]:
    """Remove cached years outside ``[reference - 3, reference + 1]``."""
    reference = reference_year or date.today().year
    protected = set(protected_years)
    removed: list[int] = []
    if not holidays_dir.exists():
        return removed
    for path in sorted(holidays_dir.glob("*.json")):
        year = _valid_year(path)
        if year is None or year in protected:
            continue
        if is_retained(year, reference):
            continue
        if not _is_readable(path):
            logger.warning("Ignorando arquivo de calendário corrompido: %s", path)
            continue
        try:
            path.unlink()
            removed.append(year)
        except OSError:
            logger.warning("Não foi possível remover %s.", path)
    return removed


__all__ = [
    "RETENCAO_ANOS",
    "RETENCAO_FUTURA",
    "is_retained",
    "run_housekeeping",
]
