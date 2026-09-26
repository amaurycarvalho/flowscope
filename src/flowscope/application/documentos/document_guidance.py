"""Decisão e execução da avaliação de guidance ao ler um documento.

Concentra o portão da categoria ``Relatorio``, a supressão de documentos sem
texto extraível e a leitura do guidance em cache para decidir se o relatório
lido é mais recente. A avaliação é delegada ao caso de uso, que prefere a LLM e
recorre à extração determinística quando ela não está disponível. O extrator
determinístico e as estratégias de LLM são injetados pelo ponto de composição.
"""

from collections.abc import Callable

from flowscope.application.avaliar_guidance import (
    CATEGORIA_RELATORIO,
    AvaliarGuidanceUseCase,
    ExtratorGuidance,
)
from flowscope.application.guidance_port import GuidanceStore
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.documents.texto import tem_texto
from flowscope.domain.fii import Guidance
from flowscope.domain.llm import LLMPort


class GuidanceService:
    """Decide e executa a avaliação de guidance de um documento lido."""

    def __init__(
        self: "GuidanceService",
        store: GuidanceStore,
        llm_factory: Callable[[], LLMPort] | None = None,
        llm_available: Callable[[], bool] | None = None,
        avaliador: AvaliarGuidanceUseCase | None = None,
        extrator: ExtratorGuidance | None = None,
    ) -> None:
        """Guarda o store e a estratégia de avaliação (LLM + fallback)."""
        self._store = store
        if avaliador is not None:
            self._avaliador = avaliador
        elif extrator is not None:
            self._avaliador = AvaliarGuidanceUseCase(
                store,
                extrator,
                llm_factory=llm_factory,
                llm_available=llm_available,
            )
        else:
            raise ValueError(
                "GuidanceService exige 'avaliador' ou 'extrator'."
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
