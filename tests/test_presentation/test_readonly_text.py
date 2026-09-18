"""Testes do widget de texto somente-leitura com atalhos e cursor."""

import os
import tkinter as tk

import pytest

from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)

_CONTROL = 0x4


class _Evento:
    """Evento de teclado mínimo para exercitar o bloqueio de edição."""

    def __init__(self, keysym: str, state: int = 0) -> None:
        self.keysym = keysym
        self.state = state


class TestBloqueioDeEdicao:
    @pytest.mark.parametrize(
        "keysym",
        ["a", "Z", "1", "Return", "BackSpace", "Delete", "space"],
    )
    def test_tecla_de_edicao_bloqueada(self, keysym):
        assert ReadonlyText._on_key(None, _Evento(keysym)) == "break"

    @pytest.mark.parametrize("keysym", ["Left", "Right", "Up", "Down", "Home", "End"])
    def test_navegacao_permitida(self, keysym):
        assert ReadonlyText._on_key(None, _Evento(keysym)) is None

    def test_shift_setas_permitidas(self):
        assert ReadonlyText._on_key(None, _Evento("Left", state=0x1)) is None

    def test_ctrl_a_e_ctrl_c_permitidos(self):
        assert ReadonlyText._on_key(None, _Evento("a", state=_CONTROL)) is None
        assert ReadonlyText._on_key(None, _Evento("c", state=_CONTROL)) is None

    def test_ctrl_v_bloqueado(self):
        assert ReadonlyText._on_key(None, _Evento("v", state=_CONTROL)) == "break"


class TestComportamentoNoWidget:
    @needs_display
    def test_cursor_visivel_e_conteudo_nao_editavel(self):
        root = tk.Tk()
        try:
            widget = ReadonlyText(root)
            widget.insert("1.0", "conteudo")
            widget.pack()
            widget.focus_force()
            root.update()
            assert widget.cget("insertwidth") == 2
            widget.event_generate("<KeyPress-a>", when="now")
            root.update()
            assert widget.get("1.0", "end-1c") == "conteudo"
        finally:
            root.destroy()

    @needs_display
    def test_seleciona_tudo_e_copia(self):
        root = tk.Tk()
        try:
            widget = ReadonlyText(root)
            widget.insert("1.0", "conteudo copiavel")
            widget.pack()
            widget.focus_force()
            root.update()
            widget.event_generate("<<SelectAll>>", when="now")
            root.update()
            assert widget.tag_ranges("sel")
            widget.event_generate("<<Copy>>", when="now")
            root.update()
            assert root.clipboard_get().rstrip("\n") == "conteudo copiavel"
        finally:
            root.destroy()

    @needs_display
    def test_ctrl_a_seleciona_tudo(self):
        root = tk.Tk()
        try:
            widget = ReadonlyText(root)
            widget.insert("1.0", "seleciona tudo")
            widget.pack()
            widget.focus_force()
            root.update()
            widget.event_generate("<Control-Key-a>", when="now")
            root.update()
            assert widget.tag_ranges("sel")
        finally:
            root.destroy()
