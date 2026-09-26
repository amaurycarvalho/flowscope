"""Porta do cache de texto extraído dos documentos.

Define o contrato de leitura/gravação por ticker consumido pela camada de
apresentação, sem acoplar o consumidor à implementação de infraestrutura.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class DocumentTextStore(Protocol):
    """Contrato do cache persistente do texto extraído por documento."""

    def obter(self: "DocumentTextStore", ticker: str, chave: str) -> str | None:
        """Retorna o texto de um documento, ou ``None`` quando ausente."""
        ...

    def salvar(
        self: "DocumentTextStore", ticker: str, chave: str, texto: str
    ) -> None:
        """Grava o texto de um documento preservando os demais do ticker."""
        ...
