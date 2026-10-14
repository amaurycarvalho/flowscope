"""Calendário de negociação da B3: feriados nacionais e predicado de dia útil."""

from datetime import date

FERIADOS_NACIONAIS: frozenset[date] = frozenset({
    date(2026, 1, 1),
    date(2026, 2, 17),
    date(2026, 4, 3),
    date(2026, 4, 21),
    date(2026, 5, 1),
    date(2026, 6, 4),
    date(2026, 9, 7),
    date(2026, 10, 12),
    date(2026, 11, 2),
    date(2026, 11, 15),
    date(2026, 12, 25),
    date(2027, 1, 1),
    date(2027, 2, 7),
    date(2027, 2, 8),
    date(2027, 3, 26),
    date(2027, 4, 21),
    date(2027, 5, 1),
    date(2027, 6, 16),
    date(2027, 9, 7),
    date(2027, 10, 12),
    date(2027, 11, 2),
    date(2027, 11, 15),
    date(2027, 12, 25),
})


def is_business_day(d: date) -> bool:
    """Retorna True quando a data é um dia útil no calendário da B3."""
    return d.weekday() < 5 and d not in FERIADOS_NACIONAIS
