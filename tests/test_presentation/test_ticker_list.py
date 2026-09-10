import os
import tkinter as tk
from unittest.mock import MagicMock

import pytest

from flowscope.presentation.gui.widgets.ticker_list import TickerList


needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


@needs_display
class TestSetTickersProgramatico:
    def test_set_tickers_nao_dispara_on_change(self):
        root = tk.Tk()
        try:
            on_change = MagicMock()
            ticker_list = TickerList(root, on_change=on_change)

            ticker_list.set_tickers(["PETR4", "VALE3"])

            on_change.assert_not_called()
        finally:
            root.destroy()

    def test_selecao_manual_dispara_on_change(self):
        root = tk.Tk()
        try:
            on_change = MagicMock()
            ticker_list = TickerList(root, on_change=on_change)
            ticker_list.set_tickers(["PETR4", "VALE3"])

            ticker_list._on_listbox_select()

            on_change.assert_called_once()
        finally:
            root.destroy()
