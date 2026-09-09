"""Motor determinístico de métricas fundamentalistas de FIIs.

As funções de cálculo são puras, operam sobre ``decimal.Decimal`` e nunca
arredondam resultados intermediários. O arredondamento acontece somente na
apresentação. Cada métrica produz uma ``MetricEvidence`` com fórmula, entradas,
fontes e versão de cálculo (RFC-006 §3, RFC-007 §37).
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from flowscope.domain.fii.classification_faixas import (
    TendenciaFfo,
    classificar_tendencia_ffo,
)

#: Identificador de versão de cálculo das métricas FII.
CALCULATION_VERSION = "FII_ANALYSIS_V1"

#: Tolerância padrão da consistência ``P/FFO × FFO Yield ≈ 1``.
TOLERANCIA_CONSISTENCIA = Decimal("0.01")

#: Fator de alerta de distribuição acima do FFO (RFC-006 §16).
FATOR_ALERTA_DISTRIBUICAO = Decimal("1.25")

#: Fonte registrada quando o valor é derivado internamente.
FONTE_DERIVADA = "DERIVADO"


class Quality(Enum):
    """Qualidade dos dados de uma análise fundamentalista."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    WARNING = "warning"
    INVALID = "invalid"


class Inconsistencia(Enum):
    """Identificadores estáveis de inconsistências e alertas."""

    DATA_INCONSISTENCY = "DATA_INCONSISTENCY"
    NEGATIVE_FFO = "NEGATIVE_FFO"
    MARKET_VALUE_INVALID = "MARKET_VALUE_INVALID"
    HIGH_DISTRIBUTION_VS_FFO = "HIGH_DISTRIBUTION_VS_FFO"
    FFO_NOT_AVAILABLE = "FFO_NOT_AVAILABLE"


@dataclass(frozen=True)
class FiiSnapshot:
    """Snapshot normalizado de entrada do motor de métricas."""

    ticker: str
    reference_date: date
    price: Decimal
    shares_outstanding: Decimal
    net_asset_value: Decimal
    ffo_12m: Decimal
    ffo_3m: Decimal
    dividends_12m: Decimal


@dataclass(frozen=True)
class MetricEvidence:
    """Evidência de cálculo de uma métrica para auditoria."""

    metric: str
    value: Decimal | None
    formula: str
    inputs: dict[str, Decimal | str]
    sources: tuple[str, ...]
    reference_date: date
    calculation_version: str


@dataclass(frozen=True)
class MetricasFii:
    """Métricas fundamentalistas calculadas a partir de um snapshot."""

    market_value: Decimal | None
    ffo_yield: Decimal | None
    dividend_yield: Decimal | None
    p_ffo: Decimal | None
    p_vp: Decimal | None
    ffo_momentum: Decimal | None
    ffo_trend: TendenciaFfo | None
    ffo_trend_change: Decimal | None
    ffo_payout: Decimal | None
    quality: Quality
    warnings: tuple[str, ...]
    evidence: tuple[MetricEvidence, ...]


def market_value(price: Decimal, shares_outstanding: Decimal) -> Decimal:
    """Calcula o valor de mercado como ``price × shares_outstanding``."""
    return price * shares_outstanding


def ffo_yield(ffo_12m: Decimal, market_value: Decimal) -> Decimal:
    """Calcula o FFO Yield como ``FFO_12M / market_value``."""
    return ffo_12m / market_value


def p_ffo(market_value: Decimal, ffo_12m: Decimal) -> Decimal:
    """Calcula o P/FFO como ``market_value / FFO_12M``."""
    return market_value / ffo_12m


def p_vp(market_value: Decimal, net_asset_value: Decimal) -> Decimal:
    """Calcula o P/VP como ``market_value / net_asset_value``."""
    return market_value / net_asset_value


def dividend_yield(dividends_12m: Decimal, market_value: Decimal) -> Decimal:
    """Calcula o Dividend Yield como ``dividends_12m / market_value``."""
    return dividends_12m / market_value


def ffo_momentum(ffo_3m: Decimal, ffo_12m: Decimal) -> Decimal:
    """Calcula o FFO Momentum como ``(FFO_3M × 4) / FFO_12M − 1``."""
    return (ffo_3m * Decimal(4)) / ffo_12m - Decimal(1)


def ffo_payout(dividends_12m: Decimal, ffo_12m: Decimal) -> Decimal:
    """Calcula o índice de distribuição sobre o FFO."""
    return dividends_12m / ffo_12m


def verificar_consistencia(
    p_ffo: Decimal | None,
    ffo_yield: Decimal | None,
    tolerance: Decimal = TOLERANCIA_CONSISTENCIA,
) -> bool:
    """Indica se ``P/FFO × FFO Yield`` respeita a tolerância em torno de 1."""
    if p_ffo is None or ffo_yield is None:
        return True
    produto = p_ffo * ffo_yield
    return abs(produto - Decimal(1)) <= tolerance


def _evidencia(
    metric: str,
    value: Decimal | None,
    formula: str,
    inputs: dict[str, Decimal],
    fontes: tuple[str, ...],
    snapshot: FiiSnapshot,
) -> MetricEvidence:
    """Constrói a evidência padronizada de uma métrica."""
    return MetricEvidence(
        metric=metric,
        value=value,
        formula=formula,
        inputs={chave: valor for chave, valor in inputs.items()},
        sources=fontes,
        reference_date=snapshot.reference_date,
        calculation_version=CALCULATION_VERSION,
    )


