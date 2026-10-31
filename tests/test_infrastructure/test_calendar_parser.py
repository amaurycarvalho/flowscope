from datetime import date
from pathlib import Path

import pytest

from flowscope.application.calendar.ports import (
    HolidaySourceError,
    HolidayYearUnavailable,
)
from flowscope.domain.calendar import ORIGEM_ANBIMA, ORIGEM_RECESSO_B3
from flowscope.infrastructure.calendar.source_parser import parse_page

_FIXTURE = Path(__file__).parent.parent / "fixtures" / "b3" / "anbima_2026.html"


def _raw() -> bytes:
    return _FIXTURE.read_bytes()


class TestParsePage:
    def test_le_feriados_da_anbima(self):
        holidays = parse_page(_raw(), 2026)
        assert len(holidays) == 15
        assert holidays[0].date == date(2026, 1, 1)
        assert holidays[0].name == "Confraternizacao Universal"
        assert holidays[0].source == ORIGEM_ANBIMA

    def test_inclui_recesso_local(self):
        holidays = {item.date: item for item in parse_page(_raw(), 2026)}
        assert holidays[date(2026, 12, 24)].source == ORIGEM_RECESSO_B3
        assert holidays[date(2026, 12, 31)].source == ORIGEM_RECESSO_B3

    def test_recesso_nao_duplica_feriado_da_anbima(self):
        raw = (
            b"<html><body><table>"
            b"<tr><td>Data</td><td>Dia da Semana</td><td>Feriado</td></tr>"
            b"<tr><td>24/12/26</td><td>quinta-feira</td><td>Vespera</td></tr>"
            b"</table></body></html>"
        )
        holidays = [item for item in parse_page(raw, 2026) if item.date == date(2026, 12, 24)]
        assert len(holidays) == 1
        assert holidays[0].source == ORIGEM_ANBIMA

    def test_dia_da_semana_divergente_invalida_ano(self):
        with pytest.raises(HolidaySourceError):
            parse_page(_raw().replace(b"quinta-feira", b"sexta-feira", 1), 2026)

    def test_pagina_sem_tabela_e_ano_indisponivel(self):
        with pytest.raises(HolidayYearUnavailable):
            parse_page(b"<html><body><p>nada</p></body></html>", 2026)
