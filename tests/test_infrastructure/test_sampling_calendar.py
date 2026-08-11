from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from flowscope.domain.sampling import SamplingConfig
from flowscope.infrastructure.b3.calendar import (
    fibonacci_dates,
    generate_dates,
    resolve_dates,
)
from flowscope.infrastructure.b3.generators import (
    _fibonacci_double_dates,
    _fibs_up_to,
    _monte_carlo_dates,
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


class TestFibsUpTo:
    @pytest.mark.parametrize(
        "limit,expected",
        [
            (0, []),
            (1, [1]),
            (2, [1, 2]),
            (3, [1, 2, 3]),
            (4, [1, 2, 3]),
            (5, [1, 2, 3, 5]),
            (13, [1, 2, 3, 5, 8, 13]),
            (89, [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]),
            (90, [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]),
        ],
    )
    def test_fibs_up_to(self, limit: int, expected: list[int]):
        assert _fibs_up_to(limit) == expected


class TestFibonacciDoubleDates:
    def test_period_30_uses_fixed_offsets(self):
        ref = date(2026, 7, 10)
        dates = _fibonacci_double_dates(ref, period_days=30)
        expected = [
            date(2026, 6, 19),
            date(2026, 6, 20),
            date(2026, 6, 21),
            date(2026, 7, 1),
            date(2026, 7, 7),
            date(2026, 7, 8),
            date(2026, 7, 9),
        ]
        assert dates == expected

    def test_period_31_uses_dynamic_offsets(self):
        ref = date(2026, 7, 10)
        dates = _fibonacci_double_dates(ref, period_days=31)
        expected = [
            date(2026, 6, 19),
            date(2026, 6, 20),
            date(2026, 6, 21),
            date(2026, 6, 23),
            date(2026, 6, 26),
            date(2026, 7, 1),
            date(2026, 7, 9),
        ]
        assert dates == expected

    def test_period_34_middle_is_middle_offset(self):
        ref = date(2026, 7, 10)
        dates = _fibonacci_double_dates(ref, period_days=34)
        expected = [
            date(2026, 6, 6),
            date(2026, 6, 7),
            date(2026, 6, 8),
            date(2026, 6, 13),
            date(2026, 6, 18),
            date(2026, 6, 26),
            date(2026, 7, 9),
        ]
        assert dates == expected

    def test_period_60_uses_13_as_middle(self):
        ref = date(2026, 7, 10)
        dates = _fibonacci_double_dates(ref, period_days=60)
        expected = [
            date(2026, 5, 16),
            date(2026, 5, 17),
            date(2026, 5, 18),
            date(2026, 5, 28),
            date(2026, 6, 5),
            date(2026, 6, 18),
            date(2026, 7, 9),
        ]
        assert dates == expected

    def test_period_89_uses_large_offsets(self):
        ref = date(2026, 7, 10)
        dates = _fibonacci_double_dates(ref, period_days=89)
        expected = [
            date(2026, 4, 12),
            date(2026, 4, 13),
            date(2026, 4, 14),
            date(2026, 4, 24),
            date(2026, 5, 15),
            date(2026, 6, 5),
            date(2026, 7, 9),
        ]
        assert dates == expected


class TestMonteCarloDates:
    def test_includes_first_and_last(self):
        ref = date(2026, 7, 10)
        dates = _monte_carlo_dates(ref, period_days=30, count=5)
        assert dates[0] == date(2026, 6, 10)
        assert dates[1] == date(2026, 7, 9)

    def test_available_excludes_endpoints(self):
        ref = date(2026, 7, 10)
        with patch("flowscope.infrastructure.b3.generators.random.sample") as mock_sample:
            mock_sample.return_value = []
            _monte_carlo_dates(ref, period_days=30, count=5)
        available = mock_sample.call_args.args[0]
        assert date(2026, 6, 10) not in available
        assert date(2026, 7, 9) not in available
        assert date(2026, 6, 11) in available
        assert len(available) == 28

    def test_sample_limited_to_available(self):
        ref = date(2026, 7, 10)
        with patch("flowscope.infrastructure.b3.generators.random.sample") as mock_sample:
            mock_sample.return_value = []
            _monte_carlo_dates(ref, period_days=30, count=100)
        available = mock_sample.call_args.args[0]
        assert mock_sample.call_args.args[1] == 28
        assert all(d in available for d in mock_sample.call_args.args[0][:3])

    def test_sample_uses_requested_count(self):
        ref = date(2026, 7, 10)
        with patch("flowscope.infrastructure.b3.generators.random.sample") as mock_sample:
            mock_sample.return_value = []
            _monte_carlo_dates(ref, period_days=30, count=5)
        assert mock_sample.call_args.args[1] == 5

    def test_empty_available_does_not_sample(self):
        ref = date(2026, 7, 10)
        with patch("flowscope.infrastructure.b3.generators.random.sample") as mock_sample:
            dates = _monte_carlo_dates(ref, period_days=1, count=5)
        mock_sample.assert_not_called()
        assert dates == [date(2026, 7, 9), date(2026, 7, 9)]
