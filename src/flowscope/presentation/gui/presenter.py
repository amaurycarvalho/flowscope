import tkinter as tk
from datetime import date
from typing import Protocol

from flowscope.application.logging_port import LogReference
from flowscope.domain.sampling import SamplingConfig


class GUIView(Protocol):
    def disable_all_buttons(self) -> None: ...
    def restore_all_buttons(self) -> None: ...
    def set_wait_cursor(self) -> None: ...
    def clear_wait_cursor(self) -> None: ...
    def set_progress(self, current: int, total: int, label: str) -> None: ...
    def set_status(self, msg: str, icon: str = "") -> None: ...
    def get_reference_date(self) -> date: ...
    def get_current_tickers(self) -> list[str]: ...
    def set_tickers(self, tickers: list[str]) -> None: ...
    def set_counter(self, text: str) -> None: ...
    def config_copy_button_state(self, state: str) -> None: ...
    def on_tab_changed(self) -> None: ...
    def clear_progress(self) -> None: ...
    def set_current_data(self, data: dict) -> None: ...
    def set_tickers_list(self, tickers: list[str]) -> None: ...
    def set_date_label(self, text: str) -> None: ...
    def get_sampling_config(self) -> SamplingConfig: ...


class FlowScopePresenter:
    def __init__(self, view: GUIView):
        self._view = view

    def on_operation_started(self) -> None:
        self._view.disable_all_buttons()
        self._view.set_wait_cursor()

    def on_operation_finished(self) -> None:
        self._view.restore_all_buttons()
        self._view.clear_wait_cursor()
        self._view.clear_progress()

    def on_portfolio_loaded(self, tickers: list[str]) -> None:
        self._view.set_tickers(tickers)

    def on_progress(self, current: int, total: int, label: str) -> None:
        self._view.set_progress(current, total, label)

    def on_result(
        self, result: dict, tickers: list[str], ref_date: date,
    ) -> None:
        self._view.set_current_data(result)
        self._view.set_tickers_list(tickers)
        self._view.config_copy_button_state(tk.NORMAL)
        self._view.set_counter(f"Tickers ({len(tickers)})")
        self._view.set_date_label(f"Dados: {ref_date}")
        self._view.on_tab_changed()
        self._view.set_status(
            f"{len(tickers)} ticker{'s' if len(tickers) != 1 else ''} "
            f"carregado{'s' if len(tickers) != 1 else ''} para {ref_date}.",
            "✓",
        )

    def on_error(self, error: Exception) -> None:
        self._view.set_status(
            f"Não foi possível carregar os dados. {error}", "⚠",
        )

    def on_technical_error(self, error: Exception, ref: LogReference) -> None:
        self._view.set_status(
            "⚠ Erro técnico. Consulte o arquivo de log em "
            "~/.flowscope/logs/flowscope.log",
        )

    def get_reference_date(self) -> date:
        return self._view.get_reference_date()

    def get_sampling_config(self) -> SamplingConfig:
        return self._view.get_sampling_config()

    def get_current_tickers(self) -> list[str]:
        return self._view.get_current_tickers()

    def set_status(self, msg: str, icon: str = "") -> None:
        self._view.set_status(msg, icon)

    @property
    def _gui(self):
        return self._view
