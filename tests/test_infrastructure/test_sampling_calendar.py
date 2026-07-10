from datetime import date
from unittest.mock import MagicMock

import pytest

from flowscope.domain.sampling import SamplingConfig
from flowscope.infrastructure.b3.calendar import (
    generate_dates,
    resolve_dates,
    fibonacci_dates,
)


class TestGenerateDates:
    def test_fibonacci_30(self):
        ref = date(2026, 7, 10)
        config = SamplingConfig(period_days=30, method="fibonacci")
        dates = generate_dates(ref, config)
        expected = [date(2026, 7, 9), date(2026, 7, 8), date(2026, 7, 7),
                    date(2026, 7, 5), date(2026, 7, 2), date(2026, 6, 27),
                    date(2026, 6, 19)]
        assert dates == expected

    def test_fibonacci_60(self):
        ref = date(2026, 7, 10)
        config = SamplingConfig(period_days=60, method="fibonacci")
        dates = generate_dates(ref, config)
        assert len(dates) == 9
        assert date(2026, 7, 9) in dates
        assert date(2026, 5, 16) in dates

    def test_fibonacci_90(self):
        ref = date(2026, 7, 10)
        config = SamplingConfig(period_days=90, method="fibonacci")
        dates = generate_dates(ref, config)
        assert len(dates) == 10

    def test_fibonacci_reverse_30(self):
        ref = date(2026, 7, 10)
        config = SamplingConfig(period_days=30, method="fibonacci_reverse")
        dates = generate_dates(ref, config)
        assert date(2026, 6, 19) in dates
        assert date(2026, 7, 9) in dates
        assert len(dates) == 7

    def test_fibonacci_double_30(self):
        ref = date(2026, 7, 10)
        config = SamplingConfig(period_days=30, method="fibonacci_double")
        dates = generate_dates(ref, config)
        assert date(2026, 6, 19) in dates
        assert date(2026, 7, 9) in dates
        assert len(dates) == 7

    def test_monte_carlo_30(self):
        ref = date(2026, 7, 10)
        config = SamplingConfig(period_days=30, method="monte_carlo")
        dates = generate_dates(ref, config)
        assert date(2026, 6, 10) in dates
        assert date(2026, 7, 9) in dates
        assert len(dates) == 7

    def test_monte_carlo_double_30(self):
        ref = date(2026, 7, 10)
        config = SamplingConfig(period_days=30, method="monte_carlo_double")
        dates = generate_dates(ref, config)
        assert date(2026, 6, 10) in dates
        assert date(2026, 7, 9) in dates
        assert len(dates) == 14

    def test_all_days_30(self):
        ref = date(2026, 7, 10)
        config = SamplingConfig(period_days=30, method="all_days")
        dates = generate_dates(ref, config)
        assert len(dates) == 30
        assert date(2026, 6, 10) in dates
        assert date(2026, 7, 9) in dates

    def test_default_config_is_fibonacci_30(self):
        ref = date(2026, 7, 10)
        dates = generate_dates(ref)
        assert len(dates) == 7
        assert date(2026, 7, 9) in dates


class TestResolveDates:
    def test_fibonacci_30_no_cache(self):
        ref = date(2026, 7, 10)
        config = SamplingConfig(period_days=30, method="fibonacci")
        dates = resolve_dates(ref, config)
        assert len(dates) == 7
        for d in dates:
            assert d.weekday() < 5

    def test_has_data_all_valid(self):
        ref = date(2026, 7, 10)
        config = SamplingConfig(period_days=60, method="fibonacci")
        has_data = MagicMock(return_value=True)
        dates = resolve_dates(ref, config, has_data=has_data)
        assert len(dates) > 0
        for d in dates:
            assert d.weekday() < 5

    def test_has_data_fallback(self):
        ref = date(2026, 7, 10)
        config = SamplingConfig(period_days=30, method="fibonacci")
        # Simulate 2026-06-29 as having no data, fallback to 2026-06-30
        def has_data(d):
            return d != date(2026, 6, 29)
        dates = resolve_dates(ref, config, has_data=has_data)
        assert len(dates) == 7
        assert date(2026, 6, 29) not in dates
        assert date(2026, 6, 30) in dates

    def test_deduplication(self):
        ref = date(2026, 7, 12)
        config = SamplingConfig(period_days=10, method="all_days")
        dates = resolve_dates(ref, config)
        assert len(dates) <= 10
        assert len(dates) == len(set(dates))


class TestFibonacciDatesCompat:
    def test_legacy_fibonacci_dates(self):
        ref = date(2026, 6, 26)
        dates = fibonacci_dates(ref)
        expected = [
            date(2026, 6, 25),
            date(2026, 6, 24),
            date(2026, 6, 23),
            date(2026, 6, 22),
            date(2026, 6, 18),
            date(2026, 6, 15),
            date(2026, 6, 5),
        ]
        assert dates == expected
        assert len(dates) == 7
