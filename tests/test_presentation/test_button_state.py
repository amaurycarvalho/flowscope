import os
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock

import pytest

from flowscope.presentation.gui.app_status import StatusMixin


@pytest.fixture
def root():
    r = tk.Tk()
    yield r
    r.destroy()


needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


class TestDisableRestoreButtons:
    @needs_display
    def test_disable_all_salva_snapshot_e_desabilita(self, root):
        btn1 = tk.Button(root, state=tk.NORMAL)
        btn2 = tk.Button(root, state=tk.DISABLED)
        btn3 = tk.Button(root, state=tk.ACTIVE)

        gui = _FakeGUI(root, [btn1, btn2, btn3])

        gui.disable_all_buttons()

        assert btn1.cget("state") == tk.DISABLED
        assert btn2.cget("state") == tk.DISABLED
        assert btn3.cget("state") == tk.DISABLED
        assert gui._button_states[btn1] == tk.NORMAL
        assert gui._button_states[btn2] == tk.DISABLED
        assert gui._button_states[btn3] == tk.ACTIVE

    @needs_display
    def test_restore_all_retorna_aos_estados_anteriores(self, root):
        btn1 = tk.Button(root, state=tk.NORMAL)
        btn2 = tk.Button(root, state=tk.DISABLED)

        gui = _FakeGUI(root, [btn1, btn2])
        gui.disable_all_buttons()
        gui.restore_all_buttons()

        assert btn1.cget("state") == tk.NORMAL
        assert btn2.cget("state") == tk.DISABLED


class _FakeGUI:
    def __init__(self, root, buttons):
        self._button_states: dict[tk.Widget, str] = {}
        self._buttons = buttons

    def disable_all_buttons(self) -> None:
        self._button_states = {}
        for btn in self._buttons:
            self._button_states[btn] = btn.cget("state")
            btn.config(state=tk.DISABLED)

    def restore_all_buttons(self) -> None:
        if not hasattr(self, "_button_states"):
            return
        for widget, state in self._button_states.items():
            try:
                widget.config(state=state)
            except tk.TclError:
                pass
        self._button_states = {}


class _CursorGUI(tk.Tk, StatusMixin):
    pass


class _DisableHost(tk.Tk, StatusMixin):
    pass


class TestDisableIdempotente:
    @needs_display
    def test_nao_sobrescreve_snapshot_ativo(self):
        gui = _DisableHost()
        try:
            gui._flash_after_id = None
            gui._load_button = tk.Button(gui, state=tk.NORMAL)
            gui._today_button = tk.Button(gui, state=tk.NORMAL)
            gui._shortcut_btn = None
            gui._copy_data_btn = tk.Button(gui, state=tk.NORMAL)
            gui._ticker_list = MagicMock()
            gui._ticker_list.all_buttons.return_value = []
            gui._period_combo = ttk.Combobox(gui, state="readonly")
            gui._sampling_combo = ttk.Combobox(gui, state="readonly")
            gui._date_entry = ttk.Entry(gui)

            gui.disable_all_buttons()
            gui.disable_all_buttons()
            gui.restore_all_buttons()

            assert gui._load_button.cget("state") == tk.NORMAL
            assert str(gui._period_combo.cget("state")) == "readonly"
            assert str(gui._date_entry.cget("state")) == "normal"
        finally:
            gui.destroy()


class TestWaitCursor:
    @needs_display
    def test_cursor_watch_sobrepoe_e_restaura(self):
        gui = _CursorGUI()
        try:
            btn = tk.Button(gui, cursor="hand2")
            btn.pack()
            gui._set_wait_cursor()
            assert btn.cget("cursor") == "watch"
            gui._clear_wait_cursor()
            assert btn.cget("cursor") == "hand2"
        finally:
            gui.destroy()

    @needs_display
    def test_cursor_watch_nao_repercorre_enquanto_ativo(self):
        gui = _CursorGUI()
        try:
            btn = tk.Button(gui, cursor="hand2")
            btn.pack()
            gui._set_wait_cursor()
            primeiro = dict(gui._cursor_states)
            gui._set_wait_cursor()
            assert gui._cursor_states == primeiro
            gui._clear_wait_cursor()
            assert gui._cursor_states == {}
        finally:
            gui.destroy()
