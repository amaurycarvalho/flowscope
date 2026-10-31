import json
from datetime import date, datetime, timezone

import pytest

from flowscope.application.calendar.config import CalendarConfig
from flowscope.application.calendar.ports import (
    HolidaySourceError,
    HolidayYearUnavailable,
    YearHolidays,
)
from flowscope.application.calendar.service import (
    ESTADO_DEFASADO,
    ESTADO_INDISPONIVEL,
    ESTADO_OK,
    CalendarService,
)
from flowscope.domain.calendar import Holiday
from flowscope.infrastructure.calendar.cache import HolidayCache


class FakeSource:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error
        self.calls = []

    def fetch_year(self, year):
        self.calls.append(year)
        if self.error is not None:
            raise self.error
        if self.data is not None:
            return self.data
        return YearHolidays(
            year=year,
            holidays=(Holiday(date(year, 1, 1), "Confraternizacao"),),
            fetched_at="2026-01-01T00:00:00+00:00",
        )


def _year(year, holidays, published=True):
    return YearHolidays(
        year=year,
        holidays=tuple(holidays),
        fetched_at="2026-01-01T00:00:00+00:00",
        published=published,
    )


def test_ensure_year_grava_e_reutiliza_cache(tmp_path):
    source = FakeSource()
    cache = HolidayCache(tmp_path)
    service = CalendarService(source, cache)
    assert service.ensure_year(2025) == ESTADO_OK
    assert service.ensure_year(2025) == ESTADO_OK
    assert source.calls == [2025]


def test_falha_usa_cache_anterior_defasado(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026, [Holiday(date(2026, 1, 1), "Confraternizacao")]))
    source = FakeSource(error=HolidaySourceError("falha"))
    service = CalendarService(source, cache)
    assert service.ensure_year(2026, force=True) == ESTADO_DEFASADO
    assert service.listar_ano(2026)["estado"] == ESTADO_DEFASADO


def test_sem_cache_e_falha_fica_indisponivel(tmp_path):
    source = FakeSource(error=HolidaySourceError("falha"))
    service = CalendarService(source, HolidayCache(tmp_path))
    assert service.ensure_year(2026) == ESTADO_INDISPONIVEL


def test_ano_futuro_indisponivel_grava_marcador_negativo(tmp_path):
    future = date.today().year + 1
    source = FakeSource(error=HolidayYearUnavailable("nao publicado"))
    cache = HolidayCache(tmp_path)
    service = CalendarService(source, cache)
    assert service.ensure_year(future) == ESTADO_INDISPONIVEL
    assert cache.read(future).published is False
    service2 = CalendarService(source, cache)
    assert service2.ensure_year(future) == ESTADO_INDISPONIVEL
    assert source.calls == [future]


def test_marcador_negativo_nao_e_lido_como_ok(tmp_path):
    future = date.today().year + 1
    cache = HolidayCache(tmp_path)
    cache.write(YearHolidays(
        year=future,
        holidays=(),
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        published=False,
    ))
    source = FakeSource()
    service = CalendarService(source, cache)
    assert service.ensure_year(future) == ESTADO_INDISPONIVEL
    assert source.calls == []


def test_resolucao_retrocede_para_dia_util_anterior(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026, [
        Holiday(date(2026, 12, 24), "Vespera", "RECESSO_B3"),
        Holiday(date(2026, 12, 25), "Natal"),
    ]))
    service = CalendarService(FakeSource(), cache)
    resultado = service.resolve_business_day("2026-12-25")
    assert resultado.data_resolvida == "2026-12-23"
    assert resultado.motivo == "feriado"
    assert resultado.feriado == "Natal"
    assert resultado.origem == "ANBIMA"


def test_resolucao_fim_de_semana(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026, [Holiday(date(2026, 1, 1), "Confraternizacao")]))
    service = CalendarService(FakeSource(), cache)
    resultado = service.resolve_business_day("2026-12-26")
    assert resultado.data_resolvida == "2026-12-25"
    assert resultado.motivo == "fim_de_semana"


def test_resolucao_atravessa_virada_do_ano(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2025, [Holiday(date(2025, 12, 31), "Vespera")]))
    cache.write(_year(2026, [Holiday(date(2026, 1, 1), "Confraternizacao")]))
    service = CalendarService(FakeSource(), cache)
    resultado = service.resolve_business_day("2026-01-01")
    assert resultado.data_resolvida == "2025-12-30"


def test_ensure_reference_garante_ano_anterior_em_janeiro(tmp_path):
    source = FakeSource()
    service = CalendarService(source, HolidayCache(tmp_path))
    service.ensure_reference(date(2026, 1, 2))
    assert source.calls == [2026, 2025]


def test_classificar_informa_dia_util_e_origem(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026, [Holiday(date(2026, 1, 1), "Confraternizacao")]))
    service = CalendarService(FakeSource(), cache)
    util = service.classificar("2026-01-02")
    feriado = service.classificar("2026-01-01")
    assert util["dia_util"] is True
    assert feriado["dia_util"] is False
    assert feriado["origem"] == "ANBIMA"


def test_exporta_csv_e_json_com_origem(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2026, [Holiday(date(2026, 1, 1), "Confraternizacao")]))
    service = CalendarService(FakeSource(), cache)
    csv = service.exportar_ano(2026, "csv")
    payload = json.loads(service.exportar_ano(2026, "json"))
    assert "data;dia_semana;nome;origem" in csv
    assert "2026-01-01;qui;Confraternizacao;ANBIMA" in csv
    assert payload["feriados"][0]["origem"] == "ANBIMA"


def test_force_substitui_cache_fresco(tmp_path):
    cache = HolidayCache(tmp_path)
    cache.write(_year(2025, [Holiday(date(2025, 1, 1), "Antigo")]))
    novo = YearHolidays(
        year=2025,
        holidays=(Holiday(date(2025, 1, 1), "Novo"),),
        fetched_at="2027-01-01T00:00:00+00:00",
    )
    service = CalendarService(FakeSource(data=novo), cache)
    assert service.ensure_year(2025, force=True) == ESTADO_OK
    assert cache.read(2025).holidays[0].name == "Novo"


def test_formato_invalido_falha(tmp_path):
    service = CalendarService(FakeSource(), HolidayCache(tmp_path))
    with pytest.raises(ValueError):
        service.exportar_ano(2026, "xml")
