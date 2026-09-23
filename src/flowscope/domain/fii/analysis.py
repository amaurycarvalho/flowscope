"""Modelos de domínio da análise fundamentalista de FIIs.

Reúne as observações normalizadas produzidas pelos adapters (patrimônio, FFO e
preço de mercado) e o resultado agregado por ticker consumido pela camada de
apresentação.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from flowscope.domain.fii.classification import (
    ClassificacaoAtivo,
    ClassificacaoExibicao,
)
from flowscope.domain.fii.classification_faixas import (
    ClasseCotistas,
    ClassePatrimonio,
    TendenciaFfo,
)
from flowscope.domain.fii.dividends import UltimoDividendo
from flowscope.domain.fii.guidance import Guidance
from flowscope.domain.fii.metrics import MetricasFii, ResultadoMargem


@dataclass(frozen=True)
class PatrimonioFii:
    """Patrimônio líquido, cotas e cotistas de um FII na data de referência."""

    reference_date: date
    net_asset_value: Decimal
    shares_outstanding: Decimal
    cotistas: int | None
    fonte: str
    vp_cota: Decimal | None = None


@dataclass(frozen=True)
class FfoObservacao:
    """FFO dos últimos 12 e 3 meses, conforme reportado pela fonte."""

    ffo_12m: Decimal
    ffo_3m: Decimal
    fonte: str
    metodologia: str = "SOURCE_REPORTED"


@dataclass(frozen=True)
class PrecoObservacao:
    """Último preço de fechamento disponível até a data de referência."""

    preco: Decimal
    data_preco: date
    fonte: str


@dataclass(frozen=True)
class MargensFii:
    """Razões de FFO, dividendos e receita exibidas na tabela de Fundamentos."""

    ffo_receita_12m: ResultadoMargem
    ffo_receita_3m: ResultadoMargem
    dividendos_receita_12m: ResultadoMargem
    dividendos_receita_3m: ResultadoMargem
    dividendos_ffo_12m: ResultadoMargem
    dividendos_ffo_3m: ResultadoMargem
    ffo_trend: TendenciaFfo | None = None


@dataclass(frozen=True)
class AnaliseFundamental:
    """Resultado da análise fundamentalista de um ticker da watchlist."""

    ticker: str
    nome: str | None
    classificacao: ClassificacaoAtivo
    ultimo_dividendo: UltimoDividendo
    dividendos_12m_por_cota: Decimal | None
    metricas: MetricasFii | None
    margens: MargensFii | None = None
    cotacao: Decimal | None = None
    vp_cota: Decimal | None = None
    p_l: Decimal | None = None
    classificacao_exibicao: ClassificacaoExibicao | None = None
    cotas: Decimal | None = None
    cotistas: int | None = None
    patrimonio: Decimal | None = None
    classe_cotistas: ClasseCotistas | None = None
    classe_patrimonio: ClassePatrimonio | None = None
    data_referencia: date | None = None
    lpa: Decimal | None = None
    roe: Decimal | None = None
    roic: Decimal | None = None
    cap_rate: Decimal | None = None
    vacancia_media: Decimal | None = None
    qtd_imoveis: int | None = None
    preco_tipico: Decimal | None = None
    pct_preco_tipico: Decimal | None = None
    indexadores: dict[str, Decimal] = field(default_factory=dict)
    cnpj: str | None = None
    nome_administrador: str | None = None
    cnpj_administrador: str | None = None
    nome_gestor: str | None = None
    cnpj_gestor: str | None = None
    bdr_nivel: str | None = None
    bdr_observacao: str | None = None
    nome_depositario: str | None = None
    nome_empresa_bdr: str | None = None
    isin: str | None = None
    guidance: Guidance | None = None
    avisos: tuple[str, ...] = ()
    erro: str | None = None
