"""Montagem das dependências da interface gráfica principal.

Concentra a construção do controller e dos providers de domínio/infraestrutura
em um mixin próprio, mantendo ``app.py`` restrito à composição da janela.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from flowscope.application.document_text_port import DocumentTextStore
from flowscope.application.documentos.catalogo import (
    ConsultarCatalogoUseCase,
)
from flowscope.application.documentos.document_guidance import GuidanceService
from flowscope.application.documentos.document_summary import DocumentSummaryService
from flowscope.application.fundamental_fallback import (
    CompositeFfoProvider,
    CompositeFundamentalProvider,
)
from flowscope.application.load_portfolio_use_case import LoadIndexPortfolioUseCase
from flowscope.application.noticias.catalogo import ConsultarCatalogoNoticiasUseCase
from flowscope.application.operation_guard import OperationGuard
from flowscope.application.use_cases import AnalyzeTickersUseCase
from flowscope.domain.llm import LLMPort
from flowscope.infrastructure.b3.bdr import BdrDividendProvider
from flowscope.infrastructure.b3.client import B3Client
from flowscope.infrastructure.b3.documentos_aquisicao import AquisicaoDocumentos
from flowscope.infrastructure.b3.emprestimos import B3ShortInterestSource
from flowscope.infrastructure.b3.fund_repository import B3FundRepository
from flowscope.infrastructure.b3.noticias_carga import AquisicaoNoticias
from flowscope.infrastructure.b3.noticias_catalogo import NoticiasCatalog
from flowscope.infrastructure.b3.noticias_vinculo import baixar_conteudo_vinculado
from flowscope.infrastructure.b3.repository import B3DataRepository
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.clipboard_image import ClipboardImageAdapter
from flowscope.infrastructure.cvm.acionistas import CvmAcionistasSource
from flowscope.infrastructure.cvm.patrimonio import CvmMonthlyPatrimonioSource
from flowscope.infrastructure.document_catalog import DocumentCatalog
from flowscope.infrastructure.fii.b3_fundamental_provider import (
    B3FundamentalDataProvider,
)
from flowscope.infrastructure.fii.b3_fundamental_repository import (
    B3FundamentalRepository,
)
from flowscope.infrastructure.fii.b3_price import B3MarketPriceFromResult
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
from flowscope.infrastructure.fii.guidance_extraction import extrair_guidance
from flowscope.infrastructure.guidance_store import JsonGuidanceStore
from flowscope.infrastructure.llm.config import (
    guidance_llm_disponivel,
    llm_configurada,
    load_llm_config,
)
from flowscope.infrastructure.llm.config_adapter import InfrastructureLLMConfig
from flowscope.infrastructure.llm.factory import create_llm_provider
from flowscope.infrastructure.logging.python_log_adapter import PythonLogAdapter
from flowscope.infrastructure.releases import obter_ultima_release
from flowscope.presentation.gui.controller import FlowScopeController
from flowscope.presentation.gui.presenter import FlowScopePresenter


@dataclass(frozen=True)
class AdaptadoresDocumentos:
    """Adaptadores e serviços da fatia de Documentos para a apresentação."""

    catalogo: DocumentCatalog
    catalogo_use_case: ConsultarCatalogoUseCase
    summary_service: DocumentSummaryService
    text_store: DocumentTextStore
    guidance_service: GuidanceService
    llm_factory: Callable[[], LLMPort]
    llm_available: Callable[[], bool]


def montar_adaptadores_documentos(
    cache_dir: Path | None = None,
) -> AdaptadoresDocumentos:
    """Monta o grafo de dependências da fatia de Documentos.

    Ponto de composição: é o único lugar que combina adaptadores de
    infraestrutura com portas de aplicação para os documentos.
    """
    base = Path(cache_dir) if cache_dir is not None else CacheManager().get_cache_dir()
    catalogo = DocumentCatalog(cache_dir=base)
    llm_factory: Callable[[], LLMPort] = lambda: create_llm_provider(
        load_llm_config()
    )
    return AdaptadoresDocumentos(
        catalogo=catalogo,
        catalogo_use_case=ConsultarCatalogoUseCase(catalogo),
        summary_service=DocumentSummaryService(
            catalogo.summary_store,
            base,
            llm_factory=llm_factory,
            llm_available=llm_configurada,
        ),
        text_store=catalogo.text_store,
        guidance_service=GuidanceService(
            JsonGuidanceStore(cache_dir=base),
            llm_factory=llm_factory,
            llm_available=guidance_llm_disponivel,
            extrator=extrair_guidance,
        ),
        llm_factory=llm_factory,
        llm_available=llm_configurada,
    )


@dataclass(frozen=True)
class AdaptadoresNoticias:
    """Adaptadores e serviços da fatia de Notícias para a apresentação."""

    catalogo: NoticiasCatalog
    catalogo_use_case: ConsultarCatalogoNoticiasUseCase
    summary_service: DocumentSummaryService
    text_store: DocumentTextStore
    baixar_vinculo: Callable[[str], str | None]
    llm_factory: Callable[[], LLMPort]
    llm_available: Callable[[], bool]


def montar_adaptadores_noticias(
    cache_dir: Path | None = None,
) -> AdaptadoresNoticias:
    """Monta o grafo de dependências da fatia de Notícias.

    Ponto de composição: é o único lugar que combina adaptadores de
    infraestrutura com portas de aplicação para as notícias.
    """
    base = Path(cache_dir) if cache_dir is not None else CacheManager().get_cache_dir()
    catalogo = NoticiasCatalog(cache_dir=base)
    llm_factory: Callable[[], LLMPort] = lambda: create_llm_provider(
        load_llm_config()
    )
    return AdaptadoresNoticias(
        catalogo=catalogo,
        catalogo_use_case=ConsultarCatalogoNoticiasUseCase(catalogo),
        summary_service=DocumentSummaryService(
            catalogo.summary_store,
            base,
            llm_factory=llm_factory,
            llm_available=llm_configurada,
        ),
        text_store=catalogo.text_store,
        baixar_vinculo=baixar_conteudo_vinculado,
        llm_factory=llm_factory,
        llm_available=llm_configurada,
    )


class WiringMixin:
    """Constrói o controller e os providers usados pela janela principal."""

    def _wire_ports(self: "WiringMixin") -> None:
        """Injeta as portas de releases, LLM e clipboard usadas pela janela."""
        self._release_checker = obter_ultima_release
        self._clipboard = ClipboardImageAdapter()
        self._llm_config = InfrastructureLLMConfig()

    def _wire_documentos(self: "WiringMixin") -> None:
        """Monta os adaptadores de documentos antes da construção das abas."""
        self._documentos_adapters = montar_adaptadores_documentos()

    def _wire_noticias(self: "WiringMixin") -> None:
        """Monta os adaptadores de notícias antes da construção das abas."""
        self._noticias_adapters = montar_adaptadores_noticias()

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
        self._aquisicao_noticias = AquisicaoNoticias(cache=cache)
        b3_fund_repository = B3FundRepository()
        fundamental_repo = B3FundamentalRepository(
            fund_repository=b3_fund_repository,
            patrimonio_source=CvmMonthlyPatrimonioSource(),
        )
        fundamental_bdr_provider = BdrDividendProvider(cache=cache)
        fundamental_acionistas_provider = CvmAcionistasSource(cache=cache)
        fundamental_short_interest_provider = B3ShortInterestSource(cache=cache)
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
            fundamental_short_interest_provider=fundamental_short_interest_provider,
            fundamental_mercado_factory=B3MarketPriceFromResult,
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
