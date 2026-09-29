"""Controlador da interface gráfica do FlowScope."""

from datetime import datetime, timezone

from flowscope.application.load_portfolio_use_case import (
    LoadIndexPortfolioUseCase,
)
from flowscope.application.logging_port import LogPort
from flowscope.application.operation_guard import OperationGuard
from flowscope.application.use_cases import AnalyzeTickersUseCase
from flowscope.presentation.gui.controller_data import (
    ORIGEM_PORTFOLIO,
    DataLoadMixin,
)
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
        fundamental_resolver_fiagro: object | None = None,
        fundamental_bdr_provider: object | None = None,
        fundamental_guidance_store: object | None = None,
        fundamental_short_interest_provider: object | None = None,
        fundamental_mercado_factory: object | None = None,
        background: object | None = None,
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
        self._fundamental_resolver_fiagro = fundamental_resolver_fiagro
        self._fundamental_bdr_provider = fundamental_bdr_provider
        self._fundamental_guidance_store = fundamental_guidance_store
        self._fundamental_short_interest_provider = (
            fundamental_short_interest_provider
        )
        self._fundamental_mercado_factory = fundamental_mercado_factory
        self._background = background

    def on_today(self: "FlowScopeController") -> None:
        """Carrega os dados para a data atual."""
        self._presenter._gui._date_entry.set_date(datetime.now(timezone.utc).date())
        self.on_load_data()

    def on_ticker_edit(self: "FlowScopeController") -> None:
        """Atualiza a análise ao editar a lista de tickers."""
        tickers = self._presenter.get_current_tickers()
        if not tickers:
            self._submeter_carga(
                self._montar_instrucao(
                    ORIGEM_PORTFOLIO, "IDIV", [], None,
                ),
                usar_guard=False,
            )
            return
        self._aplicar_carteira(tickers, anunciar=False)
        self._presenter._gui._flash_status("Filtro aplicado!", "ℹ")
