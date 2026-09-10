"""Portas da análise fundamentalista de FIIs.

As portas desacoplam o caso de uso da infraestrutura: proventos e identidade
vêm de ``FiiFundamentalRepository`` (que consome ``structured-earnings`` e
``code-cvm-resolution``), patrimônio da CVM, FFO de um provedor e o preço de
fechamento de dados de mercado já existentes.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable

from flowscope.domain.fii.analysis import FfoObservacao, PatrimonioFii, PrecoObservacao
from flowscope.domain.structured import Provento

#: Chaves dos campos normalizados da composição de fontes fundamentalistas.
CAMPO_NOME = "nome"
CAMPO_COTACAO = "cotacao"
CAMPO_DIVIDEND_YIELD = "dividend_yield"
CAMPO_FFO_YIELD = "ffo_yield"
CAMPO_P_VP = "p_vp"
CAMPO_P_FFO = "p_ffo"
CAMPO_FFO_TREND = "ffo_trend"
CAMPO_FFO_12M = "ffo_12m"
CAMPO_FFO_3M = "ffo_3m"
CAMPO_DIVIDENDO_POR_COTA = "dividendo_por_cota"

#: Conjunto canônico de campos que a composição de fontes tenta resolver.
CAMPOS_FUNDAMENTAIS = frozenset(
    {
        CAMPO_NOME,
        CAMPO_COTACAO,
        CAMPO_DIVIDEND_YIELD,
        CAMPO_FFO_YIELD,
        CAMPO_P_VP,
        CAMPO_P_FFO,
        CAMPO_FFO_TREND,
        CAMPO_FFO_12M,
        CAMPO_FFO_3M,
        CAMPO_DIVIDENDO_POR_COTA,
    }
)


@dataclass(frozen=True)
class CampoFundamental:
    """Valor de um campo fundamentalista e a fonte que o forneceu."""

    valor: Decimal | int | str | None
    fonte: str | None = None


@runtime_checkable
class FundamentalDataProvider(Protocol):
    """Contrato de uma fonte de campos fundamentalistas normalizados."""

    def obter(
        self: "FundamentalDataProvider", ticker: str, reference_date: date
    ) -> dict[str, CampoFundamental]:
        """Retorna os campos disponíveis na fonte, indexados por chave."""
        ...



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
