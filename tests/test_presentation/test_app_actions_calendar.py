from datetime import date
from unittest.mock import MagicMock, patch

from flowscope.presentation.gui.app_actions import ActionsMixin


class _Host(ActionsMixin):
    def __init__(self):
        self._date_entry = MagicMock()
        self._controller = MagicMock()


def test_on_today_delega_para_controller():
    host = _Host()
    host._on_today()
    host._controller.on_today.assert_called_once_with()


def test_fallback_de_referencia_usa_data_local():
    host = _Host()
    del host._date_entry
    with patch("flowscope.presentation.gui.app_actions.date") as fake_date:
        fake_date.today.return_value = date(2026, 10, 31)
        assert host._data_referencia() == date(2026, 10, 31)
