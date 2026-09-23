"""Porta do cache de guidance de distribuição por FII.

Define o contrato de leitura por ticker consumido pela análise fundamentalista e
o contrato de gravação consumido pelo serviço de avaliação, sem acoplar os
consumidores à implementação de infraestrutura.
"""

from typing import Protocol

from flowscope.domain.fii.guidance import Guidance


class GuidanceStore(Protocol):
    """Contrato do cache persistente do guidance de um FII."""

    def obter(self: "GuidanceStore", ticker: str) -> Guidance | None:
        """Retorna o guidance do ticker, ou ``None`` quando ausente."""
        ...

    def salvar(self: "GuidanceStore", ticker: str, guidance: Guidance) -> None:
        """Grava o guidance do ticker, substituindo o anterior."""
        ...
