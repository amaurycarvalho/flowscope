"""Ações relacionadas a abas, resumos e indicadores da interface."""

import tkinter as tk

from flowscope.application.llm_config_port import LLMConfigPort
from flowscope.presentation.gui.app_indicators import (
    build_extra_indicator_lines,
    build_full_indicator_lines,
    build_indicator_lines,
    insert_indicators,
)
from flowscope.presentation.gui.app_tabs import ABOUT_TAB, CHAT_AI_TAB
from flowscope.presentation.gui.llm.config_dialog import LLMConfigDialog


class TabActionsMixin:
    """Lida com eventos de abas, resumos e formatação de indicadores."""

    #: Porta de configuração da LLM; injetada pelo composition root.
    _llm_config: LLMConfigPort | None = None

    def _current_tabs(self: "TabActionsMixin") -> tuple[str, str] | None:
        try:
            main_tab = self._main_notebook.tab(self._main_notebook.select(), "text")
            if main_tab in (ABOUT_TAB, CHAT_AI_TAB):
                return main_tab, main_tab
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

        if main_tab == ABOUT_TAB:
            self._prefs["last_tab"] = main_tab
            content = self._tab_content.get((ABOUT_TAB, ABOUT_TAB))
            if content:
                self._orientation_panel.set_content(*content)
            self._verificar_nova_versao()
            return

        if main_tab == CHAT_AI_TAB:
            self._prefs["last_tab"] = main_tab
            content = self._tab_content.get((CHAT_AI_TAB, CHAT_AI_TAB))
            if content:
                self._orientation_panel.set_content(*content)
            self._sync_fundamental_refresh_visibility(main_tab, sub_tab)
            self._sync_copy_button_for_tab(main_tab, sub_tab)
            self._reavaliar_chat_llm()
            return

        chart = self._resolve_chart(main_tab, sub_tab)
        if chart is not None and self._deve_atualizar(chart):
            self._do_update(chart)
        if self._current_data:
            self._update_ticker_counter()

        content = self._tab_content.get((main_tab, sub_tab))
        if content:
            self._orientation_panel.set_content(*content)

        self._prefs["last_tab"] = main_tab
        self._prefs["last_subtab"] = sub_tab
        self._sync_fundamental_refresh_visibility(main_tab, sub_tab)
        self._sync_copy_button_for_tab(main_tab, sub_tab)

    def _sync_copy_button_for_tab(
        self: "TabActionsMixin", main_tab: str, sub_tab: str
    ) -> None:
        """Habilita a cópia na sub-aba Documentos e na aba "Chat AI".

        Nas demais abas, restaura o estado conforme a existência de dados. Um
        bloqueio global em andamento (``_button_states``) não é sobrescrito.
        """
        botao = getattr(self, "_copy_data_btn", None)
        if botao is None or getattr(self, "_button_states", None):
            return
        em_documentos = (main_tab, sub_tab) == ("Análise do Ticker", "Documentos")
        em_noticias = (main_tab, sub_tab) == ("Análise Geral", "Notícias")
        em_chat = main_tab == CHAT_AI_TAB
        if em_documentos or em_noticias or em_chat or getattr(self, "_current_data", None):
            botao.config(state=tk.NORMAL)
        else:
            botao.config(state=tk.DISABLED)

    def _sync_fundamental_refresh_visibility(
        self: "TabActionsMixin", main_tab: str, sub_tab: str
    ) -> None:
        """Exibe o botão de atualização de fundamentos só na sub-aba Fundamentos."""
        button = getattr(self, "_fundamental_refresh_btn", None)
        if button is None:
            return
        self._ticker_list.set_action_button_visible(
            button, (main_tab, sub_tab) == ("Análise Geral", "Fundamentos")
        )

    def _deve_atualizar(self: "TabActionsMixin", chart: object) -> bool:
        """Indica se o painel deve ser atualizado mesmo sem dados da B3.

        As sub-abas de evolução dos fundamentos e de documentos leem apenas
        caches locais e por isso são atualizadas independentemente de haver
        carga B3 corrente.
        """
        if self._current_data:
            return True
        return chart in (
            getattr(self, "_fundamental_evolution_panel", None),
            getattr(self, "_documents_panel", None),
            getattr(self, "_noticias_panel", None),
        )

    @staticmethod
    def _select_tab(notebook: object, texto: str) -> bool:
        """Seleciona a sub-aba com o texto informado, se existir."""
        try:
            for indice in range(notebook.index("end")):
                if notebook.tab(indice, "text") == texto:
                    notebook.select(indice)
                    return True
        except tk.TclError:
            return False
        return False

    def _on_fundamental_ticker_selected(self: "TabActionsMixin", ticker: str) -> None:
        """Atualiza o ticker apresentado nas sub-abas da Análise do Ticker."""
        if ticker:
            self._ticker_selecionado = ticker

    def _abrir_config_llm(self: "TabActionsMixin") -> None:
        """Abre o diálogo de configuração de LLM, reavaliando ao salvar."""
        paineis = [
            getattr(self, "_documents_panel", None),
            getattr(self, "_noticias_panel", None),
        ]

        def _on_saved() -> None:
            for painel in paineis:
                if painel is not None:
                    painel.refresh_resumir_button()
            self._reavaliar_chat_llm()

        LLMConfigDialog(
            self, config_port=self._llm_config, on_saved=_on_saved
        )

    def _reavaliar_chat_llm(self: "TabActionsMixin") -> None:
        """Reavalia o estado de configuração do painel de chat."""
        painel = getattr(self, "_chat_panel", None)
        if painel is not None:
            painel.avaliar_estado()

    def _on_fundamental_row_activated(self: "TabActionsMixin", ticker: str) -> None:
        """Ativa a sub-aba de evolução dos fundamentos para o ticker."""
        if not ticker:
            return
        self._ticker_selecionado = ticker
        if self._select_tab(self._main_notebook, "Análise do Ticker"):
            self._select_tab(self._ticker_notebook, "Evolução dos Fundamentos")

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
