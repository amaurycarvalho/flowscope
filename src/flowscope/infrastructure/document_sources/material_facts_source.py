"""Fonte de documentos de fatos relevantes para o VectorStore do llm-chat."""

import logging
from datetime import datetime, timedelta, timezone

from flowscope.application.structured_ports import RegulacaoRepository
from flowscope.domain.chat import DocumentoIndexavel, DocumentSource
from flowscope.domain.structured import CategoriaMaterialFact

logger = logging.getLogger(__name__)


class MaterialFactsSource(DocumentSource):
    """Obtém documentos do ``GetMaterialFacts`` para qualquer ticker listado."""

    def __init__(
        self: "MaterialFactsSource",
        repository: RegulacaoRepository,
        dias: int = 30,
    ) -> None:
        """Inicializa a fonte com o repositório e o período padrão de consulta."""
        self._repository = repository
        self._dias = dias

    @property
    def categoria(self: "MaterialFactsSource") -> str:
        """Retorna a categoria dos documentos fornecidos pela fonte."""
        return "fatos_relevantes"

    def obter_documentos(
        self: "MaterialFactsSource", ticker: str | None = None
    ) -> list[DocumentoIndexavel]:
        """Obtém os documentos regulatórios do ticker, tolerando falhas por categoria."""
        if not ticker:
            return []
        code_cvm = self._repository.resolver_code_cvm(ticker)
        if code_cvm is None:
            return []
        fim = datetime.now(timezone.utc).date()
        inicio = fim - timedelta(days=self._dias)
        documentos: list[DocumentoIndexavel] = []
        for categoria in CategoriaMaterialFact:
            try:
                itens = self._repository.listar_fatos_relevantes(
                    code_cvm,
                    categoria,
                    inicio,
                    fim,
                    ticker=ticker,
                )
                documentos.extend(itens)
            except Exception as e:
                logger.warning(
                    "Falha na categoria %s do ticker %s: %s",
                    categoria.value,
                    ticker,
                    e,
                )
        return documentos
