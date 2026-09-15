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


@needs_display
class TestActionButton:
    def _ticker_list(self, root) -> TickerList:
        return TickerList(
            root,
            on_index_click={
                "IBOV": lambda: None,
                "IDIV": lambda: None,
                "IFIX": lambda: None,
            },
        )

    def _add(self, ticker_list) -> tk.Button:
        return ticker_list.add_action_button(
            lambda: None,
            icon="edit-redo.png",
            tooltip="Atualizar fundamentos",
        )

    def _ordem(self, ticker_list) -> list:
        return ticker_list._btn_frame.pack_slaves()

    def test_adicionado_apos_desmarcar_todos(self):
        root = tk.Tk()
        try:
            ticker_list = self._ticker_list(root)
            btn = self._add(ticker_list)
            ordem = self._ordem(ticker_list)
            assert ordem.index(ticker_list._btn_none) < ordem.index(btn)
            assert ordem.index(btn) < ordem.index(ticker_list._sep)
        finally:
            root.destroy()

    def test_incluido_em_all_buttons(self):
        root = tk.Tk()
        try:
            ticker_list = self._ticker_list(root)
            btn = self._add(ticker_list)
            assert btn in ticker_list.all_buttons()
        finally:
            root.destroy()

    def test_usa_icone_e_tooltip(self):
        root = tk.Tk()
        try:
            ticker_list = self._ticker_list(root)
            btn = self._add(ticker_list)
            assert btn.cget("image")
            assert btn.cget("text") == ""
            assert btn.bind("<Enter>")
        finally:
            root.destroy()

    def test_visibilidade(self):
        root = tk.Tk()
        try:
            ticker_list = self._ticker_list(root)
            btn = self._add(ticker_list)
            ticker_list.set_action_button_visible(btn, False)
            assert btn.winfo_manager() == ""
            ticker_list.set_action_button_visible(btn, True)
            assert btn.winfo_manager() == "pack"
        finally:
            root.destroy()

    def test_rebuild_de_indices_mantem_acao_no_grupo(self):
        root = tk.Tk()
        try:
            ticker_list = self._ticker_list(root)
            btn = self._add(ticker_list)
            ticker_list.rebind(
                on_index_click={
                    "IBOV": lambda: None,
                    "IDIV": lambda: None,
                    "IFIX": lambda: None,
                }
            )
            ordem = self._ordem(ticker_list)
            assert ordem.index(ticker_list._btn_none) < ordem.index(btn)
            assert ordem.index(btn) < ordem.index(ticker_list._sep)
        finally:
            root.destroy()

    def test_botoes_de_indice_tem_tooltip(self):
        from flowscope.presentation.gui.widgets.ticker_list import _TOOLTIPS_INDICE

        assert _TOOLTIPS_INDICE == {
            "IBOV": "principais ações negociadas na B3",
            "IDIV": "ações com os maiores dividendos da B3",
            "IFIX": "principais fundos imobiliários (FIIs)",
        }

        root = tk.Tk()
        try:
            ticker_list = self._ticker_list(root)
            por_texto = {btn.cget("text"): btn for btn in ticker_list._index_buttons}
            for label in ("IBOV", "IDIV", "IFIX"):
                assert por_texto[label].bind("<Enter>")
        finally:
            root.destroy()
