"""Portas da análise fundamentalista de FIIs.

As portas desacoplam o caso de uso da infraestrutura: proventos e identidade
vêm de ``FiiFundamentalRepository`` (que consome ``structured-earnings`` e
``code-cvm-resolution``), patrimônio da CVM, FFO de um provedor e o preço de
fechamento de dados de mercado já existentes.
"""

from datetime import date
from typing import Protocol

from flowscope.domain.fii.analysis import FfoObservacao, PatrimonioFii, PrecoObservacao
from flowscope.domain.structured import Provento


class FiiFundamentalRepository(Protocol):
    """Contrato de acesso a dados fundamentalistas e de identidade por ticker."""

    def obter_nome(self: "FiiFundamentalRepository", ticker: str) -> str | None:
        """Retorna o nome do ativo, ou ``None`` quando não houver dados."""
        ...

    def obter_proventos(
        self: "FiiFundamentalRepository", ticker: str, reference_date: date
    ) -> list[Provento]:
        """Retorna os proventos do ticker até a data de referência."""
        ...

    def obter_patrimonio(
        self: "FiiFundamentalRepository", ticker: str, reference_date: date
    ) -> PatrimonioFii | None:
        """Retorna patrimônio, cotas e cotistas, ou ``None`` quando indisponível."""
        ...


class FfoProvider(Protocol):
    """Contrato de obtenção do FFO reportado (12m e 3m)."""

    def obter_ffo(
        self: "FfoProvider", ticker: str, reference_date: date
    ) -> FfoObservacao | None:
        """Retorna o FFO observado, ou ``None`` quando indisponível."""
        ...


class MarketPricePort(Protocol):
    """Contrato de obtenção do preço de fechamento de um ticker."""

    def preco_fechamento(
        self: "MarketPricePort", ticker: str, reference_date: date
    ) -> PrecoObservacao | None:
        """Retorna o último fechamento até a data de referência."""
        ...
