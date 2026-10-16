import os
import tkinter as tk
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from flowscope.presentation.gui.widgets import ticker_list as ticker_list_mod
from flowscope.presentation.gui.widgets.ticker_list import TickerList


needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


@needs_display
class TestCallbacks:
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

    def test_load_dispara_com_caminho_completo(self, monkeypatch, tmp_path):
        arquivo = tmp_path / "petr4.txt"
        arquivo.write_text("PETR4\nVALE3", encoding="utf-8")
        monkeypatch.setattr(
            ticker_list_mod.filedialog, "askopenfilename", lambda **k: str(arquivo)
        )
        root = tk.Tk()
        try:
            recebidos: list[Path] = []
            ticker_list = TickerList(root, on_file_changed=recebidos.append)

            ticker_list._load()

            assert recebidos == [arquivo]
        finally:
            root.destroy()

    def test_save_dispara_com_caminho_completo(self, monkeypatch, tmp_path):
        arquivo = tmp_path / "carteira.txt"
        monkeypatch.setattr(
            ticker_list_mod.filedialog, "asksaveasfilename", lambda **k: str(arquivo)
        )
        root = tk.Tk()
        try:
            recebidos: list[Path] = []
            ticker_list = TickerList(root, on_file_changed=recebidos.append)
            ticker_list.set_tickers(["PETR4"])

            ticker_list._save()

            assert recebidos == [arquivo]
            assert arquivo.read_text(encoding="utf-8") == "PETR4"
        finally:
            root.destroy()

    def test_editar_conteudo_dispara(self):
        root = tk.Tk()
        try:
            on_content_changed = MagicMock()
            ticker_list = TickerList(root, on_content_changed=on_content_changed)
            ticker_list.set_tickers(["PETR4"])

            ticker_list._save_snapshot()
            ticker_list._text.delete("1.0", tk.END)
            ticker_list._text.insert("1.0", "PETR4\nVALE3")
            ticker_list._restore_from_snapshot_edit()

            on_content_changed.assert_called_once()
        finally:
            root.destroy()

    def test_selecao_nao_dispara(self):
        root = tk.Tk()
        try:
            on_content_changed = MagicMock()
            ticker_list = TickerList(root, on_content_changed=on_content_changed)
            ticker_list.set_tickers(["PETR4", "VALE3"])

            ticker_list._on_listbox_select()

            on_content_changed.assert_not_called()
        finally:
            root.destroy()

    def test_conteudo_inalterado_nao_dispara(self):
        root = tk.Tk()
        try:
            on_content_changed = MagicMock()
            ticker_list = TickerList(root, on_content_changed=on_content_changed)
            ticker_list.set_tickers(["PETR4", "VALE3"])

            ticker_list._save_snapshot()
            ticker_list._restore_from_snapshot_edit()

            on_content_changed.assert_not_called()
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
