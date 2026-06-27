from datetime import date, timedelta


def _next_weekday(d: date) -> date:
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


_FERIADOS_NACIONAIS = frozenset({
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


def _is_business_day(d: date) -> bool:
    return d.weekday() < 5 and d not in _FERIADOS_NACIONAIS


def _next_business_day(d: date) -> date:
    while not _is_business_day(d):
        d += timedelta(days=1)
    return d


FIBONACCI_OFFSETS = [1, 2, 3, 5, 8, 13, 21]


def fibonacci_dates(ref_date: date) -> list[date]:
    dates = []
    for offset in FIBONACCI_OFFSETS:
        d = ref_date - timedelta(days=offset)
        d = _next_business_day(d)
        dates.append(d)
    return dates
