import json
from datetime import date, datetime, timedelta, timezone

from flowscope.application.calendar.config import CalendarConfig
from flowscope.application.calendar.ports import YearHolidays
from flowscope.domain.calendar import Holiday
from flowscope.infrastructure.calendar.cache import HolidayCache


def _stamp(days: int = 0) -> str:
    moment = datetime.now(timezone.utc) - timedelta(days=days)
    return moment.isoformat(timespec="seconds")


def _year(year: int, *, published: bool = True, days: int = 0) -> YearHolidays:
    return YearHolidays(
        year=year,
        holidays=(Holiday(date(year, 1, 1), "Confraternizacao"),),
        fetched_at=_stamp(days),
        published=published,
    )


def test_escreve_e_le_um_ano(tmp_path):
    cache = HolidayCache(tmp_path)
    data = _year(2026)
    assert cache.write(data) is not None
    lido = cache.read(2026)
    assert lido is not None
    assert lido.holidays[0].date == date(2026, 1, 1)


def test_leitura_sem_cache_nao_cria_diretorio(tmp_path):
    cache = HolidayCache(tmp_path / "ausente")
    assert cache.read(2026) is None
    assert not cache.holidays_dir.exists()


def test_ano_passado_publicado_e_imutavel(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2025, days=400))
    assert cache.is_fresh(2025)


def test_ano_corrente_expira(tmp_path):
    cache = HolidayCache(tmp_path, CalendarConfig(ttl_corrente_segundos=3600))
    current = date.today().year
    cache.write(_year(current, days=2))
    assert not cache.is_fresh(current)


def test_ano_futuro_usa_ttl_curto(tmp_path):
    cache = HolidayCache(tmp_path, CalendarConfig(ttl_futuro_segundos=3600))
    future = date.today().year + 1
    cache.write(_year(future, days=2))
    assert not cache.is_fresh(future)


def test_marcador_negativo_e_fresco_e_nao_publicado(tmp_path):
    cache = HolidayCache(tmp_path, CalendarConfig(ttl_negativo_segundos=3600))
    future = date.today().year + 1
    cache.write(_year(future, published=False))
    lido = cache.read(future)
    assert lido is not None
    assert not lido.published
    assert cache.is_fresh(future)


def test_corrupcao_vira_ausencia(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.holidays_dir.mkdir(parents=True)
    cache.path(2026).write_text("{invalido", encoding="utf-8")
    assert cache.read(2026) is None


def test_escrita_e_atomica_sem_temporario(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026))
    assert not list(cache.holidays_dir.glob("*.tmp"))


def test_escrita_reutiliza_cache_fresco_concorrente(tmp_path):
    cache = HolidayCache(tmp_path)
    primeiro = _year(2026, days=0)
    cache.write(primeiro)
    segundo = YearHolidays(
        year=2026,
        holidays=(Holiday(date(2026, 2, 1), "Outro"),),
        fetched_at=_stamp(days=10),
    )
    resultado = cache.write(segundo)
    assert resultado is not None
    assert resultado.holidays[0].date == date(2026, 1, 1)
    assert cache.read(2026).holidays[0].date == date(2026, 1, 1)


def test_publicado_substitui_marcador_negativo_fresco(tmp_path):
    cache = HolidayCache(tmp_path)
    future = date.today().year + 1
    cache.write(_year(future, published=False))
    publicado = YearHolidays(
        year=future,
        holidays=(Holiday(date(future, 1, 1), "Confraternizacao"),),
        fetched_at=_stamp(days=0),
    )
    assert cache.write(publicado) is not None
    lido = cache.read(future)
    assert lido.published is True
    assert lido.holidays


def test_years_so_lista_publicados_com_feriados(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026))
    cache.write(_year(2027, published=False))
    assert cache.years() == [2026]


def test_payload_tem_origem_por_feriado(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026))
    payload = json.loads(cache.path(2026).read_text(encoding="utf-8"))
    assert payload["schema_version"] == 2
    assert payload["holidays"][0]["source"] == "ANBIMA"
