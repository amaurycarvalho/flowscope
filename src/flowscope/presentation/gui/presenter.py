import tkinter as tk
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flowscope.presentation.gui.app import FlowScopeGUI


class FlowScopePresenter:
    def __init__(self, gui: "FlowScopeGUI"):
        self._gui = gui

    def on_operation_started(self) -> None:
        self._gui._disable_all_buttons()
        self._gui._set_wait_cursor()

    def on_operation_finished(self) -> None:
        self._gui._restore_all_buttons()
        self._gui._clear_wait_cursor()
        self._gui._progress_bar.pack_forget()
        self._gui._progress_bar["value"] = 0

    def on_portfolio_loaded(self, tickers: list[str]) -> None:
        self._gui._ticker_list.set_tickers(tickers)

    def on_progress(self, current: int, total: int, label: str) -> None:
        self._gui._set_progress(current, total, label)

    def on_result(
        self, result: dict, tickers: list[str], ref_date: date,
    ) -> None:
        gui = self._gui
        gui._current_data = result
        gui._tickers = list(tickers)
        gui._copy_data_btn.config(state=tk.NORMAL)
        gui._ticker_list.set_counter(f"Tickers ({len(tickers)})")
        gui._date_label.config(text=f"Dados: {ref_date}")
        gui._on_tab_changed()
        gui._set_status(
            f"{len(tickers)} ticker{'s' if len(tickers) != 1 else ''} "
            f"carregado{'s' if len(tickers) != 1 else ''} para {ref_date}.",
            "✓",
        )

    def on_error(self, error: Exception) -> None:
        self._gui._set_status(
            f"Não foi possível carregar os dados. {error}", "⚠",
        )

    def get_reference_date(self) -> date:
        return self._gui._date_entry.get_date()

    def get_current_tickers(self) -> list[str]:
        return self._gui._ticker_list.get_all_listbox_tickers()
