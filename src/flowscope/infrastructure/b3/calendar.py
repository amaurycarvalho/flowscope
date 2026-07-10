import random
from datetime import date, timedelta

from flowscope.domain.sampling import SamplingConfig

FIBONACCI_OFFSETS = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

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


def _next_weekday(d: date) -> date:
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def _fibs_up_to(limit: int) -> list[int]:
    return [f for f in FIBONACCI_OFFSETS if f <= limit]


def _fibonacci_dates(ref_date: date, period_days: int) -> list[date]:
    offsets = _fibs_up_to(period_days)
    return [ref_date - timedelta(days=o) for o in offsets]


def _fibonacci_reverse_dates(ref_date: date, period_days: int) -> list[date]:
    offsets = _fibs_up_to(period_days)
    max_offset = max(offsets)
    base = ref_date - timedelta(days=max_offset + 1)
    return [base + timedelta(days=o) for o in offsets]


def _fibonacci_double_dates(ref_date: date, period_days: int) -> list[date]:
    offsets = _fibs_up_to(period_days)
    max_offset = max(offsets)
    base = ref_date - timedelta(days=max_offset + 1)

    if period_days <= 30:
        double_offsets = [1, 2, 3, 13, 19, 20, 21]
    else:
        first_three = offsets[:3]
        last_three = offsets[-3:]
        middle = [13] if 13 not in first_three and 13 not in last_three else [offsets[len(offsets) // 2]]
        double_offsets = first_three + middle + last_three
        if len(double_offsets) > 7:
            double_offsets = double_offsets[:7]

    return [base + timedelta(days=o) for o in double_offsets]


def _monte_carlo_dates(ref_date: date, period_days: int, count: int) -> list[date]:
    first = ref_date - timedelta(days=period_days)
    last = ref_date - timedelta(days=1)
    dates = [first, last]
    available = list(date.fromordinal(d) for d in range(first.toordinal() + 1, last.toordinal()))
    if available:
        selected = random.sample(available, min(count, len(available)))
        dates.extend(selected)
    return dates


def _all_dates(ref_date: date, period_days: int) -> list[date]:
    first = ref_date - timedelta(days=period_days)
    return [first + timedelta(days=i) for i in range(period_days)]


def generate_dates(ref_date: date, config: SamplingConfig | None = None) -> list[date]:
    if config is None:
        config = SamplingConfig()

    period = config.period_days
    method = config.method

    if method == "fibonacci":
        return _fibonacci_dates(ref_date, period)
    elif method == "fibonacci_reverse":
        return _fibonacci_reverse_dates(ref_date, period)
    elif method == "fibonacci_double":
        return _fibonacci_double_dates(ref_date, period)
    elif method == "monte_carlo":
        return _monte_carlo_dates(ref_date, period, count=5)
    elif method == "monte_carlo_double":
        return _monte_carlo_dates(ref_date, period, count=12)
    elif method == "all_days":
        return _all_dates(ref_date, period)
    else:
        return _fibonacci_dates(ref_date, period)


def resolve_dates(
    ref_date: date,
    config: SamplingConfig | None = None,
    cache=None,
) -> list[date]:
    raw = generate_dates(ref_date, config)
    cfg = config or SamplingConfig()
    cache_only = cfg.period_days > 30

    resolved: list[date] = []
    for d in raw:
        bd = _next_business_day(d)
        if cache_only and cache is not None:
            nearest = cache.find_nearest(bd, max_deviation=7)
            if nearest is not None:
                resolved.append(nearest)
        else:
            resolved.append(bd)

    seen = set()
    return sorted(d for d in resolved if d not in seen and not seen.add(d))


def fibonacci_dates(ref_date: date) -> list[date]:
    dates = []
    for offset in FIBONACCI_OFFSETS[:7]:
        d = ref_date - timedelta(days=offset)
        d = _next_business_day(d)
        dates.append(d)
    return dates
