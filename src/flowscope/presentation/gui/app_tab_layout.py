"""Construção das abas e restauração do estado do layout da interface."""

import tkinter as tk
from tkinter import ttk

from flowscope.infrastructure.llm.config import load_llm_config
from flowscope.infrastructure.llm.factory import create_llm_provider
from flowscope.presentation.gui.app_tabs import (
    ABOUT_TAB,
    CHAT_AI_TAB,
    ENABLED_TABS,
    TAB_CONFIGS,
)
from flowscope.presentation.gui.charts.correlation_network_panel import (
    CorrelationNetworkPanel,
)
from flowscope.presentation.gui.charts.document_summary import llm_configurada
from flowscope.presentation.gui.charts.document_tree_panel import DocumentTreePanel
from flowscope.presentation.gui.charts.dominance_ranking import DominanceRankingChart
from flowscope.presentation.gui.charts.dominance_timeline import DominanceTimelineChart
from flowscope.presentation.gui.charts.financial_flow_panel import FinancialFlowPanel
from flowscope.presentation.gui.charts.fundamental_evolution_panel import (
    FundamentalEvolutionPanel,
)
from flowscope.presentation.gui.charts.fundamental_table import FundamentalTablePanel
from flowscope.presentation.gui.charts.noticias_panel import NoticiasPanel
from flowscope.presentation.gui.charts.price_range_panel import PriceRangePanel
from flowscope.presentation.gui.charts.quadrant_chart import QuadrantChart
from flowscope.presentation.gui.charts.vwap_hist import VWAPHistChart
from flowscope.presentation.gui.chat.chat_panel import ChatPanel
from flowscope.presentation.gui.chat.noticias import FonteNoticias
from flowscope.presentation.gui.widgets.about_panel import AboutPanel


