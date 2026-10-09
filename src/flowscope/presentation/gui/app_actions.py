"""Ações de configuração e atualização de gráficos da interface gráfica."""

import tkinter as tk
from datetime import date, datetime, timezone

from flowscope.application.clipboard_port import ClipboardError, ImageClipboardPort
from flowscope.domain.sampling import SamplingConfig
from flowscope.presentation.gui import evolucao_job
from flowscope.presentation.gui.app_tabs import ABOUT_TAB, CHAT_AI_TAB
from flowscope.presentation.gui.background.events import Outcome
from flowscope.presentation.gui.background.job import Politica
from flowscope.presentation.gui.charts.fundamental_table import FundamentalTablePanel
from flowscope.presentation.gui.charts.quadrant_chart import QuadrantChart
from flowscope.presentation.gui.documentos_job import (
    GRUPO,
    POLITICA,
    executar_documentos,
)

#: Grupo e política da leitura do catálogo de documentos (fora da aquisição).
GRUPO_LEITURA_DOCUMENTOS = "documentos-leitura"
POLITICA_LEITURA = Politica.LATEST_WINS

#: Grupo e política da transferência assíncrona de gráficos ao clipboard.
GRUPO_CLIPBOARD = "clipboard"
POLITICA_CLIPBOARD = Politica.LATEST_WINS


