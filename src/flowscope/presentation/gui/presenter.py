"""Apresentador da interface gráfica, conectando a view aos casos de uso."""

import tkinter as tk
from datetime import date
from typing import Protocol

from flowscope.application.logging_port import LogReference
from flowscope.domain.sampling import SamplingConfig


class GUIView(Protocol):
    """Contrato da interface gráfica utilizado pelo apresentador."""

    def disable_all_buttons(self: "GUIView") -> None:
        """Desabilita todos os botões da interface."""
        ...

    def restore_all_buttons(self: "GUIView") -> None:
        """Restaura o estado anterior de todos os botões."""
        ...

    def set_wait_cursor(self: "GUIView") -> None:
        """Exibe o cursor de espera na janela."""
        ...

    def clear_wait_cursor(self: "GUIView") -> None:
        """Restaura o cursor padrão da janela."""
        ...

    def set_progress(self: "GUIView", current: int, total: int, label: str) -> None:
        """Atualiza a barra de progresso da barra de status."""
        ...

    def set_status(self: "GUIView", msg: str, icon: str = "") -> None:
        """Exibe uma mensagem na barra de status."""
        ...

    def get_reference_date(self: "GUIView") -> date:
        """Retorna a data de referência selecionada na interface."""
        ...

    def get_current_tickers(self: "GUIView") -> list[str]:
        """Retorna a lista de tickers atualmente exibidos."""
        ...

    def set_tickers(self: "GUIView", tickers: list[str]) -> None:
        """Define a lista de tickers exibidos na lista de tickers."""
        ...

    def set_counter(self: "GUIView", text: str) -> None:
        """Define o texto do contador de tickers."""
        ...

    def config_copy_button_state(self: "GUIView", state: str) -> None:
        """Configura o estado do botão de copiar dados."""
        ...

    def on_tab_changed(self: "GUIView") -> None:
        """Notifica a interface sobre a troca de aba."""
        ...

    def clear_progress(self: "GUIView") -> None:
        """Limpa a barra de progresso da barra de status."""
        ...

    def set_current_data(self: "GUIView", data: dict) -> None:
        """Armazena os dados carregados da análise atual."""
        ...

    def set_tickers_list(self: "GUIView", tickers: list[str]) -> None:
        """Define a lista completa de tickers da análise."""
        ...

    def set_date_label(self: "GUIView", text: str) -> None:
        """Define o texto do rótulo de data na barra superior."""
        ...

    def get_sampling_config(self: "GUIView") -> SamplingConfig:
        """Retorna a configuração de amostragem selecionada na interface."""
        ...


class FlowScopePresenter:
    """Apresentador que orquestra a interação entre casos de uso e a view."""

    def __init__(self: "FlowScopePresenter", view: GUIView) -> None:
        """Inicializa o apresentador com a view de referência."""
        self._view = view

    def on_operation_started(self: "FlowScopePresenter") -> None:
        """Notifica a view sobre o início de uma operação."""
        self._view.disable_all_buttons()
        self._view.set_wait_cursor()

    def on_operation_finished(self: "FlowScopePresenter") -> None:
        """Notifica a view sobre o fim de uma operação."""
        self._view.restore_all_buttons()
        self._view.clear_wait_cursor()
        self._view.clear_progress()

    def on_portfolio_loaded(self: "FlowScopePresenter", tickers: list[str]) -> None:
        """Exibe a carteira carregada na interface."""
        self._view.set_tickers(tickers)

    def on_progress(self: "FlowScopePresenter", current: int, total: int, label: str) -> None:
        """Propaga o progresso da operação para a view."""
        self._view.set_progress(current, total, label)

    def on_result(
        self: "FlowScopePresenter", result: dict, tickers: list[str], ref_date: date,
    ) -> None:
        """Apresenta o resultado da análise na interface."""
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

    def on_error(self: "FlowScopePresenter", error: Exception) -> None:
        """Exibe uma mensagem de erro ao usuário."""
        self._view.set_status(
            f"Não foi possível carregar os dados. {error}", "⚠",
        )

    def on_technical_error(self: "FlowScopePresenter", error: Exception, ref: LogReference) -> None:
        """Exibe mensagem de erro técnico e orienta o usuário ao arquivo de log."""
        self._view.set_status(
            "⚠ Erro técnico. Consulte o arquivo de log em "
            "~/.flowscope/logs/flowscope.log",
        )

    def get_reference_date(self: "FlowScopePresenter") -> date:
        """Retorna a data de referência fornecida pela interface."""
        return self._view.get_reference_date()

    def get_sampling_config(self: "FlowScopePresenter") -> SamplingConfig:
        """Retorna a configuração de amostragem da interface."""
        return self._view.get_sampling_config()

    def get_current_tickers(self: "FlowScopePresenter") -> list[str]:
        """Retorna os tickers atualmente selecionados na interface."""
        return self._view.get_current_tickers()

    def set_status(self: "FlowScopePresenter", msg: str, icon: str = "") -> None:
        """Define a mensagem exibida na barra de status."""
        self._view.set_status(msg, icon)

    @property
    def _gui(self: "FlowScopePresenter") -> GUIView:
        """Retorna a view associada ao apresentador."""
        return self._view
