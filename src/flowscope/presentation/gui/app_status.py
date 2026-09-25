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

    #: Cursores transitórios geridos pelo Tk durante ``<Motion>`` sobre
    #: separadores de coluna de tabelas e sashes de painéis divididos. Não são
    #: cursores de repouso e não DEVEM ser usados como baseline do snapshot.
    _CURSORES_TRANSITORIOS: ClassVar[frozenset[str]] = frozenset({
        "hresize",
        "sb_h_double_arrow",
        "sb_v_double_arrow",
    })

    def _ocultar_botao_interromper(self: "StatusMixin") -> None:
        botao = getattr(self, "_stop_button", None)
        if botao is not None:
            botao.pack_forget()

    def _on_stop_clicked(self: "StatusMixin") -> None:
        """Solicita ao apresentador a interrupção dos processamentos ativos."""
        self._presenter.request_cancel()

    def set_cancellable(self: "StatusMixin", cancellable: bool) -> None:
        """Mostra ou oculta o botão de interromper conforme a operação ativa."""
        self._stop_button_visivel = bool(cancellable)
        botao = getattr(self, "_stop_button", None)
        if botao is None:
            return
        if cancellable:
            botao.pack(side=tk.RIGHT, padx=PAD_SMALL)
        else:
            botao.pack_forget()

    def _set_status(self: "StatusMixin", msg: str, icon: str = "") -> None:
        text = f"{icon} {msg}" if icon else msg
        self._status_var.set(text)
        self._progress_bar.pack_forget()
        self._ocultar_botao_interromper()

    def _set_progress(self: "StatusMixin", current: int, total: int, label: str) -> None:
        pct = int(current / max(total, 1) * 100) if total > 0 else 100
        self._status_var.set(label)
        self._progress_bar["value"] = pct
        self._progress_bar.pack(side=tk.RIGHT, padx=PAD_SMALL)
        if getattr(self, "_stop_button_visivel", False):
            botao = getattr(self, "_stop_button", None)
            if botao is not None:
                botao.pack(side=tk.RIGHT, padx=PAD_SMALL)
        self.update_idletasks()

    def _flash_status(self: "StatusMixin", msg: str, icon: str = "✓", clear_ms: int = 2500) -> None:
        if self._flash_after_id:
            self.after_cancel(self._flash_after_id)
        self._set_status(msg, icon)
        self._flash_after_id = self.after(clear_ms, lambda: self._set_status("Pronto."))

    @classmethod
    def _cursor_de_repouso(cls: "StatusMixin", widget: tk.Widget) -> str:
        """Retorna o cursor de repouso do widget, ignorando transitórios do Tk.

        O ``cget("cursor")`` pode devolver uma lista Tcl — por exemplo
        ``('sb_h_double_arrow',)`` quando o toolkit geriu o cursor via
        ``<Motion>`` sobre um separador. Normalizamos para o nome do cursor e
        tratamos os cursores transitórios de separador/sash como repouso (vazio),
        de modo que nunca sejam usados como baseline da restauração.
        """
        try:
            atual = widget.cget("cursor")
        except tk.TclError:
            return ""
        if isinstance(atual, (tuple, list)):
            atual = atual[0] if atual else ""
        texto = str(atual)
        return "" if texto in cls._CURSORES_TRANSITORIOS else texto

    def _set_wait_cursor(self: "StatusMixin") -> None:
        if not getattr(self, "_cursor_states", None):
            estados: dict[tk.Widget, str] = {}
            for widget in self._iter_widgets():
                estados[widget] = self._cursor_de_repouso(widget)
                try:
                    widget.config(cursor="watch")
                except tk.TclError:
                    pass
            self._cursor_states = estados
        self._instalar_hook_motion_busy()
        self.update_idletasks()

    def _clear_wait_cursor(self: "StatusMixin") -> None:
        self._remover_hook_motion_busy()
        for widget, cursor in getattr(self, "_cursor_states", {}).items():
            try:
                widget.config(cursor=cursor)
            except tk.TclError:
                try:
                    widget.config(cursor="")
                except tk.TclError:
                    pass
        self._cursor_states = {}

    def _instalar_hook_motion_busy(self: "StatusMixin") -> None:
        """Reafirma o cursor de espera em ``<Motion>`` enquanto ocupado.

        O hook global roda depois dos bindings de classe do Tk (widget ->
        classe -> toplevel -> all), sobrepondo cursores transitórios como o
        ``hresize`` de separadores de coluna e o ``sb_*`` de sashes.
        """
        if getattr(self, "_busy_motion_id", None) is not None:
            return
        try:
            self._busy_motion_id = self.bind_all(
                "<Motion>", self._on_busy_motion, add="+"
            )
        except tk.TclError:
            self._busy_motion_id = None

    def _remover_hook_motion_busy(self: "StatusMixin") -> None:
        funcid = getattr(self, "_busy_motion_id", None)
        if funcid is None:
            return
        try:
            self.unbind_all("<Motion>")
        except tk.TclError:
            pass
        try:
            self.deletecommand(funcid)
        except tk.TclError:
            pass
        self._busy_motion_id = None

    def _on_busy_motion(self: "StatusMixin", event: tk.Event) -> None:
        """Reaplica o cursor de espera ao widget sob o ponteiro."""
        widget = getattr(event, "widget", None)
        if widget is None:
            return
        try:
            if self._cursor_de_repouso(widget) != "watch":
                widget.config(cursor="watch")
        except (tk.TclError, AttributeError):
            pass

    def _iter_widgets(self: "StatusMixin") -> list[tk.Widget]:
        """Percorre a árvore de widgets a partir da janela, em profundidade."""
        pilha: list[tk.Widget] = [self]
        widgets: list[tk.Widget] = []
        while pilha:
            widget = pilha.pop()
            widgets.append(widget)
            try:
                pilha.extend(widget.winfo_children())
            except tk.TclError:
                continue
        return widgets

    def _disable_all_buttons(self: "StatusMixin") -> None:
        if self._flash_after_id:
            self.after_cancel(self._flash_after_id)
            self._flash_after_id = None
        if getattr(self, "_button_states", None):
            return
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
        for nome in ("_documents_panel", "_noticias_panel"):
            painel = getattr(self, nome, None)
            if painel is None:
                continue
            for btn in painel.all_buttons():
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
        for nome in ("_documents_panel", "_noticias_panel"):
            painel = getattr(self, nome, None)
            if painel is not None:
                painel.refresh_open_button()
                painel.refresh_resumir_button()

    # ── GUIView protocol public methods ──────────────────────────────

    def disable_all_buttons(self: "StatusMixin") -> None:
        """Desabilita todos os botões da interface."""
        self._disable_all_buttons()

    def restore_all_buttons(self: "StatusMixin") -> None:
        """Restaura o estado anterior de todos os botões."""
        self._restore_all_buttons()

    def enter_busy(self: "StatusMixin") -> None:
        """Exibe o cursor de espera na janela."""
        self._set_wait_cursor()

    def exit_busy(self: "StatusMixin") -> None:
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
        """Limpa a barra de progresso e o botão de interromper da barra de status."""
        self._progress_bar.pack_forget()
        self._progress_bar["value"] = 0
        self._ocultar_botao_interromper()

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
