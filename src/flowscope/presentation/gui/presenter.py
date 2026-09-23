"""Apresentador da interface gráfica, conectando a view aos casos de uso."""

import tkinter as tk
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from enum import Enum
from typing import Protocol

from flowscope.application.cancellation import CancellationToken
from flowscope.application.logging_port import LogReference
from flowscope.domain.sampling import SamplingConfig


class _BusyState(Enum):
    """Estado ocupado da interface, alternando entre ocioso e ocupado."""

    IDLE = "idle"
    BUSY = "busy"


class GUIView(Protocol):
    """Contrato da interface gráfica utilizado pelo apresentador."""

    def disable_all_buttons(self: "GUIView") -> None:
        """Desabilita todos os botões da interface."""
        ...

    def restore_all_buttons(self: "GUIView") -> None:
        """Restaura o estado anterior de todos os botões."""
        ...

    def enter_busy(self: "GUIView") -> None:
        """Exibe o cursor de espera na janela."""
        ...

    def exit_busy(self: "GUIView") -> None:
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

    def set_cancellable(self: "GUIView", cancellable: bool) -> None:
        """Mostra ou oculta o botão de interromper processamento."""
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

    def agendar(self: "GUIView", ms: int, callback: object) -> object:
        """Agenda a execução de ``callback`` na thread do Tk."""
        ...

    def set_fundamental_data(self: "GUIView", dados: dict) -> None:
        """Armazena os resultados da análise fundamentalista por ticker."""
        ...


class FlowScopePresenter:
    """Apresentador que orquestra a interação entre casos de uso e a view."""

    def __init__(self: "FlowScopePresenter", view: GUIView) -> None:
        """Inicializa o apresentador com a view de referência."""
        self._view = view
        self._operacoes_ativas = 0
        self._estado = _BusyState.IDLE
        self._dados_disponiveis = False
        self._cancel_token = CancellationToken()
        self._jobs_cancelaveis = 0

    @property
    def cancel_token(self: "FlowScopePresenter") -> CancellationToken:
        """Retorna o token de cancelamento compartilhado pelos jobs."""
        return self._cancel_token

    def request_cancel(self: "FlowScopePresenter") -> None:
        """Solicita o cancelamento de todos os processamentos em background."""
        self._cancel_token.request()

    def job_cancelavel_iniciado(self: "FlowScopePresenter") -> None:
        """Contabiliza o início de um job cancelável e exibe o botão."""
        self._jobs_cancelaveis += 1
        self._view.set_cancellable(True)

    def job_cancelavel_finalizado(self: "FlowScopePresenter") -> None:
        """Contabiliza o fim de um job cancelável e oculta o botão no último."""
        if self._jobs_cancelaveis == 0:
            return
        self._jobs_cancelaveis -= 1
        if self._jobs_cancelaveis == 0:
            self._view.set_cancellable(False)

    def enter(self: "FlowScopePresenter") -> None:
        """Contabiliza o início de uma operação, entrando no estado ocupado.

        Na transição de ocioso para ocupado (primeira operação ativa), desabilita
        os controles e aplica o cursor de espera. Operações sobrepostas apenas
        incrementam a contagem, sem repetir os efeitos colaterais.
        """
        self._operacoes_ativas += 1
        if self._estado is _BusyState.IDLE:
            self._estado = _BusyState.BUSY
            self._cancel_token.clear()
            self._view.disable_all_buttons()
            self._view.enter_busy()

    def exit(self: "FlowScopePresenter") -> None:
        """Contabiliza o término de uma operação, restaurando ao chegar a zero.

        Na transição de ocupado para ocioso (última operação ativa), restaura os
        controles, o cursor e a barra de progresso. Chamadas sem operação ativa
        são ignoradas, mantendo a transição idempotente.
        """
        if self._operacoes_ativas == 0:
            return
        self._operacoes_ativas -= 1
        if self._operacoes_ativas == 0 and self._estado is _BusyState.BUSY:
            self._estado = _BusyState.IDLE
            self._view.restore_all_buttons()
            self._view.exit_busy()
            self._view.clear_progress()
            self._jobs_cancelaveis = 0
            self._view.set_cancellable(False)
            if self._cancel_token.is_set:
                self._view.set_status("Processamento interrompido.", "⚠")
            self._sincronizar_copy_button()

    @contextmanager
    def busy(self: "FlowScopePresenter") -> Iterator[None]:
        """Garante entrada/saída balanceadas do estado ocupado, mesmo em erro."""
        self.enter()
        try:
            yield
        finally:
            self.exit()

    def on_operation_started(self: "FlowScopePresenter") -> None:
        """Notifica a view sobre o início de uma operação."""
        self.enter()

    def on_operation_finished(self: "FlowScopePresenter") -> None:
        """Notifica a view sobre o fim de uma operação.

        Restaura os controles apenas quando todas as operações (incluindo a
        análise fundamentalista) terminam, mantendo-os desabilitados durante a
        fase fundamental.
        """
        self.exit()

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
        self._dados_disponiveis = True
        self._sincronizar_copy_button()
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

    def _sincronizar_copy_button(self: "FlowScopePresenter") -> None:
        """Habilita a cópia apenas com dados carregados e nenhuma operação ativa."""
        if self._dados_disponiveis and self._operacoes_ativas == 0:
            self._view.config_copy_button_state(tk.NORMAL)
        else:
            self._view.config_copy_button_state(tk.DISABLED)

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

    def agendar(self: "FlowScopePresenter", ms: int, callback: object) -> object:
        """Agenda a execução de ``callback`` na thread do Tk."""
        return self._view.agendar(ms, callback)

    def on_fundamental_started(self: "FlowScopePresenter") -> None:
        """Sinaliza o início da análise fundamentalista em background."""
        self.enter()

    def on_fundamental_finished(self: "FlowScopePresenter") -> None:
        """Sinaliza o fim da análise fundamentalista e libera os controles."""
        self.exit()

    def on_fundamental_progress(
        self: "FlowScopePresenter",
        detalhe: str,
        current: int | None = None,
        total: int | None = None,
    ) -> None:
        """Exibe o progresso da análise fundamentalista na barra de status.

        Com ``current``/``total`` informados, atualiza a barra de progresso;
        sem eles, exibe apenas o texto na barra de status.
        """
        if current is None or total is None:
            self._view.set_status(detalhe, "•")
            return
        self._view.set_progress(current, total, f"• {detalhe}")

    def on_fundamental_result(
        self: "FlowScopePresenter", dados: dict, houve_falha: bool = False
    ) -> None:
        """Armazena os resultados e exibe o desfecho da carga."""
        self._view.set_fundamental_data(dados)
        if houve_falha:
            self._view.set_status(
                "Dados atualizados com mitigação de falhas.", "⚠"
            )
        else:
            self._view.set_status("Dados atualizados com sucesso.", "✓")
        self._view.on_tab_changed()

    def on_fundamental_error(self: "FlowScopePresenter") -> None:
        """Exibe a falha catastrófica da análise fundamentalista."""
        self._view.set_status("Falha ao atualizar dados", "⚠")

    @property
    def _gui(self: "FlowScopePresenter") -> GUIView:
        """Retorna a view associada ao apresentador."""
        return self._view
