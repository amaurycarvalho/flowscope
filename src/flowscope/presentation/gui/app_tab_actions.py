"""Ações relacionadas a abas, resumos e indicadores da interface."""

import tkinter as tk

from flowscope.presentation.gui.app_indicators import (
    build_extra_indicator_lines,
    build_full_indicator_lines,
    build_indicator_lines,
    insert_indicators,
)


class TabActionsMixin:
    """Lida com eventos de abas, resumos e formatação de indicadores."""

    def _current_tabs(self: "TabActionsMixin") -> tuple[str, str] | None:
        try:
            main_tab = self._main_notebook.tab(self._main_notebook.select(), "text")
            if main_tab == "Análise Geral":
                sub_tab = self._general_notebook.tab(self._general_notebook.select(), "text")
            else:
                sub_tab = self._ticker_notebook.tab(self._ticker_notebook.select(), "text")
            return main_tab, sub_tab
        except tk.TclError:
            return None

    def _on_tab_changed(self: "TabActionsMixin", event: tk.Event | None = None) -> None:
        tabs = self._current_tabs()
        if tabs is None:
            return
        main_tab, sub_tab = tabs

        if self._current_data:
            chart = self._resolve_chart(main_tab, sub_tab)
            if chart:
                self._do_update(chart)
            self._update_ticker_counter()

        content = self._tab_content.get((main_tab, sub_tab))
        if content:
            self._orientation_panel.set_content(*content)

        self._prefs["last_tab"] = main_tab
        self._prefs["last_subtab"] = sub_tab

    def _on_ticker_edit(self: "TabActionsMixin") -> None:
        self._controller.on_ticker_edit()

    def _show_summary(self: "TabActionsMixin", main_tab: str, sub_tab: str,
                      expected_main: str, expected_sub: str,
                      title: str, content_key: tuple[str, str], summary: str) -> None:
        if main_tab != expected_main or sub_tab != expected_sub:
            return
        body = self._tab_content.get(content_key, ("", []))[1]
        self._orientation_panel.set_content(
            title,
            body + [("\n\n---\n\n" + summary, "")],
        )

    def _on_quadrant_summary(self: "TabActionsMixin", summary: str) -> None:
        try:
            tabs = self._current_tabs()
            if tabs is None:
                return
            self._show_summary(
                *tabs, "Análise Geral", "Quadrantes",
                "Quadrantes — CLV vs VWAP Distance",
                ("Análise Geral", "Quadrantes"), summary,
            )
        except (tk.TclError, KeyError):
            pass

    def _on_flow_summary(self: "TabActionsMixin", summary: str) -> None:
        try:
            tabs = self._current_tabs()
            if tabs is None:
                return
            self._show_summary(
                *tabs, "Análise do Ticker", "Fluxo Financeiro",
                "Fluxo Financeiro — Daily Money Flow",
                ("Análise do Ticker", "Fluxo Financeiro"), summary,
            )
        except (tk.TclError, KeyError):
            pass

    def _update_ticker_counter(self: "TabActionsMixin") -> None:
        all_listbox = self._ticker_list.get_all_listbox_tickers()
        n_total = len(all_listbox)
        if not self._current_data:
            if n_total > 0:
                self._ticker_list.set_counter(f"Tickers ({n_total})")
            return
        filtered = self._ticker_list.get_tickers()
        active = [t for t in filtered if t in self._current_data]
        n_filtered = len(active)
        if n_filtered < n_total and n_total > 0:
            self._ticker_list.set_counter(f"Exibindo {n_filtered} de {n_total} ativos")
        elif n_total > 0:
            self._ticker_list.set_counter(f"Tickers ({n_total})")

    def _format_selected_indicators(
        self: "TabActionsMixin", text_w: tk.Text, ticker: str, data: dict, keys: tuple[str, ...],
    ) -> None:
        all_inds = data.get("all_indicators", {})
        if isinstance(all_inds, dict) and "_ticker" not in all_inds:
            data = dict(data)
            data["_ticker"] = ticker
        lines = build_indicator_lines(data, keys)
        insert_indicators(text_w, lines)

    def _format_all_indicators(self: "TabActionsMixin", text_w: tk.Text, ticker: str, data: dict) -> None:
        keys = (
            "range", "range_percentual", "typical_price", "median_price",
            "weighted_close", "clv", "money_flow_multiplier",
            "money_flow_volume", "buying_pressure", "selling_pressure",
            "average_trade_size", "average_financial_ticket",
            "daily_efficiency", "dominance_score", "financial_density",
            "trade_density", "volume_density", "vwap_distance",
        )
        lines = build_full_indicator_lines(data, keys)
        insert_indicators(text_w, lines)
        insert_indicators(text_w, build_extra_indicator_lines(data))
