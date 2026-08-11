from datetime import date

from flowscope.domain.sampling import SamplingConfig
from flowscope.infrastructure.b3.calendar import (
    _find_nearest_with_data,
    _resolve_with_data,
    fibonacci_dates,
    resolve_dates,
)


class TestFibonacciDates:
    def test_from_friday(self):
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

    def test_all_weekdays(self):
        ref = date(2026, 6, 18)
        dates = fibonacci_dates(ref)
        for d in dates:
            assert d.weekday() < 5

    def test_returns_seven_dates(self):
        ref = date(2026, 6, 26)
        dates = fibonacci_dates(ref)
        assert len(dates) == 7

    def test_with_has_data_approximates(self):
        ref = date(2026, 7, 10)
        dates = fibonacci_dates(ref, has_data=lambda d: d != date(2026, 7, 9))
        assert date(2026, 7, 9) not in dates
        assert date(2026, 7, 8) in dates

    def test_deduplicates_weekend(self):
        ref = date(2026, 7, 6)
        dates = fibonacci_dates(ref)
        assert len(dates) == len(set(dates))
        assert dates.count(ref) == 1


class TestFindNearestWithData:
    def test_returns_own_date_when_has_data(self):
        ref = date(2026, 7, 10)
        result = _find_nearest_with_data(ref, lambda d: d == ref, set())
        assert result == ref

    def test_prefers_backward_candidate(self):
        ref = date(2026, 7, 10)
        result = _find_nearest_with_data(ref, lambda d: d == date(2026, 7, 9), set())
        assert result == date(2026, 7, 9)

    def test_finds_future_candidate(self):
        ref = date(2026, 7, 10)
        result = _find_nearest_with_data(ref, lambda d: d == date(2026, 7, 13), set())
        assert result == date(2026, 7, 13)

    def test_max_date_blocks_future_candidate(self):
        ref = date(2026, 7, 10)
        result = _find_nearest_with_data(
            ref, lambda d: d == date(2026, 7, 13), set(), max_date=date(2026, 7, 10)
        )
        assert result is None

    def test_max_date_allows_candidate_within_limit(self):
        ref = date(2026, 7, 10)
        result = _find_nearest_with_data(
            ref, lambda d: d == date(2026, 7, 9), set(), max_date=date(2026, 7, 10)
        )
        assert result == date(2026, 7, 9)

    def test_default_deviation_is_seven(self):
        ref = date(2026, 7, 10)
        result = _find_nearest_with_data(ref, lambda d: d == date(2026, 7, 2), set())
        assert result is None

    def test_finds_within_deviation(self):
        ref = date(2026, 7, 10)
        result = _find_nearest_with_data(
            ref, lambda d: d == date(2026, 7, 9), set(), max_deviation=1
        )
        assert result == date(2026, 7, 9)

    def test_beyond_deviation_returns_none(self):
        ref = date(2026, 7, 10)
        result = _find_nearest_with_data(
            ref, lambda d: d == date(2026, 7, 8), set(), max_deviation=1
        )
        assert result is None

    def test_skips_already_selected(self):
        ref = date(2026, 7, 10)
        result = _find_nearest_with_data(ref, lambda d: d == ref, {ref})
        assert result is None

    def test_selected_candidate_not_returned_even_with_data(self):
        ref = date(2026, 7, 10)
        result = _find_nearest_with_data(ref, lambda d: d == ref, {ref})
        assert result is None

    def test_ignores_non_business_day(self):
        ref = date(2026, 7, 10)
        result = _find_nearest_with_data(ref, lambda d: d == date(2026, 7, 11), set())
        assert result is None


class TestResolveWithData:
    def test_default_max_deviation_is_seven(self):
        raw = [date(2026, 7, 10)]
        has_data = lambda d: d == date(2026, 7, 2)
        assert _resolve_with_data(raw, has_data) == []

    def test_respects_max_deviation_argument(self):
        raw = [date(2026, 7, 10)]
        has_data = lambda d: d == date(2026, 7, 2)
        assert _resolve_with_data(raw, has_data, max_deviation=8) == [date(2026, 7, 2)]

    def test_continues_when_no_data(self):
        raw = [date(2026, 7, 1), date(2026, 7, 10)]
        has_data = lambda d: d == date(2026, 7, 9)
        assert _resolve_with_data(raw, has_data) == [date(2026, 7, 9)]

    def test_max_date_blocks_future(self):
        raw = [date(2026, 7, 10)]
        has_data = lambda d: d == date(2026, 7, 13)
        assert _resolve_with_data(raw, has_data, max_date=date(2026, 7, 10)) == []

    def test_deduplicates_data_dates(self):
        raw = [date(2026, 7, 10), date(2026, 7, 10)]
        has_data = lambda d: d == date(2026, 7, 10)
        assert _resolve_with_data(raw, has_data) == [date(2026, 7, 10)]

    def test_has_data_none_appends_business_day(self):
        assert _resolve_with_data([date(2026, 7, 10)], None) == [date(2026, 7, 10)]

    def test_has_data_none_deduplicates(self):
        raw = [date(2026, 7, 10), date(2026, 7, 10)]
        assert _resolve_with_data(raw, None) == [date(2026, 7, 10)]


class TestResolveDates:
    def test_passes_config(self):
        ref = date(2026, 7, 10)
        config = SamplingConfig(period_days=3, method="all_days")
        result = resolve_dates(ref, config)
        assert result == [date(2026, 7, 7), date(2026, 7, 8), date(2026, 7, 9)]
