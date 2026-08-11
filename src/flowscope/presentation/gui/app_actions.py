"""Ações de configuração e atualização de gráficos da interface gráfica."""

import tkinter as tk
from datetime import datetime, timezone

from flowscope.domain.sampling import SamplingConfig
from flowscope.presentation.gui.charts.quadrant_chart import QuadrantChart


class ActionsMixin:
    """Lida com eventos de seleção de período, amostragem e atualização dos gráficos."""

    def _on_period_combo_changed(self: "ActionsMixin", event: tk.Event | None = None) -> None:
        text = self._PERIOD_STATUS.get(self._period_var.get(), "")
        if text:
            self._set_status(text)
        if self._current_data:
            self._controller.on_load_data()

    def _update_sampling_label(self: "ActionsMixin") -> None:
        text = self._SAMPLING_STATUS.get(self._sampling_var.get(), "")
        self._sampling_label.config(text=text)

    def _on_sampling_combo_changed(self: "ActionsMixin", event: tk.Event | None = None) -> None:
        self._update_sampling_label()
        if self._current_data:
            self._controller.on_load_data()

    def get_sampling_config(self: "ActionsMixin") -> SamplingConfig:
        """Retorna a configuração de amostragem selecionada na interface."""
        period_map = {
            "Últimos 30 dias": 30,
            "Últimos 60 dias (cache)": 60,
            "Últimos 90 dias (cache)": 90,
        }
        sampling_map = {
            "Fibonacci": "fibonacci",
            "Fibonacci reverso": "fibonacci_reverse",
            "Fibonacci duplo": "fibonacci_double",
            "Monte Carlo": "monte_carlo",
            "Monte Carlo duplo": "monte_carlo_double",
            "Todos os dias": "all_days",
        }
        return SamplingConfig(
            period_days=period_map.get(self._period_var.get(), 30),
            method=sampling_map.get(self._sampling_var.get(), "fibonacci"),
        )

    def _on_today(self: "ActionsMixin") -> None:
        self._date_entry.set_date(datetime.now(timezone.utc).date())
        self._controller.on_load_data()

    def _on_load_data(self: "ActionsMixin") -> None:
        self._controller.on_load_data()

    def _get_selected_ticker(self: "ActionsMixin") -> str | None:
        selected = self._ticker_list.get_tickers()
        if selected:
            return selected[0]
        all_tickers = self._ticker_list.get_all_listbox_tickers()
        if all_tickers:
            return all_tickers[0]
        return None

    def _resolve_chart(self: "ActionsMixin", main_tab: str, sub_tab: str) -> object | None:
        if main_tab == "Análise Geral":
            return self._GENERAL.get(sub_tab)
        return self._TICKER.get(sub_tab)

    def _resolve_current_chart(self: "ActionsMixin") -> object | None:
        try:
            main_tab = self._main_notebook.tab(self._main_notebook.select(), "text")
            if main_tab == "Análise Geral":
                sub_tab = self._general_notebook.tab(self._general_notebook.select(), "text")
            else:
                sub_tab = self._ticker_notebook.tab(self._ticker_notebook.select(), "text")
            return self._resolve_chart(main_tab, sub_tab)
        except tk.TclError:
            return None

    def _do_update(self: "ActionsMixin", chart: object) -> None:
        tickers = self._ticker_list.get_tickers()
        filtered = {t: self._current_data.get(t) for t in tickers if t in self._current_data}
        if isinstance(chart, QuadrantChart):
            chart.update(filtered, show_arrows=(len(filtered) == 1))
        elif chart in self._ticker_charts:
            chart.update(self._current_data, ticker=self._get_selected_ticker())
        else:
            chart.update(filtered)

    def _copy_chart(self: "ActionsMixin", figure: object) -> None:
        from flowscope.infrastructure.clipboard_image import (
            ClipboardError,
            copy_image_to_clipboard,
        )

        self._set_wait_cursor()
        try:
            copy_image_to_clipboard(figure)
            self._flash_status("Gráfico copiado!")
        except ClipboardError as e:
            self._set_status(f"Erro: {e}", "⚠")
        finally:
            self._clear_wait_cursor()
