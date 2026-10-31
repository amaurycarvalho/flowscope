from datetime import date

from flowscope.application.calendar.ports import YearHolidays, WeekendBusinessDayLookup
from flowscope.application.calendar.service import CalendarService
from flowscope.domain.calendar import Holiday
from flowscope.infrastructure.calendar.cache import HolidayCache
from flowscope.infrastructure.calendar.lookup import CachedBusinessDayLookup


class _Source:
    def fetch_year(self, year):
        raise AssertionError("lookup não deve consultar a fonte")


def test_lookup_le_cache_sem_alterar_arquivos(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(YearHolidays(
        year=2026,
        holidays=(Holiday(date(2026, 1, 1), "Confraternizacao"),),
        fetched_at="2026-01-01T00:00:00+00:00",
    ))
    antes = cache.path(2026).read_bytes()
    arquivos = sorted(path.name for path in tmp_path.rglob("*") if path.is_file())
    lookup = CachedBusinessDayLookup(CalendarService(_Source(), cache))
    assert not lookup.is_business_day(date(2026, 1, 1))
    assert lookup.is_business_day(date(2026, 1, 2))
    depois = sorted(path.name for path in tmp_path.rglob("*") if path.is_file())
    assert arquivos == depois
    assert cache.path(2026).read_bytes() == antes


def test_lookup_padrao_so_fim_de_semana():
    lookup = WeekendBusinessDayLookup()
    assert lookup.is_business_day(date(2026, 1, 1))
    assert not lookup.is_business_day(date(2026, 1, 3))
