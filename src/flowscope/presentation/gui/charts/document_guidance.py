"""Decisão e execução da avaliação de guidance ao ler um documento.

Concentra o portão da categoria ``Relatorio``, a supressão de documentos sem
texto extraível e a leitura do guidance em cache para decidir se o relatório
lido é mais recente. A avaliação é delegada ao caso de uso, que prefere a LLM e
recorre à extração determinística quando ela não está disponível.
"""

from collections.abc import Callable

from flowscope.application.avaliar_guidance import (
    CATEGORIA_RELATORIO,
    AvaliarGuidanceUseCase,
)
from flowscope.application.guidance_port import GuidanceStore
from flowscope.domain.fii import Guidance
from flowscope.domain.llm import LLMPort
from flowscope.infrastructure.document_catalog import DocumentoArquivo
from flowscope.infrastructure.fii.guidance_extraction import extrair_guidance
from flowscope.infrastructure.llm.config import load_llm_config
from flowscope.infrastructure.llm.factory import create_llm_provider
from flowscope.presentation.gui.charts.document_preview import tem_texto


def _criar_llm() -> LLMPort:
    """Cria a porta de completion a partir da configuração do usuário."""
    return create_llm_provider(load_llm_config())


def _llm_disponivel() -> bool:
    """Indica se a análise de guidance via LLM está habilitada e configurada.

    O flag ``llm.guidance.enabled`` (padrão desabilitado) controla o uso da LLM
    especificamente para guidance; quando desabilitado, roda apenas a extração
    determinística, ainda que o provedor de chat esteja configurado.
    """
    from flowscope.infrastructure.llm.config import load_guidance_llm_enabled
    from flowscope.presentation.gui.charts.document_summary import (
        llm_configurada,
    )

    return load_guidance_llm_enabled() and llm_configurada()


class GuidanceService:
    """Decide e executa a avaliação de guidance de um documento lido."""

    def __init__(
        self: "GuidanceService",
        store: GuidanceStore,
        llm_factory: Callable[[], LLMPort] | None = None,
        llm_available: Callable[[], bool] | None = None,
        avaliador: AvaliarGuidanceUseCase | None = None,
    ) -> None:
        """Guarda o store e a estratégia de avaliação (LLM + fallback)."""
        self._store = store
        self._avaliador = avaliador or AvaliarGuidanceUseCase(
            store,
            extrair_guidance,
            llm_factory=llm_factory or _criar_llm,
            llm_available=llm_available or _llm_disponivel,
        )

    def precisa(self: "GuidanceService", arquivo: DocumentoArquivo) -> bool:
        """Indica se o documento deve disparar avaliação de guidance."""
        if arquivo.categoria != CATEGORIA_RELATORIO:
            return False
        cache = self._store.obter(arquivo.ticker)
        return self._avaliador.deve_avaliar(arquivo.ano, arquivo.mes, cache)

    def avaliar(
        self: "GuidanceService", arquivo: DocumentoArquivo, texto: str | None
    ) -> Guidance | None:
        """Avalia o texto do documento, ignorando-o quando não é extraível."""
        if not tem_texto(texto):
            return None
        return self._avaliador.avaliar_documento(
            arquivo.ticker,
            arquivo.categoria,
            arquivo.ano,
            arquivo.mes,
            texto or "",
            str(arquivo.caminho),
        )
