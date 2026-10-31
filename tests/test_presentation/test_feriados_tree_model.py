from datetime import date

from flowscope.application.calendar.view import (
    construir_arvore,
    feriados_do_payload,
    texto_ano,
    texto_dia,
    texto_mes,
)
from flowscope.domain.calendar import Holiday


def _holiday(ano, mes, dia, nome="Feriado", origem="ANBIMA"):
    return Holiday(date(ano, mes, dia), nome, origem)


def test_arvore_ordena_anos_meses_e_dias():
    arvore = construir_arvore({
        2025: [_holiday(2025, 12, 31)],
        2026: [
            _holiday(2026, 12, 25),
            _holiday(2026, 1, 1),
            _holiday(2026, 1, 2),
        ],
    })
    assert [ano.ano for ano in arvore] == [2026, 2025]
    assert [mes.mes for mes in arvore[0].meses] == [1, 12]
    assert [dia.data.day for dia in arvore[0].meses[0].dias] == [1, 2]


def test_folha_exibe_dia_e_abreviatura():
    arvore = construir_arvore({2026: [_holiday(2026, 1, 1)]})
    assert arvore[0].meses[0].dias[0].rotulo == "01 (qui)"


def test_textos_de_ano_mes_e_dia():
    arvore = construir_arvore({2026: [
        _holiday(2026, 1, 1, "Confraternizacao", "ANBIMA"),
    ]})
    ano = arvore[0]
    mes = ano.meses[0]
    dia = mes.dias[0]
    assert "Janeiro" in texto_ano(ano)
    assert "01 (qui) Confraternizacao" in texto_mes(mes)
    assert "2026-01-01 (qui) — Confraternizacao (ANBIMA)" in texto_dia(dia)


def test_converte_payload_em_feriados():
    holidays = feriados_do_payload({
        "feriados": [
            {"data": "2026-01-01", "nome": "Confraternizacao", "origem": "ANBIMA"},
            {"data": "invalida", "nome": "x", "origem": "ANBIMA"},
        ]
    })
    assert len(holidays) == 1
    assert holidays[0].source == "ANBIMA"