class ActionsMixin:
    """Lida com eventos de seleção de período, amostragem e atualização dos gráficos."""

    #: Porta de cópia de gráficos; injetada pelo composition root.
    _clipboard: ImageClipboardPort | None = None

    def _on_period_combo_changed(self: "ActionsMixin", event: tk.Event | None = None) -> None:
        text = self._PERIOD_STATUS.get(self._period_var.get(), "")
        if text:
            self._set_status(text)
        if self._current_data:
            self._controller.on_load_data()
        else:
            self._atualizar_evolucao_se_visivel()

    def _update_sampling_label(self: "ActionsMixin") -> None:
        text = self._SAMPLING_STATUS.get(self._sampling_var.get(), "")
        self._sampling_label.config(text=text)

    def _on_sampling_combo_changed(self: "ActionsMixin", event: tk.Event | None = None) -> None:
        self._update_sampling_label()
        if self._current_data:
            self._controller.on_load_data()
        else:
            self._atualizar_evolucao_se_visivel()

    def _atualizar_evolucao_se_visivel(self: "ActionsMixin") -> None:
        """Remonta a evolução quando a sub-aba está visível, sem dados da B3."""
        current_tabs = getattr(self, "_current_tabs", None)
        if current_tabs is None:
            return
        if current_tabs() == ("Análise do Ticker", "Evolução dos Fundamentos"):
            self._update_fundamental_evolution()

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
        period_var = getattr(self, "_period_var", None)
        sampling_var = getattr(self, "_sampling_var", None)
        periodo = period_var.get() if period_var is not None else ""
        amostragem = sampling_var.get() if sampling_var is not None else ""
        return SamplingConfig(
            period_days=period_map.get(periodo, 30),
            method=sampling_map.get(amostragem, "fibonacci"),
        )

    def _on_today(self: "ActionsMixin") -> None:
        self._date_entry.set_date(datetime.now(timezone.utc).date())
        self._controller.on_load_data()

    def _on_load_data(self: "ActionsMixin") -> None:
        if getattr(self, "_inicializando", False):
            return
        self._controller.on_load_data()

    def _on_atualizar_fundamentos(self: "ActionsMixin") -> None:
        """Força a recomputação dos fundamentos da data, ignorando o cache."""
        self._controller.on_atualizar_fundamentos()

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
        if main_tab in (ABOUT_TAB, CHAT_AI_TAB):
            return None
        return self._TICKER.get(sub_tab)

    def _resolve_current_chart(self: "ActionsMixin") -> object | None:
        try:
            main_tab = self._main_notebook.tab(self._main_notebook.select(), "text")
            if main_tab in (ABOUT_TAB, CHAT_AI_TAB):
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
        else:
            self._update_especial(chart, filtered, tickers)

    def _update_especial(
        self: "ActionsMixin", chart: object, filtered: dict, tickers: list[str]
    ) -> None:
        """Atualiza os painéis que não seguem o fluxo padrão de dados filtrados."""
        if chart is getattr(self, "_correlation_network_panel", None):
            chart.update(filtered, tickers=tickers)
        elif isinstance(chart, FundamentalTablePanel):
            dados = getattr(self, "_fundamental_data", {})
            chart.update({t: dados[t] for t in tickers if t in dados})
            self._sincronizar_selecao_fundamental()
        elif chart is getattr(self, "_fundamental_evolution_panel", None):
            self._update_fundamental_evolution()
        elif chart is getattr(self, "_documents_panel", None):
            self._update_documents()
        elif chart is getattr(self, "_noticias_panel", None):
            self._update_noticias()
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
        """Submete a leitura do cache histórico e preenche o painel de evolução."""
        painel = getattr(self, "_fundamental_evolution_panel", None)
        if painel is None:
            return
        ticker = self._ticker_apresentado()
        store = getattr(self, "_fundamental_history_store", None)
        config = self.get_sampling_config()
        ancora = self._data_referencia()
        chave = (ticker, config.period_days, config.method)
        background = getattr(self, "_background", None)
        if background is None:
            painel.update(
                evolucao_job.preparar_series(
                    store,
                    ticker,
                    periodo_dias=config.period_days,
                    metodo=config.method,
                    ancora=ancora,
                ),
                ticker=ticker,
            )
            return
        painel.mostrar_carregando(ticker)
        background.submit(
            lambda ctx: ctx.resultado(
                valor=evolucao_job.preparar_series(
                    store,
                    ticker,
                    periodo_dias=config.period_days,
                    metodo=config.method,
                    ancora=ancora,
                )
            ),
            grupo=evolucao_job.GRUPO,
            politica=evolucao_job.POLITICA,
            chave=chave,
            ao_resultado=lambda evento: self._aplicar_evolucao(
                ticker, chave, evento.valor
            ),
        )

    def _aplicar_evolucao(
        self: "ActionsMixin", ticker: str | None, chave: tuple, series: object
    ) -> None:
        """Aplica as séries se o ticker e a configuração não mudaram."""
        painel = getattr(self, "_fundamental_evolution_panel", None)
        if painel is None or ticker != self._ticker_apresentado():
            return
        config = self.get_sampling_config()
        if chave != (ticker, config.period_days, config.method):
            return
        painel.update(series, ticker=ticker)

    def _update_documents(self: "ActionsMixin") -> None:
        """Submete a leitura do catálogo de documentos do ticker apresentado.

        O ticker é o mesmo apresentado na sub-aba "Evolução dos Fundamentos",
        mantendo as duas sub-abas sincronizadas. A exibição é somente-leitura;
        a aquisição de novos documentos ocorre apenas pelo botão "Atualizar".
        """
        self._submeter_leitura_documentos(self._ticker_apresentado())

    def _submeter_leitura_documentos(
        self: "ActionsMixin", ticker: str | None
    ) -> None:
        """Lê o catálogo do ticker fora da thread do Tk e remonta por evento."""
        painel = getattr(self, "_documents_panel", None)
        if painel is None:
            return
        if not ticker:
            painel.aplicar_catalogo(None, None)
            return
        background = getattr(self, "_background", None)
        if background is None:
            painel.update(ticker)
            return
        painel.mostrar_carregando(ticker)

        def trabalho(ctx: object) -> None:
            catalogo = painel.carregar_catalogo(ticker)
            pendentes, guidances = painel.carregar_guidance(ticker, catalogo)
            ctx.resultado(valor=(catalogo, pendentes, guidances))

        background.submit(
            trabalho,
            grupo=GRUPO_LEITURA_DOCUMENTOS,
            politica=POLITICA_LEITURA,
            chave=ticker,
            ao_resultado=lambda evento: self._aplicar_catalogo_documentos(
                ticker, evento.valor
            ),
        )

    def _aplicar_catalogo_documentos(
        self: "ActionsMixin", ticker: str | None, valor: object
    ) -> None:
        """Aplica o catálogo, os RGs pendentes e o guidance se o ticker não mudou."""
        painel = getattr(self, "_documents_panel", None)
        if painel is None or ticker != self._ticker_apresentado():
            return
        catalogo, pendentes, guidances = valor
        painel.aplicar_catalogo(ticker, catalogo, pendentes, guidances)

    def _adquirir_documentos(self: "ActionsMixin", ticker: str) -> None:
        """Adquire os documentos do ticker em background e remonta a árvore."""
        painel = getattr(self, "_documents_panel", None)
        aquisicao = getattr(self, "_aquisicao_documentos", None)
        if painel is None:
            return
        if aquisicao is None or not ticker:
            self._submeter_leitura_documentos(ticker)
            return
        background = getattr(self, "_background", None)
        if background is None or background.tem_ativo(GRUPO):
            return
        painel.mostrar_carregando(ticker)
        deduplicar = getattr(self, "_deduplicar_documentos", None)
        estado = {"adquiridos": 0}

        def trabalho(ctx: object) -> None:
            estado["adquiridos"] = executar_documentos(
                ctx, aquisicao, ticker, self._data_referencia(), deduplicar
            )

        background.submit(
            trabalho,
            grupo=GRUPO,
            politica=POLITICA,
            cancelavel=True,
            ao_progresso=lambda evento: self._presenter.on_progress(
                evento.atual, evento.total, evento.detalhe
            ),
            ao_termino=lambda evento: self._finalizar_documentos(
                ticker, evento, estado["adquiridos"]
            ),
        )

    def _finalizar_documentos(
        self: "ActionsMixin", ticker: str, evento: object, adquiridos: int
    ) -> None:
        """Relê o catálogo e informa o desfecho da aquisição."""
        if ticker == self._ticker_apresentado():
            self._submeter_leitura_documentos(ticker)
        if evento.outcome is not Outcome.SUCESSO:
            return
        if adquiridos:
            self._flash_status("Documentos atualizados!")
        else:
            self._flash_status("Nenhum documento novo.", "ℹ")

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
        """Copia o gráfico: rendering no Tk e transferência em background.

        O rendering permanece serializado com a thread da interface; apenas a
        transferência do PNG ao sistema é submetida ao gerenciador de background,
        que governa o estado ocupado e publica sucesso/erro por eventos.
        """
        if self._clipboard is None:
            return
        background = getattr(self, "_background", None)
        if background is None:
            self._copiar_grafico_sincrono(figure)
            return
        with self._presenter.busy():
            try:
                caminho = self._clipboard.salvar_png(figure)
            except ClipboardError as e:
                self._set_status(f"Erro: {e}", "⚠")
                return
            background.submit(
                lambda ctx: ctx.resultado(
                    valor=self._clipboard.transferir_png(caminho)
                ),
                grupo=GRUPO_CLIPBOARD,
                politica=POLITICA_CLIPBOARD,
                ao_resultado=lambda evento: self._flash_status(
                    "Gráfico copiado!"
                ),
                ao_erro=lambda evento: self._set_status(
                    f"Erro: {evento.excecao}", "⚠"
                ),
            )

    def _copiar_grafico_sincrono(self: "ActionsMixin", figure: object) -> None:
        """Copia o gráfico na própria thread do Tk (hosts sem background)."""
        with self._presenter.busy():
            try:
                self._clipboard.copy_image(figure)
                self._flash_status("Gráfico copiado!")
            except ClipboardError as e:
                self._set_status(f"Erro: {e}", "⚠")
