"""Controlador da interface gráfica do FlowScope."""

from datetime import datetime, timezone

from flowscope.application.load_portfolio_use_case import (
    LoadIndexPortfolioUseCase,
    PortfolioNotFoundError,
)
from flowscope.application.logging_port import LogPort
from flowscope.application.operation_guard import OperationGuard
from flowscope.application.use_cases import AnalyzeTickersUseCase
from flowscope.presentation.gui.controller_data import DataLoadMixin
from flowscope.presentation.gui.controller_fundamental import FundamentalMixin
from flowscope.presentation.gui.presenter import FlowScopePresenter


class FlowScopeController(DataLoadMixin, FundamentalMixin):
    """Controlador que orquestra as operações de carga e análise de dados."""

    def __init__(
        self: "FlowScopeController",
        guard: OperationGuard,
        load_portfolio: LoadIndexPortfolioUseCase,
        analyze: AnalyzeTickersUseCase,
        presenter: FlowScopePresenter,
        logger: LogPort,
        fundamental_repo: object | None = None,
        fundamental_provider: object | None = None,
        fundamental_ffo_provider: object | None = None,
        fundamental_dividend_provider: object | None = None,
        fundamental_acionistas_provider: object | None = None,
        fundamental_indexadores_provider: object | None = None,
        fundamental_history_store: object | None = None,
    ) -> None:
        """Inicializa o controlador com as dependências da aplicação."""
        self._guard = guard
        self._load_portfolio = load_portfolio
        self._analyze = analyze
        self._presenter = presenter
        self._logger = logger
        self._fundamental_repo = fundamental_repo
        self._fundamental_provider = fundamental_provider
        self._fundamental_ffo_provider = fundamental_ffo_provider
        self._fundamental_dividend_provider = fundamental_dividend_provider
        self._fundamental_acionistas_provider = fundamental_acionistas_provider
        self._fundamental_indexadores_provider = fundamental_indexadores_provider
        self._fundamental_history_store = fundamental_history_store
        self._fundamental_generation = 0
        self._fundamental_job = None

    def on_today(self: "FlowScopeController") -> None:
        """Carrega os dados para a data atual."""
        self._presenter._gui._date_entry.set_date(datetime.now(timezone.utc).date())
        self.on_load_data()

    def on_ticker_edit(self: "FlowScopeController") -> None:
        """Atualiza a análise ao editar a lista de tickers."""
        tickers = self._presenter.get_current_tickers()
        if not tickers:
            try:
                tickers = self._load_portfolio.execute("IDIV")
            except PortfolioNotFoundError:
                self._presenter._gui._flash_status(
                    "Não foi possível carregar a carteira IDIV.", "⚠",
                )
                return
            self._presenter.on_portfolio_loaded(tickers)
        self._presenter._gui._tickers = list(tickers)
        self._presenter._gui._set_wait_cursor()
        try:
            current = self._presenter._gui._resolve_current_chart()
            if current and self._presenter._gui._current_data:
                self._presenter._gui._do_update(current)
        finally:
            self._presenter._gui._clear_wait_cursor()
        self._presenter._gui._flash_status("Filtro aplicado!", "ℹ")
