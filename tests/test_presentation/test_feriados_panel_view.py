from datetime import date
from unittest.mock import MagicMock

from flowscope.domain.calendar import Holiday
from flowscope.presentation.gui.charts.feriados_panel import FeriadosPanel


class _Tree:
    def __init__(self):
        self._next = 0

    def get_children(self, parent=""):
        return ()

    def delete(self, item):
        pass

    def insert(self, parent, index, text):
        self._next += 1
        return f"item{self._next}"

    def selection(self):
        return ()


def _panel():
    panel = object.__new__(FeriadosPanel)
    panel._tree = _Tree()
    panel._nos = {}
    panel._arvore = ()
    panel._anos = {}
    panel._selected_key = lambda: None
    panel._set_text = MagicMock()
    return panel


def test_cache_com_anos_mas_sem_selecao_orienta_selecionar():
    panel = _panel()
    panel._render({2026: (Holiday(date(2026, 1, 1), "Confraternizacao"),)})
    panel._set_text.assert_called_with(
        "Selecione um ano, mês ou dia para ver os feriados."
    )


def test_arvore_vazia_orienta_atualizar():
    panel = _panel()
    panel._render({})
    panel._set_text.assert_called_with(
        "Nenhum feriado em cache. Use o botão de atualização para carregar."
    )
