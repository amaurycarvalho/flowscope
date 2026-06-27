from datetime import date

from flowscope.infrastructure.b3.calendar import fibonacci_dates


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
