from datetime import date
from unittest.mock import patch

from flowscope.presentation.gui.charts.noticias_panel import _hoje


def test_hoje_usa_data_local():
    with patch(
        "flowscope.presentation.gui.charts.noticias_panel.date"
    ) as fake_date:
        fake_date.today.return_value = date(2026, 10, 31)
        assert _hoje() == date(2026, 10, 31)
