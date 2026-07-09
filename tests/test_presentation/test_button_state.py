import os
import tkinter as tk
import pytest


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
