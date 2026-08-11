"""Geração de datas de amostragem e resolução de dias úteis para a B3."""

from collections.abc import Callable
from datetime import date, timedelta

from flowscope.domain.sampling import SamplingConfig
from flowscope.infrastructure.b3.generators import (
    FIBONACCI_OFFSETS,
    _all_dates,
    _fibonacci_dates,
    _fibonacci_double_dates,
    _fibonacci_reverse_dates,
    _monte_carlo_dates,
)
from flowscope.infrastructure.b3.holidays import (
    FERIADOS_NACIONAIS as _FERIADOS_NACIONAIS,
)


def _is_business_day(d: date) -> bool:
    """Retorna True quando a data é um dia útil no calendário da B3."""
    return d.weekday() < 5 and d not in _FERIADOS_NACIONAIS


def _next_business_day(d: date) -> date:
    """Avança a data até o próximo dia útil."""
    while not _is_business_day(d):
        d += timedelta(days=1)
    return d


def _next_weekday(d: date) -> date:
    """Avança a data até o próximo dia da semana."""
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def _monte_carlo_five(ref_date: date, period_days: int) -> list[date]:
    """Gera cinco datas aleatórias na janela do período."""
    return _monte_carlo_dates(ref_date, period_days, count=5)


def _monte_carlo_twelve(ref_date: date, period_days: int) -> list[date]:
    """Gera doze datas aleatórias na janela do período."""
    return _monte_carlo_dates(ref_date, period_days, count=12)


_GENERATORS = {
    "fibonacci": _fibonacci_dates,
    "fibonacci_reverse": _fibonacci_reverse_dates,
    "fibonacci_double": _fibonacci_double_dates,
    "monte_carlo": _monte_carlo_five,
    "monte_carlo_double": _monte_carlo_twelve,
    "all_days": _all_dates,
}


def generate_dates(ref_date: date, config: SamplingConfig | None = None) -> list[date]:
    """Gera as datas de amostragem conforme o método e o período da configuração."""
    if config is None:
        config = SamplingConfig()

    generator = _GENERATORS.get(config.method)
    if generator is None:
        generator = _fibonacci_dates
    return generator(ref_date, config.period_days)


def _find_nearest_with_data(
    date: date, has_data: Callable[[date], bool] | None, already_selected: set[date], max_deviation: int = 7,
    max_date: date | None = None,
) -> date | None:
    """Procura a data útil mais próxima que possua dados disponíveis.

    Nunca retorna datas posteriores a ``max_date`` (a data de referência),
    evitando que o sistema consulte datas futuras na B3.
    """
    for delta in range(max_deviation + 1):
        candidate = date - timedelta(days=delta)
        if (candidate not in already_selected
                and (max_date is None or candidate <= max_date)
                and _is_business_day(candidate)
                and has_data(candidate)):
            return candidate
        if delta > 0:
            candidate = date + timedelta(days=delta)
            if (candidate not in already_selected
                    and (max_date is None or candidate <= max_date)
                    and _is_business_day(candidate)
                    and has_data(candidate)):
                return candidate
    return None


def _resolve_with_data(
    raw_dates: list[date], has_data: Callable[[date], bool] | None, max_deviation: int = 7,
    max_date: date | None = None,
) -> list[date]:
    """Resolve as datas brutas para dias úteis com dados, eliminando duplicados."""
    resolved: list[date] = []
    seen: set[date] = set()
    for d in raw_dates:
        bd = _next_business_day(d)
        if has_data is not None:
            data_date = _find_nearest_with_data(bd, has_data, seen, max_deviation, max_date)
            if data_date is None:
                continue
            if data_date not in seen:
                resolved.append(data_date)
                seen.add(data_date)
        else:
            if bd not in seen:
                resolved.append(bd)
                seen.add(bd)
    return sorted(resolved)


def resolve_dates(
    ref_date: date,
    config: SamplingConfig | None = None,
    has_data: Callable[[date], bool] | None = None,
) -> list[date]:
    """Resolve as datas geradas para dias úteis, aproximando quando houver dados disponíveis."""
    raw = generate_dates(ref_date, config)
    return _resolve_with_data(raw, has_data, max_date=ref_date) if has_data is not None else sorted(
        _next_business_day(d) for d in {_next_business_day(d)
                                         for d in raw}
    )


def fibonacci_dates(ref_date: date, has_data: Callable[[date], bool] | None = None) -> list[date]:
    """Retorna as datas de amostragem da sequência de Fibonacci a partir da data de referência."""
    raw = [ref_date - timedelta(days=o) for o in FIBONACCI_OFFSETS[:7]]
    if has_data is not None:
        return _resolve_with_data(raw, has_data, max_date=ref_date)
    dates = []
    seen = set()
    for d in raw:
        bd = _next_business_day(d)
        if bd not in seen:
            dates.append(bd)
            seen.add(bd)
    return dates
