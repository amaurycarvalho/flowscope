"""Fonte de notícias do Plantão B3 para o VectorStore do llm-chat."""

from datetime import datetime, timedelta, timezone

from flowscope.application.structured_ports import RegulacaoRepository
from flowscope.domain.chat import DocumentoIndexavel, DocumentSource


class NoticiasSource(DocumentSource):
    """Obtém notícias do Plantão B3, independentemente do ticker."""

    def __init__(
        self: "NoticiasSource",
        repository: RegulacaoRepository,
        dias: int = 30,
    ) -> None:
        """Inicializa a fonte com o repositório e o período padrão de consulta."""
        self._repository = repository
        self._dias = dias

    @property
    def categoria(self: "NoticiasSource") -> str:
        """Retorna a categoria dos documentos fornecidos pela fonte."""
        return "noticias"

    def obter_documentos(
        self: "NoticiasSource", ticker: str | None = None
    ) -> list[DocumentoIndexavel]:
        """Obtém as notícias do Plantão B3 para o período configurado.

        O ticker é ignorado, pois as notícias são globais de mercado.
        """
        del ticker
        fim = datetime.now(timezone.utc).date()
        inicio = fim - timedelta(days=self._dias)
        return list(self._repository.listar_noticias(data_inicio=inicio, data_fim=fim))
