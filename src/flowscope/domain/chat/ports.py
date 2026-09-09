"""Contratos de indexação de documentos para o VectorStore do llm-chat."""

from abc import ABC, abstractmethod
from typing import Protocol


class DocumentoIndexavel(Protocol):
    """Contrato de documento com representação textual para indexação."""

    def to_text(self: "DocumentoIndexavel") -> str:
        """Produz representação textual densa do documento."""
        ...


class DocumentSource(ABC):
    """Fonte abstrata de documentos indexáveis para o VectorStore."""

    @property
    @abstractmethod
    def categoria(self: "DocumentSource") -> str:
        """Retorna a categoria dos documentos fornecidos pela fonte."""
        ...

    @abstractmethod
    def obter_documentos(
        self: "DocumentSource", ticker: str | None = None
    ) -> list[DocumentoIndexavel]:
        """Obtém documentos indexáveis, opcionalmente filtrando por ticker."""
        ...
