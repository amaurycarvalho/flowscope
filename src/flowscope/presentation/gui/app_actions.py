"""Ações de configuração e atualização de gráficos da interface gráfica."""

import logging
import queue
import time
import tkinter as tk
from datetime import date, datetime, timezone

from flowscope.domain.sampling import SamplingConfig
from flowscope.presentation.gui.app_tabs import ABOUT_TAB
from flowscope.presentation.gui.charts.fundamental_evolution_data import (
    montar_series,
)
from flowscope.presentation.gui.charts.fundamental_table import FundamentalTablePanel
from flowscope.presentation.gui.charts.quadrant_chart import QuadrantChart
from flowscope.presentation.gui.documentos_job import (
    MENSAGEM_PROGRESSO,
    DocumentosJob,
)
from flowscope.presentation.gui.llm.config_dialog import LLMConfigDialog

logger = logging.getLogger("flowscope")

#: Tempo máximo sem progresso antes de encerrar a aquisição de documentos.
_LIMITE_INATIVIDADE_DOCUMENTOS_S = 120.0


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

    def _on_atualizar_fundamentos(self: "ActionsMixin") -> None:
        """Força a recomputação dos fundamentos da data, ignorando o cache."""
        self._controller.on_atualizar_fundamentos()

    def _abrir_config_llm(self: "ActionsMixin") -> None:
        """Abre o diálogo de configuração de LLM, reavaliando o botão ao salvar."""
        painel = getattr(self, "_documents_panel", None)
        on_saved = (
            painel.refresh_resumir_button if painel is not None else None
        )
        LLMConfigDialog(self, on_saved=on_saved)

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
        if main_tab == ABOUT_TAB:
            return None
        return self._TICKER.get(sub_tab)

    def _resolve_current_chart(self: "ActionsMixin") -> object | None:
        try:
            main_tab = self._main_notebook.tab(self._main_notebook.select(), "text")
            if main_tab == ABOUT_TAB:
                return None
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
        elif isinstance(chart, FundamentalTablePanel):
            dados = getattr(self, "_fundamental_data", {})
            chart.update({t: dados[t] for t in tickers if t in dados})
            self._sincronizar_selecao_fundamental()
        elif chart is getattr(self, "_fundamental_evolution_panel", None):
            self._update_fundamental_evolution()
        elif chart is getattr(self, "_documents_panel", None):
            self._update_documents()
        elif chart in self._ticker_charts:
            chart.update(self._current_data, ticker=self._ticker_apresentado())
        else:
            chart.update(filtered)

    def _ticker_apresentado(self: "ActionsMixin") -> str | None:
        """Retorna o ticker apresentado nas sub-abas por ticker.

        O ticker é sempre o selecionado na tabela da sub-aba "Fundamentos",
        fonte única compartilhada por todas as sub-abas da "Análise do Ticker".
        """
        return getattr(self, "_ticker_selecionado", None)

    def _sincronizar_selecao_fundamental(self: "ActionsMixin") -> None:
        """Seleciona na tabela o ticker atual ou a primeira linha disponível."""
        tabela = getattr(self, "_fundamental_table", None)
        if tabela is None:
            return
        ticker = getattr(self, "_ticker_selecionado", None)
        if not (ticker and tabela.has_ticker(ticker)):
            ticker = tabela.first_ticker()
        if ticker:
            self._ticker_selecionado = ticker
            tabela.select_ticker(ticker)
        else:
            self._ticker_selecionado = None

    def _update_fundamental_evolution(self: "ActionsMixin") -> None:
        """Preenche o painel de evolução a partir do cache histórico."""
        painel = self._fundamental_evolution_panel
        ticker = self._ticker_apresentado()
        store = getattr(self, "_fundamental_history_store", None)
        if not ticker or store is None:
            painel.update((), ticker=ticker)
            return
        datas = store.datas(ticker)
        if not datas:
            painel.update((), ticker=ticker)
            return
        observacoes = store.historico(ticker, datas[0], datas[-1])
        painel.update(montar_series(observacoes), ticker=ticker)

    def _update_documents(self: "ActionsMixin") -> None:
        """Preenche o painel de documentos a partir do cache do ticker.

        O ticker é o mesmo apresentado na sub-aba "Evolução dos Fundamentos",
        mantendo as duas sub-abas sincronizadas. A exibição é somente-leitura;
        a aquisição de novos documentos ocorre apenas no botão "Atualizar".
        """
        painel = getattr(self, "_documents_panel", None)
        if painel is None:
            return
        painel.update(self._ticker_apresentado())

    def _adquirir_documentos(self: "ActionsMixin", ticker: str) -> None:
        """Adquire os documentos do ticker em thread e remonta a árvore."""
        painel = getattr(self, "_documents_panel", None)
        aquisicao = getattr(self, "_aquisicao_documentos", None)
        if painel is None:
            return
        if aquisicao is None or not ticker:
            painel.update(ticker)
            return
        if getattr(self, "_documentos_job", None) is not None:
            return
        painel.mostrar_carregando(ticker)
        job = DocumentosJob(
            aquisicao,
            ticker,
            self._data_referencia(),
            cancel_token=self._presenter.cancel_token,
        )
        self._documentos_job = job
        self._presenter.on_operation_started()
        self._presenter.job_cancelavel_iniciado()
        self._documentos_ultima_atividade = time.monotonic()
        try:
            job.iniciar()
        except Exception:
            logger.warning(
                "Falha ao iniciar a aquisição de documentos de %s",
                ticker,
                exc_info=True,
            )
            if getattr(self, "_documentos_job", None) is job:
                self._documentos_job = None
            self._presenter.job_cancelavel_finalizado()
            self._presenter.on_operation_finished()
            return
        self._poll_documentos_job(job, ticker)

    def _cancelamento_solicitado(self: "ActionsMixin") -> bool:
        """Indica se o usuário solicitou a interrupção do processamento."""
        token = getattr(self._presenter, "cancel_token", None)
        return token is not None and token.is_set is True

    def _poll_documentos_job(self: "ActionsMixin", job: DocumentosJob, ticker: str) -> None:
        """Consome a fila do job na thread do Tk até a aquisição concluir.

        Cada mensagem é tratada dentro de ``try/except``: um erro ao processar
        o progresso é registrado no log e não interrompe o esvaziamento da fila,
        de modo que a mensagem terminal ainda encerra o job e libera o cursor.
        """
        terminou = self._drenar_fila_documentos(job, ticker)
        if not terminou and self._cancelamento_solicitado():
            terminou = True
        if not terminou and self._documentos_job_travado(job):
            logger.warning(
                "Aquisição de documentos de %s sem progresso; encerrando para "
                "restaurar a interface.",
                ticker,
            )
            terminou = True
        if terminou:
            self._finalizar_documentos_job(job, ticker)
            return
        self.after(50, lambda: self._poll_documentos_job(job, ticker))

    def _drenar_fila_documentos(
        self: "ActionsMixin", job: DocumentosJob, ticker: str
    ) -> bool:
        """Esvazia a fila do job e informa se ele foi concluído."""
        terminou = False
        try:
            while True:
                mensagem = job.fila.get_nowait()
                if self._mensagem_de_progresso(mensagem):
                    self._tratar_progresso_documentos(mensagem, ticker)
                else:
                    terminou = True
        except queue.Empty:
            pass
        return terminou

    @staticmethod
    def _mensagem_de_progresso(mensagem: object) -> bool:
        """Indica se a mensagem é de progresso da aquisição de documentos."""
        return (
            isinstance(mensagem, tuple)
            and bool(mensagem)
            and mensagem[0] == MENSAGEM_PROGRESSO
        )

    def _tratar_progresso_documentos(
        self: "ActionsMixin", mensagem: tuple, ticker: str
    ) -> None:
        """Repassa o progresso ao presenter, registrando falhas sem abortar."""
        try:
            _tipo, current, total, label = mensagem
            self._documentos_ultima_atividade = time.monotonic()
            self._presenter.on_progress(current, total, label)
        except Exception:
            logger.exception(
                "Erro ao tratar progresso da aquisição de %s", ticker
            )

    def _finalizar_documentos_job(
        self: "ActionsMixin", job: DocumentosJob, ticker: str
    ) -> None:
        """Encerra o job, remonta a árvore e libera o estado ocupado."""
        if getattr(self, "_documentos_job", None) is job:
            self._documentos_job = None
        painel = getattr(self, "_documents_panel", None)
        if painel is not None:
            painel.update(ticker)
        self._presenter.job_cancelavel_finalizado()
        self._presenter.on_operation_finished()
        if not self._cancelamento_solicitado():
            self._flash_status("Documentos atualizados!")

    def _documentos_job_travado(self: "ActionsMixin", job: DocumentosJob) -> bool:
        """Indica se o job morreu ou ficou sem progresso por tempo demais."""
        thread = getattr(job, "thread", None)
        if thread is not None and not thread.is_alive() and job.fila.empty():
            return True
        ultima = getattr(self, "_documentos_ultima_atividade", None)
        if ultima is None:
            return False
        return time.monotonic() - ultima > _LIMITE_INATIVIDADE_DOCUMENTOS_S

    def _data_referencia(self: "ActionsMixin") -> date:
        """Retorna a data de referência selecionada, ou a data corrente."""
        entry = getattr(self, "_date_entry", None)
        if entry is not None:
            return entry.get_date()
        return datetime.now(timezone.utc).date()

    def agendar(self: "ActionsMixin", ms: int, callback: object) -> object:
        """Agenda a execução de ``callback`` na thread do Tk."""
        return self.after(ms, callback)

    def set_fundamental_data(self: "ActionsMixin", dados: dict) -> None:
        """Armazena os resultados da análise fundamentalista por ticker.

        Garante que o ticker apresentado continue válido: mantém o atual
        quando ainda presente e, caso contrário, adota o primeiro disponível.
        """
        self._fundamental_data = dados
        atual = getattr(self, "_ticker_selecionado", None)
        if atual not in dados:
            self._ticker_selecionado = next(iter(dados), None)

    def _copy_chart(self: "ActionsMixin", figure: object) -> None:
        from flowscope.infrastructure.clipboard_image import (
            ClipboardError,
            copy_image_to_clipboard,
        )

        with self._presenter.busy():
            try:
                copy_image_to_clipboard(figure)
                self._flash_status("Gráfico copiado!")
            except ClipboardError as e:
                self._set_status(f"Erro: {e}", "⚠")
