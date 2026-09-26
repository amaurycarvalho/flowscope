"""Porta do cache persistente de resumos de documentos.

Espelha a ``DocumentTextStore``: define o contrato de leitura/gravação por
ticker consumido pela aplicação, sem acoplar o consumidor à implementação de
infraestrutura.
"""

from typing import Protocol, runtime_checkable

from flowscope.application.resumo_documento import ResumoDocumento


@runtime_checkable
class DocumentSummaryStore(Protocol):
    """Contrato do cache persistente dos resumos por documento."""

    def obter(
        self: "DocumentSummaryStore", ticker: str, chave: str
    ) -> ResumoDocumento | None:
        """Retorna o resumo de um documento, ou ``None`` quando ausente."""
        ...

    def salvar(
        self: "DocumentSummaryStore",
        ticker: str,
        chave: str,
        short_summary: str,
        long_summary: str,
    ) -> None:
        """Grava o resumo de um documento preservando os demais do ticker."""
        ...
