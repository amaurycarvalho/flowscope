"""Portas da análise fundamentalista de FIIs.

As portas desacoplam o caso de uso da infraestrutura: proventos e identidade
vêm de ``FiiFundamentalRepository`` (que consome ``structured-earnings`` e
``code-cvm-resolution``), patrimônio da CVM, FFO de um provedor e o preço de
fechamento de dados de mercado já existentes.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Protocol, runtime_checkable

from flowscope.domain.fii.analysis import FfoObservacao, PatrimonioFii, PrecoObservacao
from flowscope.domain.fii.dividends import DividendoConsolidado
from flowscope.domain.structured import Provento

#: Chaves dos campos normalizados da composição de fontes fundamentalistas.
CAMPO_NOME = "nome"
CAMPO_COTACAO = "cotacao"
CAMPO_VP_COTA = "vp_cota"
CAMPO_DIVIDEND_YIELD = "dividend_yield"
CAMPO_FFO_YIELD = "ffo_yield"
CAMPO_P_VP = "p_vp"
CAMPO_P_L = "p_l"
CAMPO_P_FFO = "p_ffo"
CAMPO_FFO_TREND = "ffo_trend"
CAMPO_FFO_12M = "ffo_12m"
CAMPO_FFO_3M = "ffo_3m"
CAMPO_RECEITA_12M = "receita_12m"
CAMPO_RECEITA_3M = "receita_3m"
CAMPO_RENDIMENTOS_12M = "rendimentos_12m"
CAMPO_RENDIMENTOS_3M = "rendimentos_3m"
CAMPO_DIVIDENDO_POR_COTA = "dividendo_por_cota"
CAMPO_DISCRIMINADOR = "discriminador"
CAMPO_ESPECIE = "especie"
CAMPO_SETOR = "setor"
CAMPO_SUBSETOR = "subsetor"
CAMPO_SEGMENTO = "segmento"
CAMPO_GESTAO = "gestao"
CAMPO_CLASSIFICACAO_FII = "classificacao_fii"
CAMPO_QTD_IMOVEIS = "qtd_imoveis"
CAMPO_PATRIMONIO = "patrimonio"
CAMPO_DATA_REFERENCIA = "data_referencia"
CAMPO_MIN_52_SEM = "min_52_sem"
CAMPO_MAX_52_SEM = "max_52_sem"
CAMPO_LPA = "lpa"
CAMPO_ROE = "roe"
CAMPO_ROIC = "roic"
CAMPO_CAP_RATE = "cap_rate"
CAMPO_VACANCIA_MEDIA = "vacancia_media"
CAMPO_CNPJ = "cnpj"
CAMPO_ADMINISTRADOR = "administrador"
CAMPO_CNPJ_ADMINISTRADOR = "cnpj_administrador"
CAMPO_GESTOR = "gestor"
CAMPO_CNPJ_GESTOR = "cnpj_gestor"

#: Conjunto canônico de campos que a composição de fontes tenta resolver.
CAMPOS_FUNDAMENTAIS = frozenset(
    {
        CAMPO_NOME,
        CAMPO_COTACAO,
        CAMPO_VP_COTA,
        CAMPO_DIVIDEND_YIELD,
        CAMPO_FFO_YIELD,
        CAMPO_P_VP,
        CAMPO_P_L,
        CAMPO_P_FFO,
        CAMPO_FFO_TREND,
        CAMPO_FFO_12M,
        CAMPO_FFO_3M,
        CAMPO_RECEITA_12M,
        CAMPO_RECEITA_3M,
        CAMPO_RENDIMENTOS_12M,
        CAMPO_RENDIMENTOS_3M,
        CAMPO_DIVIDENDO_POR_COTA,
        CAMPO_DISCRIMINADOR,
        CAMPO_ESPECIE,
        CAMPO_SETOR,
        CAMPO_SUBSETOR,
        CAMPO_SEGMENTO,
        CAMPO_GESTAO,
        CAMPO_CLASSIFICACAO_FII,
        CAMPO_QTD_IMOVEIS,
        CAMPO_PATRIMONIO,
        CAMPO_DATA_REFERENCIA,
        CAMPO_MIN_52_SEM,
        CAMPO_MAX_52_SEM,
        CAMPO_LPA,
        CAMPO_ROE,
        CAMPO_ROIC,
        CAMPO_CAP_RATE,
        CAMPO_VACANCIA_MEDIA,
        CAMPO_CNPJ,
        CAMPO_ADMINISTRADOR,
        CAMPO_CNPJ_ADMINISTRADOR,
        CAMPO_GESTOR,
        CAMPO_CNPJ_GESTOR,
    }
)


@dataclass(frozen=True)
class CampoFundamental:
    """Valor de um campo fundamentalista e a fonte que o forneceu."""

    valor: Decimal | int | str | date | None
    fonte: str | None = None


class OrigemDados(Enum):
    """Origem do dado fundamentalista devolvido por uma fonte."""

    CACHE = "cache"
    REDE = "rede"


@runtime_checkable
class FundamentalDataProvider(Protocol):
    """Contrato de uma fonte de campos fundamentalistas normalizados."""

    def obter(
        self: "FundamentalDataProvider", ticker: str, reference_date: date
    ) -> dict[str, CampoFundamental]:
        """Retorna os campos disponíveis na fonte, indexados por chave."""
        ...


@runtime_checkable
class AcionistasProvider(Protocol):
    """Contrato de obtenção da quantidade de acionistas de uma companhia aberta."""

    def obter_acionistas(
        self: "AcionistasProvider", ticker: str, reference_date: date
    ) -> int | None:
        """Retorna a quantidade de acionistas, ou ``None`` quando indisponível."""
        ...


@runtime_checkable
class IndexadoresProvider(Protocol):
    """Contrato de obtenção dos percentuais de patrimônio por indexador."""

    def obter_indexadores(
        self: "IndexadoresProvider", ticker: str, reference_date: date
    ) -> dict[str, Decimal]:
        """Retorna o percentual por indexador, ou vazio quando indisponível."""
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


@runtime_checkable
class DividendHistoryProvider(Protocol):
    """Contrato de um histórico de dividendos com origem por entrada.

    Complementa a fonte primária (B3) com dados de outras origens (ex.: CVM),
    preservando em ``DividendoConsolidado.fonte`` a procedência de cada valor.
    """

    def obter_dividendos(
        self: "DividendHistoryProvider", ticker: str, reference_date: date
    ) -> list[DividendoConsolidado]:
        """Retorna os dividendos do ticker até a data de referência."""
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

    def extremos_preco(
        self: "MarketPricePort",
        ticker: str,
        reference_date: date,
        janela: timedelta,
    ) -> tuple[Decimal, Decimal] | None:
        """Retorna ``(mínimo, máximo)`` da janela, ou ``None`` quando vazia."""
        ...
