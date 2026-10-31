from datetime import date
from types import SimpleNamespace

import flowscope.infrastructure.b3.client as client_module
import flowscope.infrastructure.b3.repository as repository_module
from flowscope.presentation import cli_consultas


class _FakeDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 10, 12)


class _FakeService:
    def resolve_reference(self, value):
        return SimpleNamespace(data_resolvida="2026-10-09")


class _FakeCalendar:
    service = _FakeService()
    lookup = object()


class _FakeUseCase:
    captured = []

    def __init__(self, repository):
        self.repository = repository

    def execute(self, ref_date, ticker_filter=None):
        self.captured.append(ref_date)
        return "csv"


def test_exportar_vwap_usa_data_local_resolvida(tmp_path, monkeypatch):
    _FakeUseCase.captured = []
    monkeypatch.setattr(cli_consultas, "date", _FakeDate)
    monkeypatch.setattr(
        "flowscope.infrastructure.calendar.build_calendar_services",
        lambda: _FakeCalendar(),
    )
    monkeypatch.setattr(client_module, "B3Client", lambda **kwargs: object())
    monkeypatch.setattr(
        repository_module, "B3DataRepository", lambda *args, **kwargs: object()
    )
    monkeypatch.setattr(
        "flowscope.application.use_cases.ExportVWAPUseCase",
        _FakeUseCase,
    )
    args = SimpleNamespace(tickers=None, saida=str(tmp_path / "vwap.csv"))

    cli_consultas._exportar_vwap(args)

    assert _FakeUseCase.captured == [date(2026, 10, 9)]
    assert (tmp_path / "vwap.csv").read_text(encoding="utf-8") == "csv"
