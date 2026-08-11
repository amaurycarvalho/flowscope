"""Geradores de datas de amostragem usados pelo calendário da B3."""

import random
from datetime import date, timedelta

FIBONACCI_OFFSETS = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]


def _fibs_up_to(limit: int) -> list[int]:
    """Filtra os offsets de Fibonacci que cabem dentro do período informado."""
    return [f for f in FIBONACCI_OFFSETS if f <= limit]


def _fibonacci_dates(ref_date: date, period_days: int) -> list[date]:
    """Retorna as datas recuadas da referência conforme os offsets de Fibonacci."""
    offsets = _fibs_up_to(period_days)
    return [ref_date - timedelta(days=o) for o in offsets]


def _fibonacci_reverse_dates(ref_date: date, period_days: int) -> list[date]:
    """Retorna as datas de Fibonacci partindo de uma base imediatamente anterior."""
    offsets = _fibs_up_to(period_days)
    max_offset = max(offsets)
    base = ref_date - timedelta(days=max_offset + 1)
    return [base + timedelta(days=o) for o in offsets]


def _fibonacci_double_dates(ref_date: date, period_days: int) -> list[date]:
    """Gera datas de Fibonacci com densidade dobrada na janela do período."""
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
    """Seleciona datas aleatórias na janela, incluindo o primeiro e o último dia."""
    first = ref_date - timedelta(days=period_days)
    last = ref_date - timedelta(days=1)
    dates = [first, last]
    available = [date.fromordinal(d) for d in range(first.toordinal() + 1, last.toordinal())]
    if available:
        selected = random.sample(available, min(count, len(available)))
        dates.extend(selected)
    return dates


def _all_dates(ref_date: date, period_days: int) -> list[date]:
    """Gera todos os dias da janela a partir da data de referência."""
    first = ref_date - timedelta(days=period_days)
    return [first + timedelta(days=i) for i in range(period_days)]
