"""Composição neutra das dependências compartilhadas do FlowScope.

Concentra, em um único ponto independente de Tk, a montagem do cache, das
aquisições de documentos e notícias, da deduplicação, do grafo de fundamentos,
dos stores e da fábrica de LLM. É consumido pela interface gráfica
(:class:`~flowscope.presentation.gui.app_wiring.WiringMixin`), pelos subcomandos
CLI e pelo servidor MCP, evitando que cada superfície recomponha o mesmo grafo.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from flowscope.application.document_preview import ExtracaoTexto
from flowscope.application.document_text_port import DocumentTextStore
from flowscope.application.documentos.catalogo import (
    ConsultarCatalogoUseCase,
    chave_documento,
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
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.llm import LLMPort
from flowscope.infrastructure.action_lock import ActionLock, OperacaoEmAndamento
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
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes
from flowscope.infrastructure.content_hashes import hash_de_caminho
from flowscope.infrastructure.cvm.acionistas import CvmAcionistasSource
from flowscope.infrastructure.cvm.patrimonio import CvmMonthlyPatrimonioSource
from flowscope.infrastructure.deduplicacao import (
    executar_housekeeping_documentos,
    executar_housekeeping_noticias,
)
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
from flowscope.infrastructure.llm.config import llm_configurada, load_llm_config
from flowscope.infrastructure.llm.config_adapter import InfrastructureLLMConfig
from flowscope.infrastructure.llm.factory import create_llm_provider
from flowscope.infrastructure.logging.python_log_adapter import PythonLogAdapter
from flowscope.infrastructure.referencia import (
    registrar_last_fundamentals,
    resolver_data_referencia,
)

__all__ = [
    "AdaptadoresDocumentos",
    "AdaptadoresNoticias",
    "Nucleo",
    "montar_adaptadores_documentos",
    "montar_adaptadores_noticias",
    "montar_nucleo",
    "registrar_carga_fundamentos",
    "registrar_last_fundamentals",
    "resolvedor_chave_documento",
    "resolver_data_referencia",
    "salvar_preferencias",
]


@dataclass(frozen=True)
class AdaptadoresDocumentos:
    """Adaptadores e serviços da fatia de Documentos."""

    catalogo: DocumentCatalog
    catalogo_use_case: ConsultarCatalogoUseCase
    summary_service: DocumentSummaryService
    text_store: DocumentTextStore
    guidance_service: GuidanceService
    guidance_paths: Callable[[object], list[Path]]
    llm_factory: Callable[[], LLMPort]
    llm_available: Callable[[], bool]
    context_window_provider: Callable[[], int]
    cache_support_provider: Callable[[], bool]
    token_counter_provider: Callable[[], Callable[[str], int] | None]


@dataclass(frozen=True)
class AdaptadoresNoticias:
    """Adaptadores e serviços da fatia de Notícias."""

    catalogo: NoticiasCatalog
    catalogo_use_case: ConsultarCatalogoNoticiasUseCase
    summary_service: DocumentSummaryService
    text_store: DocumentTextStore
    baixar_vinculo: Callable[..., ExtracaoTexto | None]
    llm_factory: Callable[[], LLMPort]
    llm_available: Callable[[], bool]


def resolvedor_chave_documento(base: Path) -> Callable[[DocumentoArquivo], str]:
    """Resolve a chave de conteúdo (hash) de um documento na raiz de cache.

    Usa o hash SHA-256 registrado pela deduplicação do ticker; sem hash, cai
    para o caminho relativo do documento.
    """

    def chave(arquivo: DocumentoArquivo) -> str:
        relativo = chave_documento(arquivo.caminho, base)
        return hash_de_caminho(base, arquivo.ticker, relativo) or relativo

    return chave


def montar_adaptadores_documentos(
    cache_dir: Path | None = None,
) -> AdaptadoresDocumentos:
    """Monta o grafo de dependências da fatia de Documentos.

    Ponto de composição: é o único lugar que combina adaptadores de
    infraestrutura com portas de aplicação para os documentos.
    """
    base = Path(cache_dir) if cache_dir is not None else CacheManager().get_cache_dir()
    catalogo = DocumentCatalog(cache_dir=base)
    guidance_store = JsonGuidanceStore(cache_dir=base)
    porta_llm = InfrastructureLLMConfig()
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
            guidance_store,
            llm_factory=llm_factory,
            llm_available=llm_configurada,
            extrator=extrair_guidance,
            chave_rg=resolvedor_chave_documento(base),
        ),
        guidance_paths=lambda tickers: [
            guidance_store.caminho(ticker) for ticker in tickers
        ],
        llm_factory=llm_factory,
        llm_available=llm_configurada,
        context_window_provider=lambda: porta_llm.context_window(
            load_llm_config()
        ),
        cache_support_provider=lambda: porta_llm.cache_suportado(
            load_llm_config()
        ),
        token_counter_provider=lambda: porta_llm.token_counter(
            load_llm_config()
        ),
    )


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


@dataclass(frozen=True)
class Nucleo:
    """Grafo de dependências neutro reusado por GUI, CLI e MCP."""

    cache: CacheManager
    base: Path
    documentos: AdaptadoresDocumentos
    noticias: AdaptadoresNoticias
    aquisicao_documentos: AquisicaoDocumentos
    aquisicao_noticias: AquisicaoNoticias
    deduplicar_documentos: Callable[[str, object], None]
    deduplicar_noticias: Callable[[object], None]
    repo: B3DataRepository
    guard: OperationGuard
    load_portfolio: LoadIndexPortfolioUseCase
    analyze: AnalyzeTickersUseCase
    b3_fund_repository: B3FundRepository
    fundamental_repo: B3FundamentalRepository
    fundamental_provider: CompositeFundamentalProvider
    fundamental_ffo_provider: CompositeFfoProvider
    fundamental_dividend_provider: FundamentusDividendHistoryProvider
    fundamental_acionistas_provider: CvmAcionistasSource
    fundamental_indexadores_provider: CvmIndexadoresProvider
    fundamental_bdr_provider: BdrDividendProvider
    fundamental_short_interest_provider: B3ShortInterestSource
    history_store: JsonFundamentalHistoryStore
    guidance_store: JsonGuidanceStore
    llm_factory: Callable[[], LLMPort]
    logger: PythonLogAdapter

    @property
    def resolver_fiagro(self: Nucleo) -> Callable[[str], bool]:
        """Indica, por ticker, se o fundo é um FIAGRO."""
        return lambda ticker: self.b3_fund_repository.tipo_fundo(ticker) == "FIAGRO"

    @property
    def mercado_factory(self: Nucleo) -> type:
        """Fábrica do ``MarketPricePort`` a partir do resultado da análise."""
        return B3MarketPriceFromResult


def montar_nucleo(cache: CacheManager | None = None) -> Nucleo:
    """Monta o grafo neutro de dependências, sem depender de Tk."""
    cache = cache or CacheManager()
    base = cache.get_cache_dir()
    documentos = montar_adaptadores_documentos(base)
    noticias = montar_adaptadores_noticias(base)
    repo = B3DataRepository(B3Client())
    b3_fund_repository = B3FundRepository()
    fundamental_repo = B3FundamentalRepository(
        fund_repository=b3_fund_repository,
        patrimonio_source=CvmMonthlyPatrimonioSource(),
    )
    fundamental_acionistas_provider = CvmAcionistasSource(cache=cache)
    fundamental_provider = CompositeFundamentalProvider(
        [
            FundamentusFundamentalDataProvider(FundamentusProvider(cache=cache)),
            B3FundamentalDataProvider(fundamental_repo),
            CvmAnnualFundDataProvider(),
            CvmPapelCnpjProvider(fundamental_acionistas_provider.obter_cnpj),
        ]
    )
    return Nucleo(
        cache=cache,
        base=base,
        documentos=documentos,
        noticias=noticias,
        aquisicao_documentos=AquisicaoDocumentos(cache=cache),
        aquisicao_noticias=AquisicaoNoticias(cache=cache),
        deduplicar_documentos=lambda ticker, token: executar_housekeeping_documentos(
            base, ticker, token
        ),
        deduplicar_noticias=lambda token: executar_housekeeping_noticias(base, token),
        repo=repo,
        guard=OperationGuard(),
        load_portfolio=LoadIndexPortfolioUseCase(repo),
        analyze=AnalyzeTickersUseCase(repo),
        b3_fund_repository=b3_fund_repository,
        fundamental_repo=fundamental_repo,
        fundamental_provider=fundamental_provider,
        fundamental_ffo_provider=CompositeFfoProvider(
            [FundamentusProvider(cache=cache), FFOEngineProvider()]
        ),
        fundamental_dividend_provider=FundamentusDividendHistoryProvider(cache=cache),
        fundamental_acionistas_provider=fundamental_acionistas_provider,
        fundamental_indexadores_provider=CvmIndexadoresProvider(),
        fundamental_bdr_provider=BdrDividendProvider(cache=cache),
        fundamental_short_interest_provider=B3ShortInterestSource(cache=cache),
        history_store=JsonFundamentalHistoryStore(cache_dir=base),
        guidance_store=JsonGuidanceStore(cache_dir=base),
        llm_factory=documentos.llm_factory,
        logger=PythonLogAdapter(logging.getLogger("flowscope")),
    )


#: Espera máxima, em segundos, para adquirir o lock ao gravar preferências.
_ESPERA_LOCK_CONFIG = 30.0


def salvar_preferencias(config_dir: Path, config_path: Path, data: dict) -> None:
    """Grava as preferências preservando os demais blocos, atômica e sob lock.

    Faz *read-modify-write* do ``config.json``: relê o arquivo e aplica apenas
    as chaves informadas, mantendo blocos geridos por outros módulos (como
    ``llm``). A leitura e a gravação ocorrem sob o lock global de ação e a
    escrita é atômica, de modo que gravações concorrentes (CLI e GUI) não
    percam chaves.
    """
    import json

    lock = ActionLock()
    try:
        lock.adquirir(esperar=_ESPERA_LOCK_CONFIG)
    except OperacaoEmAndamento:
        logging.getLogger("flowscope").warning(
            "Lock de ação indisponível ao gravar preferências; escrevendo atômico"
        )
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        existente: dict = {}
        if config_path.exists():
            try:
                carregado = json.loads(config_path.read_text(encoding="utf-8"))
                if isinstance(carregado, dict):
                    existente = carregado
            except (json.JSONDecodeError, OSError):
                existente = {}
        existente.update(data)
        _atomic_write_bytes(
            config_path,
            json.dumps(existente, indent=2, default=str).encode("utf-8"),
        )
    except OSError:
        pass
    finally:
        lock.liberar()


def registrar_carga_fundamentos(data: date) -> None:
    """Registra o marcador da última carga de fundamentos no ``config.json``."""
    registrar_last_fundamentals(data)


def resolver_data_referencia_seguro() -> date | None:
    """Resolve a data de referência tolerando configuração ilegível."""
    try:
        return resolver_data_referencia()
    except Exception:  # configuração ilegível não deve derrubar o consumidor
        logging.getLogger("flowscope").warning(
            "Falha ao resolver a data de referência", exc_info=True
        )
        return None


#: Espera máxima, em segundos, do lock nas fases de escrita da GUI.
#: A GUI não bloqueia a interface: participa do lock quando ele está livre e,
#: se estiver retido por uma ação da CLI, registra e prossegue.
_ESPERA_LOCK_GUI = 0.0


@contextmanager
def bloqueio_de_escrita(esperar: float = _ESPERA_LOCK_GUI) -> Iterator[None]:
    """Adquire o lock global nas fases de gravação da GUI, liberando ao fim.

    Participa do mesmo lock de ação da CLI, de modo que uma fase de escrita da
    GUI e uma execução da CLI não gravem concorrentemente. Não retém o lock fora
    da fase de escrita.
    """
    lock = ActionLock()
    try:
        lock.adquirir(esperar=esperar)
    except OperacaoEmAndamento:
        logging.getLogger("flowscope").warning(
            "Lock de ação indisponível para a fase de escrita da GUI"
        )
    try:
        yield
    finally:
        lock.liberar()
