"""Montagem das dependências da interface gráfica principal.

Concentra a construção do controller e dos providers de domínio/infraestrutura
em um mixin próprio, mantendo ``app.py`` restrito à composição da janela.
"""

import logging

from flowscope.application.fundamental_fallback import (
    CompositeFfoProvider,
    CompositeFundamentalProvider,
)
from flowscope.application.load_portfolio_use_case import LoadIndexPortfolioUseCase
from flowscope.application.operation_guard import OperationGuard
from flowscope.application.use_cases import AnalyzeTickersUseCase
from flowscope.infrastructure.b3.bdr import BdrDividendProvider
from flowscope.infrastructure.b3.client import B3Client
from flowscope.infrastructure.b3.documentos_aquisicao import AquisicaoDocumentos
from flowscope.infrastructure.b3.fund_repository import B3FundRepository
from flowscope.infrastructure.b3.repository import B3DataRepository
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.cvm.acionistas import CvmAcionistasSource
from flowscope.infrastructure.cvm.patrimonio import CvmMonthlyPatrimonioSource
from flowscope.infrastructure.fii.b3_fundamental_provider import (
    B3FundamentalDataProvider,
)
from flowscope.infrastructure.fii.b3_fundamental_repository import (
    B3FundamentalRepository,
)
from flowscope.infrastructure.fii.cvm_fund_data_provider import (
    CvmAnnualFundDataProvider,
    CvmIndexadoresProvider,
    CvmPapelCnpjProvider,
)
from flowscope.infrastructure.fii.ffo_engine_provider import FFOEngineProvider
from flowscope.infrastructure.fii.ffo_provider import FundamentusProvider
from flowscope.infrastructure.fii.fundamental_history_store import (
    JsonFundamentalHistoryStore,
)
from flowscope.infrastructure.fii.fundamentus.adapter import (
    FundamentusFundamentalDataProvider,
)
from flowscope.infrastructure.fii.fundamentus.dividend_provider import (
    FundamentusDividendHistoryProvider,
)
from flowscope.infrastructure.guidance_store import JsonGuidanceStore
from flowscope.infrastructure.logging.python_log_adapter import PythonLogAdapter
from flowscope.presentation.gui.controller import FlowScopeController
from flowscope.presentation.gui.presenter import FlowScopePresenter


class WiringMixin:
    """Constrói o controller e os providers usados pela janela principal."""

    def _wire_controller(self: "WiringMixin") -> None:
        """Monta o grafo de dependências e conecta a lista de tickers."""
        repo = B3DataRepository(B3Client())
        guard = OperationGuard()
        load_portfolio = LoadIndexPortfolioUseCase(repo)
        analyze = AnalyzeTickersUseCase(repo)
        presenter = FlowScopePresenter(view=self)
        self._presenter = presenter
        logger = PythonLogAdapter(logging.getLogger("flowscope"))
        cache = CacheManager()
        self._aquisicao_documentos = AquisicaoDocumentos(cache=cache)
        b3_fund_repository = B3FundRepository()
        fundamental_repo = B3FundamentalRepository(
            fund_repository=b3_fund_repository,
            patrimonio_source=CvmMonthlyPatrimonioSource(),
        )
        fundamental_bdr_provider = BdrDividendProvider(cache=cache)
        fundamental_acionistas_provider = CvmAcionistasSource(cache=cache)
        fundamental_provider = CompositeFundamentalProvider(
            [
                FundamentusFundamentalDataProvider(
                    FundamentusProvider(cache=cache)
                ),
                B3FundamentalDataProvider(fundamental_repo),
                CvmAnnualFundDataProvider(),
                CvmPapelCnpjProvider(
                    fundamental_acionistas_provider.obter_cnpj
                ),
            ]
        )
        fundamental_ffo_provider = CompositeFfoProvider(
            [FundamentusProvider(cache=cache), FFOEngineProvider()]
        )
        fundamental_dividend_provider = FundamentusDividendHistoryProvider(
            cache=cache
        )
        fundamental_indexadores_provider = CvmIndexadoresProvider()
        self._fundamental_history_store = JsonFundamentalHistoryStore()
        self._guidance_store = JsonGuidanceStore()
        self._controller = FlowScopeController(
            guard=guard,
            load_portfolio=load_portfolio,
            analyze=analyze,
            presenter=presenter,
            logger=logger,
            fundamental_repo=fundamental_repo,
            fundamental_provider=fundamental_provider,
            fundamental_ffo_provider=fundamental_ffo_provider,
            fundamental_dividend_provider=fundamental_dividend_provider,
            fundamental_acionistas_provider=fundamental_acionistas_provider,
            fundamental_indexadores_provider=fundamental_indexadores_provider,
            fundamental_history_store=self._fundamental_history_store,
            fundamental_resolver_fiagro=(
                lambda ticker: b3_fund_repository.tipo_fundo(ticker) == "FIAGRO"
            ),
            fundamental_bdr_provider=fundamental_bdr_provider,
            fundamental_guidance_store=self._guidance_store,
        )
        self._ticker_list.rebind(
            on_change=self._on_ticker_edit,
            on_load=self._controller.on_load_data,
            on_data_needed=self._controller.on_load_data,
            on_index_click={
                "IBOV": lambda: self._controller.on_index_clicked("IBOV"),
                "IDIV": lambda: self._controller.on_index_clicked("IDIV"),
                "IFIX": lambda: self._controller.on_index_clicked("IFIX"),
            },
        )
        self._fundamental_refresh_btn = self._ticker_list.add_action_button(
            self._on_atualizar_fundamentos,
            icon="edit-redo.png",
            tooltip="Atualizar fundamentos",
        )
        self._ticker_list.set_action_button_visible(
            self._fundamental_refresh_btn, False
        )