class TabsLayoutMixin:
    """Constrói as abas de análise e restaura o estado dos separadores."""

    def _build_general_tabs(self: "TabsLayoutMixin") -> None:
        general_fundamental_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_fundamental_frame, text="Fundamentos")
        self._fundamental_table = FundamentalTablePanel(
            general_fundamental_frame,
            widths=getattr(self, "_prefs", {}).get("fundamental_column_widths"),
            on_widths_changed=self._on_fundamental_widths_changed,
            on_row_activated=getattr(
                self, "_on_fundamental_row_activated", None
            ),
            on_ticker_selected=getattr(
                self, "_on_fundamental_ticker_selected", None
            ),
        )
        self._fundamental_table.frame.pack(fill=tk.BOTH, expand=True)

        general_vwap_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_vwap_frame, text="VWAP")
        self._vwap_chart = VWAPHistChart(general_vwap_frame, copy_chart_callback=self._copy_chart)
        self._vwap_chart.frame.pack(fill=tk.BOTH, expand=True)

        general_quadrantes_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_quadrantes_frame, text="Quadrantes")
        self._quadrant_chart = QuadrantChart(
            general_quadrantes_frame,
            copy_chart_callback=self._copy_chart,
            summary_callback=self._on_quadrant_summary,
        )
        self._quadrant_chart.frame.pack(fill=tk.BOTH, expand=True)

        general_dominance_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_dominance_frame, text="Dominância do Pregão")
        self._dominance_ranking = DominanceRankingChart(
            general_dominance_frame, copy_chart_callback=self._copy_chart,
        )
        self._dominance_ranking.frame.pack(fill=tk.BOTH, expand=True)

        general_network_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(
            general_network_frame, text="Rede de Correlação"
        )
        self._correlation_network_panel = CorrelationNetworkPanel(
            general_network_frame, copy_chart_callback=self._copy_chart,
        )
        self._correlation_network_panel.frame.pack(fill=tk.BOTH, expand=True)

        general_noticias_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_noticias_frame, text="Notícias")
        self._noticias_panel = NoticiasPanel(
            general_noticias_frame,
            status_callback=getattr(self, "_set_status", None),
            acquire_callback=getattr(self, "_adquirir_noticias", None),
            ia_callback=getattr(self, "_abrir_config_llm", None),
            resumir_callback=getattr(self, "_resumir_noticias_pendentes", None),
            resumir_ativo_callback=getattr(
                self, "_noticias_resumos_em_andamento", None
            ),
            reference_date_provider=getattr(self, "_data_referencia", None),
        )
        self._noticias_panel.frame.pack(fill=tk.BOTH, expand=True)

    def _on_fundamental_widths_changed(self: "TabsLayoutMixin", widths: dict) -> None:
        """Guarda as larguras das colunas para persistir no fechamento."""
        if hasattr(self, "_prefs"):
            self._prefs["fundamental_column_widths"] = widths

    def _build_ticker_tabs(self: "TabsLayoutMixin") -> None:
        ticker_main_frame = ttk.Frame(self._main_notebook)
        self._main_notebook.add(ticker_main_frame, text="Análise do Ticker")

        self._ticker_notebook = ttk.Notebook(ticker_main_frame)
        self._ticker_notebook.pack(fill=tk.BOTH, expand=True)

        for name, *_ in TAB_CONFIGS:
            if name not in ENABLED_TABS:
                continue
            frame = ttk.Frame(self._ticker_notebook)
            self._ticker_notebook.add(frame, text=name)
            if name == "Evolução da Dominância":
                self._dominance_timeline = DominanceTimelineChart(
                    frame, copy_chart_callback=self._copy_chart,
                )
                self._dominance_timeline.frame.pack(fill=tk.BOTH, expand=True)
            elif name == "Amplitude de Preço":
                self._price_range_panel = PriceRangePanel(
                    frame, copy_chart_callback=self._copy_chart,
                )
                self._price_range_panel.frame.pack(fill=tk.BOTH, expand=True)
            elif name == "Fluxo Financeiro":
                self._financial_flow_panel = FinancialFlowPanel(
                    frame, copy_chart_callback=self._copy_chart,
                    summary_callback=self._on_flow_summary,
                )
                self._financial_flow_panel.frame.pack(fill=tk.BOTH, expand=True)
            elif name == "Evolução dos Fundamentos":
                self._fundamental_evolution_panel = FundamentalEvolutionPanel(
                    frame, copy_chart_callback=self._copy_chart,
                )
                self._fundamental_evolution_panel.frame.pack(fill=tk.BOTH, expand=True)
            elif name == "Documentos":
                self._documents_panel = DocumentTreePanel(
                    frame,
                    status_callback=getattr(self, "_set_status", None),
                    acquire_callback=getattr(self, "_adquirir_documentos", None),
                    ia_callback=getattr(self, "_abrir_config_llm", None),
                    resumir_callback=getattr(
                        self, "_resumir_documentos_pendentes", None
                    ),
                    resumir_ativo_callback=getattr(
                        self, "_resumos_em_andamento", None
                    ),
                )
                self._documents_panel.frame.pack(fill=tk.BOTH, expand=True)

    def _build_chat_tab(self: "TabsLayoutMixin") -> None:
        """Registra a aba de topo única "Chat AI" após a "Análise do Ticker"."""
        chat_frame = ttk.Frame(self._main_notebook)
        self._main_notebook.add(chat_frame, text=CHAT_AI_TAB)
        self._chat_panel = self._criar_chat_panel(chat_frame)
        self._chat_panel.pack(fill=tk.BOTH, expand=True)

    def _criar_chat_panel(
        self: "TabsLayoutMixin", parent: tk.Widget
    ) -> ChatPanel:
        """Constrói o painel de chat ligado ao estado da janela principal."""
        return ChatPanel(
            parent,
            fundamental_data_provider=lambda: getattr(self, "_fundamental_data", {}),
            watchlist_provider=self._watchlist_provider,
            llm_factory=lambda: create_llm_provider(load_llm_config()),
            llm_available=llm_configurada,
            config_callback=getattr(self, "_abrir_config_llm", None),
            status_callback=getattr(self, "_set_status", None),
            fontes_adicionais=[self._criar_fonte_noticias()],
        )

    def _criar_fonte_noticias(self: "TabsLayoutMixin") -> FonteNoticias:
        """Cria a fonte adicional de contexto com as notícias do período."""
        return FonteNoticias(
            reference_date_provider=getattr(self, "_data_referencia", None)
        )

    def _watchlist_provider(self: "TabsLayoutMixin") -> list[str]:
        """Retorna os tickers exibidos, tolerando hosts sem lista de tickers."""
        lista = getattr(self, "_ticker_list", None)
        if lista is None:
            return []
        return lista.get_tickers()

    def _build_about_tab(self: "TabsLayoutMixin") -> None:
        """Registra a aba "Sobre" logo após a "Análise do Ticker"."""
        about_frame = ttk.Frame(self._main_notebook)
        self._main_notebook.add(about_frame, text=ABOUT_TAB)
        self._about_panel = AboutPanel(
            about_frame,
            icon=self._load_icon("flowscope.png", size=(72, 72)),
            on_open_repository=self._abrir_repositorio,
            on_open_log=self._abrir_log_flowscope,
        )
        self._about_panel.frame.pack(fill=tk.BOTH, expand=True)

    def _restore_tabs(self: "TabsLayoutMixin", last_tab: str, last_subtab: str) -> None:
        try:
            for i in range(self._main_notebook.index("end")):
                if self._main_notebook.tab(i, "text") == last_tab:
                    self._main_notebook.select(i)
                    break
            if last_tab in ("Análise Geral", "Análise do Ticker"):
                notebook = (
                    self._general_notebook
                    if last_tab == "Análise Geral"
                    else self._ticker_notebook
                )
                for i in range(notebook.index("end")):
                    if notebook.tab(i, "text") == last_subtab:
                        notebook.select(i)
                        break
        except tk.TclError:
            pass
        self._on_tab_changed()

    def _restore_sashes(self: "TabsLayoutMixin", positions: list[int]) -> None:
        try:
            if len(positions) >= 2:
                self._main_pw.sash_place(0, positions[0], 0)
            if len(positions) >= 4 and hasattr(self, "_left_pw"):
                self._left_pw.sash_place(0, 0, positions[1])
        except tk.TclError:
            pass
