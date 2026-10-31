import json
from datetime import date
from types import SimpleNamespace

import pytest

from flowscope.application.calendar.ports import (
    HolidaySourceError,
    YearHolidays,
)
from flowscope.application.calendar.service import CalendarService
from flowscope.domain.calendar import Holiday
from flowscope.infrastructure.calendar.cache import HolidayCache
from flowscope.presentation import cli_acoes, cli_consultas
from flowscope.presentation.cli import build_parser


class _Source:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def fetch_year(self, year):
        self.calls.append(year)
        if self.error is not None:
            raise self.error
        return YearHolidays(
            year=year,
            holidays=(Holiday(date(year, 1, 1), "Confraternizacao"),),
            fetched_at="2099-01-01T00:00:00+00:00",
        )


def _install(monkeypatch, service):
    calendar = SimpleNamespace(service=service, lookup=object())
    monkeypatch.setattr(
        "flowscope.infrastructure.calendar.build_calendar_services",
        lambda: calendar,
    )


def test_consultar_feriados_exibe_json(tmp_path, monkeypatch, capsys):
    cache = HolidayCache(tmp_path)
    service = CalendarService(_Source(), cache)
    service.ensure_year(2026)
    _install(monkeypatch, service)
    args = build_parser().parse_args(["consultar", "feriados", "--ano", "2026"])

    cli_consultas.executar_consultar(args)

    payload = json.loads(capsys.readouterr().out)
    assert payload["ano"] == 2026
    assert payload["feriados"][0]["origem"] == "ANBIMA"


def test_consultar_feriados_sem_cache_nao_consulta_rede(tmp_path, monkeypatch, capsys):
    source = _Source()
    service = CalendarService(source, HolidayCache(tmp_path))
    _install(monkeypatch, service)
    args = build_parser().parse_args(["consultar", "feriados", "--ano", "2026"])

    cli_consultas.executar_consultar(args)

    payload = json.loads(capsys.readouterr().out)
    assert payload["estado"] == "calendario_indisponivel"
    assert source.calls == []


def test_exportar_feriados_csv_stdout(tmp_path, monkeypatch, capsys):
    cache = HolidayCache(tmp_path)
    service = CalendarService(_Source(), cache)
    service.ensure_year(2026)
    _install(monkeypatch, service)
    args = build_parser().parse_args(
        ["exportar", "feriados", "--ano", "2026", "--formato", "csv"]
    )

    cli_consultas.executar_exportar(args)

    saida = capsys.readouterr().out
    assert saida.startswith("data;dia_semana;nome;origem")
    assert "2026-01-01;qui;Confraternizacao;ANBIMA" in saida


def test_exportar_feriados_json_em_arquivo(tmp_path, monkeypatch):
    cache = HolidayCache(tmp_path)
    service = CalendarService(_Source(), cache)
    service.ensure_year(2026)
    _install(monkeypatch, service)
    destino = tmp_path / "feriados.json"
    args = build_parser().parse_args([
        "exportar", "feriados", "--ano", "2026",
        "--formato", "json", "--saida", str(destino),
    ])

    cli_consultas.executar_exportar(args)

    payload = json.loads(destino.read_text(encoding="utf-8"))
    assert payload["ano"] == 2026


def test_atualizar_feriados_forca_revalidacao(tmp_path, monkeypatch):
    source = _Source()
    service = CalendarService(source, HolidayCache(tmp_path))
    _install(monkeypatch, service)

    resultado = cli_acoes.atualizar_feriados([2026, 2027])

    assert source.calls == [2026, 2027]
    assert resultado["anos"]["2026"]["estado"] == "ok"
    assert resultado["falha"] is False


def test_atualizar_feriados_sem_cache_indica_falha(tmp_path, monkeypatch):
    service = CalendarService(
        _Source(HolidaySourceError("falha")), HolidayCache(tmp_path)
    )
    _install(monkeypatch, service)

    resultado = cli_acoes.atualizar_feriados([2026])

    assert resultado["falha"] is True
    assert resultado["anos"]["2026"]["estado"] == "calendario_indisponivel"


def test_resolver_referencia_retrocede_para_dia_util():
    class _Resolucao:
        data_resolvida = "2026-10-30"

        def as_dict(self):
            return {"data_solicitada": "2026-10-31", "data_resolvida": "2026-10-30"}

    class _Service:
        def resolve_reference(self, value):
            return _Resolucao()

    nucleo = SimpleNamespace(calendar=SimpleNamespace(service=_Service()))
    data, resolucao = cli_acoes._resolver_referencia(nucleo, date(2026, 10, 31))
    assert data == date(2026, 10, 30)
    assert resolucao["data_solicitada"] == "2026-10-31"
