"""Modelos de domínio da análise fundamentalista de FIIs.

Reúne as observações normalizadas produzidas pelos adapters (patrimônio, FFO e
preço de mercado) e o resultado agregado por ticker consumido pela camada de
apresentação.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from flowscope.domain.fii.classification import (
    ClassificacaoAtivo,
    ClassificacaoExibicao,
)
from flowscope.domain.fii.classification_faixas import (
    ClasseCotistas,
    ClassePatrimonio,
)
from flowscope.domain.fii.dividends import UltimoDividendo
from flowscope.domain.fii.metrics import MetricasFii


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
class AnaliseFundamental:
    """Resultado da análise fundamentalista de um ticker da watchlist."""

    ticker: str
    nome: str | None
    classificacao: ClassificacaoAtivo
    ultimo_dividendo: UltimoDividendo
    dividendos_12m_por_cota: Decimal | None
    metricas: MetricasFii | None
    cotacao: Decimal | None = None
    vp_cota: Decimal | None = None
    p_l: Decimal | None = None
    classificacao_exibicao: ClassificacaoExibicao | None = None
    cotistas: int | None = None
    patrimonio: Decimal | None = None
    classe_cotistas: ClasseCotistas | None = None
    classe_patrimonio: ClassePatrimonio | None = None
    data_referencia: date | None = None
    avisos: tuple[str, ...] = ()
    erro: str | None = None
