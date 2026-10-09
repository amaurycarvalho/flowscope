"""Porta do ledger de avaliação de guidance de distribuição por FII.

Define o contrato de leitura por ticker consumido pela análise fundamentalista
(o guidance corrente derivado) e o contrato de avaliação por Relatório Gerencial
consumido pelo serviço de avaliação, sem acoplar os consumidores à implementação
de infraestrutura.
"""

from collections.abc import Mapping
from pathlib import Path
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

    def avaliacoes(
        self: "GuidanceStore", ticker: str
    ) -> Mapping[str, AvaliacaoGuidance]:
        """Retorna o mapa das avaliações do ticker, por chave de conteúdo."""
        ...

    def caminho(self: "GuidanceStore", ticker: str) -> Path:
        """Retorna o caminho do arquivo de ledger do ticker."""
        ...

    def salvar_avaliacao(
        self: "GuidanceStore",
        ticker: str,
        chave: str,
        avaliacao: AvaliacaoGuidance,
    ) -> None:
        """Grava a avaliação do RG, substituindo a anterior da mesma chave."""
        ...
