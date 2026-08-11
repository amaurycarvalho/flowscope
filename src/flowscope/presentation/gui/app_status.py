"""Estado, barra de status e métodos do protocolo GUIView do FlowScope."""

import tkinter as tk
from datetime import date
from typing import ClassVar

from flowscope.presentation.gui.app_constants import PAD_SMALL


class StatusMixin:
    """Gerencia a barra de status, cursor e estado dos controles da janela."""

    _PERIOD_STATUS: ClassVar[dict[str, str]] = {
        "Últimos 30 dias": "Janela de 30 dias corridos. Os dados serão baixados da B3 e armazenados em cache.",
        "Últimos 60 dias (cache)": "Janela de 60 dias corridos. Apenas dados já em cache serão utilizados — sem download da B3.",
        "Últimos 90 dias (cache)": "Janela de 90 dias corridos. Apenas dados já em cache serão utilizados — sem download da B3.",
    }

    _SAMPLING_STATUS: ClassVar[dict[str, str]] = {
        "Fibonacci": "Amostra concentrada nas datas mais recentes.",
        "Fibonacci reverso": "Amostra concentrada nas datas mais distantes.",
        "Fibonacci duplo": "Amostra concentrada nas margens do período.",
        "Monte Carlo": "Amostra das margens do período com centro aleatório disperso.",
        "Monte Carlo duplo": "Amostra das margens com centro aleatório concentrado.",
        "Todos os dias": "Amostra contendo todos os dias.",
    }

    def _set_status(self: "StatusMixin", msg: str, icon: str = "") -> None:
        text = f"{icon} {msg}" if icon else msg
        self._status_var.set(text)
        self._progress_bar.pack_forget()

    def _set_progress(self: "StatusMixin", current: int, total: int, label: str) -> None:
        pct = int(current / max(total, 1) * 100) if total > 0 else 100
        self._status_var.set(label)
        self._progress_bar["value"] = pct
        self._progress_bar.pack(side=tk.RIGHT, padx=PAD_SMALL)
        self.update_idletasks()

    def _flash_status(self: "StatusMixin", msg: str, icon: str = "✓", clear_ms: int = 2500) -> None:
        if self._flash_after_id:
            self.after_cancel(self._flash_after_id)
        self._set_status(msg, icon)
        self._flash_after_id = self.after(clear_ms, lambda: self._set_status("Pronto."))

    def _set_wait_cursor(self: "StatusMixin") -> None:
        self.config(cursor="watch")
        self.update_idletasks()

    def _clear_wait_cursor(self: "StatusMixin") -> None:
        self.config(cursor="")

    def _disable_all_buttons(self: "StatusMixin") -> None:
        if self._flash_after_id:
            self.after_cancel(self._flash_after_id)
            self._flash_after_id = None
        self._button_states: dict[tk.Widget, str] = {}
        gui_buttons = [
            self._load_button, self._today_button,
        ]
        if self._shortcut_btn:
            gui_buttons.append(self._shortcut_btn)
        for btn in gui_buttons:
            self._button_states[btn] = btn.cget("state")
            btn.config(state=tk.DISABLED)
        self._copy_data_btn.config(state=tk.DISABLED)
        for btn in self._ticker_list.all_buttons():
            self._button_states[btn] = btn.cget("state")
            btn.config(state=tk.DISABLED)
        for combo in (self._period_combo, self._sampling_combo):
            self._button_states[combo] = str(combo.cget("state"))
            combo.config(state=tk.DISABLED)
        self._button_states[self._date_entry] = str(self._date_entry.cget("state"))
        self._date_entry.config(state=tk.DISABLED)

    def _restore_all_buttons(self: "StatusMixin") -> None:
        if not hasattr(self, "_button_states"):
            return
        for widget, state in self._button_states.items():
            try:
                widget.config(state=state)
            except tk.TclError:
                pass
        self._button_states = {}

    # ── GUIView protocol public methods ──────────────────────────────

    def disable_all_buttons(self: "StatusMixin") -> None:
        """Desabilita todos os botões da interface."""
        self._disable_all_buttons()

    def restore_all_buttons(self: "StatusMixin") -> None:
        """Restaura o estado anterior de todos os botões."""
        self._restore_all_buttons()

    def set_wait_cursor(self: "StatusMixin") -> None:
        """Exibe o cursor de espera na janela."""
        self._set_wait_cursor()

    def clear_wait_cursor(self: "StatusMixin") -> None:
        """Restaura o cursor padrão da janela."""
        self._clear_wait_cursor()

    def set_progress(self: "StatusMixin", current: int, total: int, label: str) -> None:
        """Atualiza a barra de progresso da barra de status."""
        self._set_progress(current, total, label)

    def set_status(self: "StatusMixin", msg: str, icon: str = "") -> None:
        """Exibe uma mensagem na barra de status."""
        self._set_status(msg, icon)

    def get_reference_date(self: "StatusMixin") -> date:
        """Retorna a data de referência selecionada na interface."""
        return self._date_entry.get_date()

    def get_current_tickers(self: "StatusMixin") -> list[str]:
        """Retorna a lista de tickers atualmente exibidos."""
        return self._ticker_list.get_all_listbox_tickers()

    def set_tickers(self: "StatusMixin", tickers: list[str]) -> None:
        """Define a lista de tickers exibidos na lista de tickers."""
        self._ticker_list.set_tickers(tickers)

    def set_counter(self: "StatusMixin", text: str) -> None:
        """Define o texto do contador de tickers."""
        self._ticker_list.set_counter(text)

    def config_copy_button_state(self: "StatusMixin", state: str) -> None:
        """Configura o estado do botão de copiar dados."""
        self._copy_data_btn.config(state=state)

    def on_tab_changed(self: "StatusMixin") -> None:
        """Notifica a interface sobre a troca de aba."""
        self._on_tab_changed()

    def clear_progress(self: "StatusMixin") -> None:
        """Limpa a barra de progresso da barra de status."""
        self._progress_bar.pack_forget()
        self._progress_bar["value"] = 0

    def set_current_data(self: "StatusMixin", data: dict) -> None:
        """Armazena os dados carregados da análise atual."""
        self._current_data = {k: v for k, v in data.items() if not k.startswith("_")}
        self._sampling_dates = data.get("_sampling_dates", [])

    def set_tickers_list(self: "StatusMixin", tickers: list[str]) -> None:
        """Define a lista completa de tickers da análise."""
        self._tickers = list(tickers)

    def set_date_label(self: "StatusMixin", text: str) -> None:
        """Define o texto do rótulo de data na barra superior."""
        self._date_label.config(text=text)