def analisar_snapshot(
    snapshot: FiiSnapshot,
    *,
    fontes: tuple[str, ...] = (FONTE_DERIVADA,),
    tolerance: Decimal = TOLERANCIA_CONSISTENCIA,
) -> MetricasFii:
    """Calcula todas as métricas de um snapshot com regras de N/A e evidência.

    FFO não positivo torna ``N/A`` as métricas que dependem do FFO. Valor de
    mercado não positivo invalida o registro. Quando todos os dados estão
    disponíveis, a inconsistência ``P/FFO × FFO Yield ≈ 1`` é verificada e, em
    caso de violação, uma evidência de ``DATA_INCONSISTENCY`` é gerada.
    """
    warnings: list[str] = []
    evidencias: list[MetricEvidence] = []

    valor_mercado = market_value(snapshot.price, snapshot.shares_outstanding)
    if valor_mercado <= Decimal(0):
        return MetricasFii(
            market_value=None,
            ffo_yield=None,
            dividend_yield=None,
            p_ffo=None,
            p_vp=None,
            ffo_momentum=None,
            ffo_trend=None,
            ffo_trend_change=None,
            ffo_payout=None,
            quality=Quality.INVALID,
            warnings=(Inconsistencia.MARKET_VALUE_INVALID.value,),
            evidence=(),
        )

    evidencias.append(
        _evidencia(
            "MARKET_VALUE",
            valor_mercado,
            "price * shares_outstanding",
            {"price": snapshot.price, "shares_outstanding": snapshot.shares_outstanding},
            fontes,
            snapshot,
        )
    )

    ffo_positivo = snapshot.ffo_12m > Decimal(0)
    ffo_na = not ffo_positivo
    if ffo_na:
        warnings.append(Inconsistencia.NEGATIVE_FFO.value)

    yield_ffo = None if ffo_na else ffo_yield(snapshot.ffo_12m, valor_mercado)
    multiplo_ffo = None if ffo_na else p_ffo(valor_mercado, snapshot.ffo_12m)
    variacao: Decimal | None = None
    tendencia: TendenciaFfo | None = None
    if ffo_positivo:
        variacao = ffo_momentum(snapshot.ffo_3m, snapshot.ffo_12m)
        tendencia = classificar_tendencia_ffo(variacao)

    nav_positivo = snapshot.net_asset_value > Decimal(0)
    valor_vp = None if not nav_positivo else p_vp(valor_mercado, snapshot.net_asset_value)

    rendimento = dividend_yield(snapshot.dividends_12m, valor_mercado)

    payout = None
    if ffo_positivo and snapshot.dividends_12m >= Decimal(0):
        payout = ffo_payout(snapshot.dividends_12m, snapshot.ffo_12m)

    if yield_ffo is not None:
        evidencias.append(
            _evidencia(
                "FFO_YIELD",
                yield_ffo,
                "ffo_12m / market_value",
                {"ffo_12m": snapshot.ffo_12m, "market_value": valor_mercado},
                fontes,
                snapshot,
            )
        )
    if multiplo_ffo is not None:
        evidencias.append(
            _evidencia(
                "P_FFO",
                multiplo_ffo,
                "market_value / ffo_12m",
                {"market_value": valor_mercado, "ffo_12m": snapshot.ffo_12m},
                fontes,
                snapshot,
            )
        )
    if valor_vp is not None:
        evidencias.append(
            _evidencia(
                "P_VP",
                valor_vp,
                "market_value / net_asset_value",
                {"market_value": valor_mercado, "net_asset_value": snapshot.net_asset_value},
                fontes,
                snapshot,
            )
        )
    evidencias.append(
        _evidencia(
            "DIVIDEND_YIELD",
            rendimento,
            "dividends_12m / market_value",
            {"dividends_12m": snapshot.dividends_12m, "market_value": valor_mercado},
            fontes,
            snapshot,
        )
    )
    if variacao is not None:
        evidencias.append(
            _evidencia(
                "FFO_MOMENTUM",
                variacao,
                "(ffo_3m * 4) / ffo_12m - 1",
                {"ffo_3m": snapshot.ffo_3m, "ffo_12m": snapshot.ffo_12m},
                fontes,
                snapshot,
            )
        )

    if yield_ffo is not None and rendimento > yield_ffo * FATOR_ALERTA_DISTRIBUICAO:
        warnings.append(Inconsistencia.HIGH_DISTRIBUTION_VS_FFO.value)

    if not verificar_consistencia(multiplo_ffo, yield_ffo, tolerance):
        warnings.append(Inconsistencia.DATA_INCONSISTENCY.value)

    if ffo_na and not warnings:
        warnings.append(Inconsistencia.FFO_NOT_AVAILABLE.value)

    qualidade = _qualidade(
        ffo_na=ffo_na,
        nav_positivo=nav_positivo,
        warnings=tuple(warnings),
    )
    return MetricasFii(
        market_value=valor_mercado,
        ffo_yield=yield_ffo,
        dividend_yield=rendimento,
        p_ffo=multiplo_ffo,
        p_vp=valor_vp,
        ffo_momentum=variacao,
        ffo_trend=tendencia,
        ffo_trend_change=variacao,
        ffo_payout=payout,
        quality=qualidade,
        warnings=tuple(warnings),
        evidence=tuple(evidencias),
    )


def _qualidade(
    *, ffo_na: bool, nav_positivo: bool, warnings: tuple[str, ...]
) -> Quality:
    """Deriva a qualidade geral a partir das regras da RFC-006 §32."""
    if ffo_na or not nav_positivo:
        return Quality.PARTIAL
    if warnings:
        return Quality.WARNING
    return Quality.COMPLETE
