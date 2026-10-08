"""Porta do ledger de avaliação de guidance de distribuição por FII.

Define o contrato de leitura por ticker consumido pela análise fundamentalista
(o guidance corrente derivado) e o contrato de avaliação por Relatório Gerencial
consumido pelo serviço de avaliação, sem acoplar os consumidores à implementação
de infraestrutura.
"""

from typing import Protocol

from flowscope.domain.fii.guidance import AvaliacaoGuidance, Guidance


class GuidanceStore(Protocol):
    """Contrato do ledger persistente de avaliações de guidance de um FII."""

    def obter(self: "GuidanceStore", ticker: str) -> Guidance | None:
        """Retorna o guidance corrente derivado, ou ``None`` quando ausente."""
        ...

    def obter_avaliacao(
        self: "GuidanceStore", ticker: str, chave: str
    ) -> AvaliacaoGuidance | None:
        """Retorna a avaliação do Relatório Gerencial identificado por ``chave``."""
        ...

    def salvar_avaliacao(
        self: "GuidanceStore",
        ticker: str,
        chave: str,
        avaliacao: AvaliacaoGuidance,
    ) -> None:
        """Grava a avaliação do RG, substituindo a anterior da mesma chave."""
        ...
