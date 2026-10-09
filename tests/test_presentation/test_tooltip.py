"""Testes do ciclo de vida do widget ToolTip (sem necessidade de display)."""

import tkinter as tk

import pytest

from flowscope.presentation.gui.widgets import tooltip as tooltip_module
from flowscope.presentation.gui.widgets.tooltip import ToolTip


class _FakeWidget:
    """Widget mínimo que registra agendamentos, cancelamentos e eventos."""

    def __init__(self) -> None:
        self.callbacks: dict[str, object] = {}
        self._next_id = 0
        self.enter_cb = None
        self.leave_cb = None
        self.button_cb = None
        self.after_cancel_raises = False

    def bind(self, event, callback, add=False):
        if event == "<Enter>":
            self.enter_cb = callback
        elif event == "<Leave>":
            self.leave_cb = callback
        elif event == "<ButtonPress>":
            self.button_cb = callback

    def after(self, delay, func):
        self._next_id += 1
        after_id = f"after#{self._next_id}"
        self.callbacks[after_id] = func
        return after_id

    def after_cancel(self, after_id):
        if self.after_cancel_raises or after_id not in self.callbacks:
            raise tk.TclError(after_id)
        del self.callbacks[after_id]

    def run_pending(self):
        for func in list(self.callbacks.values()):
            func()
        self.callbacks.clear()

    def winfo_rootx(self):
        return 100

    def winfo_rooty(self):
        return 200


class _FakeToplevel:
    """Substituto de ``tk.Toplevel`` que registra criação e destruição."""

    instances: list["_FakeToplevel"] = []

    def __init__(self, master) -> None:
        self.master = master
        self.destroyed = False
        _FakeToplevel.instances.append(self)

    def wm_overrideredirect(self, flag):
        return None

    def wm_geometry(self, geometry):
        return None

    def destroy(self):
        self.destroyed = True


class _FakeLabel:
    """Substituto de ``tk.Label`` suficiente para ``_show``."""

    def __init__(self, master, **kwargs) -> None:
        self.master = master

    def pack(self):
        return None


def _live_windows() -> list[_FakeToplevel]:
    return [janela for janela in _FakeToplevel.instances if not janela.destroyed]


@pytest.fixture(autouse=True)
def _fake_tk(monkeypatch):
    _FakeToplevel.instances = []
    monkeypatch.setattr(tooltip_module.tk, "Toplevel", _FakeToplevel)
    monkeypatch.setattr(tooltip_module.tk, "Label", _FakeLabel)


class TestEntradasRepetidas:
    def test_dois_enter_sem_leave_agendam_uma_unica_exibicao(self):
        widget = _FakeWidget()
        tip = ToolTip(widget, "dica", delay_ms=400)

        widget.enter_cb()
        widget.enter_cb()

        assert len(widget.callbacks) == 1
        widget.run_pending()
        assert len(_FakeToplevel.instances) == 1
        assert tip._tip_window is not None

    def test_enter_enter_leave_nao_deixa_janela_orfa(self):
        widget = _FakeWidget()
        tip = ToolTip(widget, "dica")

        widget.enter_cb()
        widget.enter_cb()
        widget.leave_cb()
        widget.run_pending()

        assert _live_windows() == []
        assert tip._tip_window is None


class TestExibicao:
    def test_show_destroi_janela_anterior(self):
        widget = _FakeWidget()
        tip = ToolTip(widget, "dica")

        tip._show()
        primeira = tip._tip_window
        tip._show()

        assert primeira.destroyed is True
        assert tip._tip_window is not primeira
        assert len(_live_windows()) == 1

    def test_show_zera_after_id(self):
        widget = _FakeWidget()
        tip = ToolTip(widget, "dica")

        widget.enter_cb()
        assert tip._after_id is not None

        tip._show()

        assert tip._after_id is None


class TestSaida:
    def test_leave_destroi_janela_visivel(self):
        widget = _FakeWidget()
        tip = ToolTip(widget, "dica")
        tip._show()

        widget.leave_cb()

        assert tip._tip_window is None
        assert _live_windows() == []

    def test_saida_durante_o_atraso_nao_exibe_dica(self):
        widget = _FakeWidget()
        tip = ToolTip(widget, "dica")

        widget.enter_cb()
        widget.leave_cb()
        widget.run_pending()

        assert _FakeToplevel.instances == []
        assert tip._tip_window is None

    def test_leave_tolera_tclerror_em_after_cancel(self):
        widget = _FakeWidget()
        tip = ToolTip(widget, "dica")

        widget.enter_cb()
        widget.after_cancel_raises = True

        widget.leave_cb()

        assert tip._after_id is None
        assert tip._tip_window is None

    def test_clique_destroi_janela_visivel(self):
        widget = _FakeWidget()
        tip = ToolTip(widget, "dica")
        tip._show()

        widget.button_cb()

        assert tip._tip_window is None
        assert _live_windows() == []
