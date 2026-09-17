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

#: Meses considerados para anualizar o último dividendo de um FII.
MESES_POR_ANO = 12

#: Número de trimestres usados para anualizar o dividendo de um BDR.
TRIMESTRES_POR_ANO = 4


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


def p_l(preco: Decimal, ultimo_dividendo: Decimal | None) -> Decimal | None:
    """Calcula o P/L de um FII em anos como ``preco / (ultimo_dividendo × 12)``.

    O último dividendo de um FII é mensal; multiplicá-lo por 12 o anualiza para
    que o P/L represente a quantidade de anos para recuperar o investimento,
    como no P/L de uma ação. Retorna ``None`` quando o último dividendo é
    ausente ou zero, evitando uma divisão indefinida.
    """
    if ultimo_dividendo is None or ultimo_dividendo == Decimal(0):
        return None
    return preco / (ultimo_dividendo * Decimal(MESES_POR_ANO))


def p_l_bdr(
    preco: Decimal | None, ultimo_dividendo: Decimal | None
) -> Decimal | None:
    """Calcula o P/L de um BDR como ``preco / (ultimo_dividendo × 4)``.

    O dividendo de um BDR é trimestral; multiplicá-lo por 4 o anualiza. Retorna
    ``None`` quando o preço ou o último dividendo são ausentes ou zero.
    """
    if preco is None or preco == Decimal(0):
        return None
    if ultimo_dividendo is None or ultimo_dividendo == Decimal(0):
        return None
    return preco / (ultimo_dividendo * Decimal(TRIMESTRES_POR_ANO))


def dividend_yield(dividends_12m: Decimal, market_value: Decimal) -> Decimal:
    """Calcula o Dividend Yield como ``dividends_12m / market_value``."""
    return dividends_12m / market_value


def ffo_momentum(ffo_3m: Decimal, ffo_12m: Decimal) -> Decimal:
    """Calcula o FFO Momentum como ``(FFO_3M × 4) / FFO_12M − 1``."""
    return (ffo_3m * Decimal(4)) / ffo_12m - Decimal(1)


def ffo_payout(dividends_12m: Decimal, ffo_12m: Decimal) -> Decimal:
    """Calcula o índice de distribuição sobre o FFO."""
    return dividends_12m / ffo_12m


class MotivoMargem(Enum):
    """Motivo de indisponibilidade de uma razão sobre a receita."""

    RECEITA_NEGATIVA = "RECEITA_NEGATIVA"
    FFO_NEGATIVO = "FFO_NEGATIVO"
    RECEITA_E_FFO_NEGATIVOS = "RECEITA_E_FFO_NEGATIVOS"


@dataclass(frozen=True)
class ResultadoMargem:
    """Resultado de uma razão: valor numérico ou motivo de indisponibilidade."""

    valor: Decimal | None
    motivo: MotivoMargem | None = None


def ffo_receita(ffo: Decimal | None, receita: Decimal | None) -> ResultadoMargem:
    """Calcula ``FFO / Receita`` tratando sinais negativos e divisão por zero.

    Receita e FFO negativos exibem texto em vez de número; divisão por zero ou
    insumo ausente resultam em ``N/A`` (``valor`` e ``motivo`` nulos).
    """
    if ffo is None or receita is None or receita == Decimal(0):
        return ResultadoMargem(None)
    if receita < Decimal(0) and ffo < Decimal(0):
        return ResultadoMargem(None, MotivoMargem.RECEITA_E_FFO_NEGATIVOS)
    if receita < Decimal(0):
        return ResultadoMargem(None, MotivoMargem.RECEITA_NEGATIVA)
    if ffo < Decimal(0):
        return ResultadoMargem(None, MotivoMargem.FFO_NEGATIVO)
    return ResultadoMargem(ffo / receita)


def dividendos_receita(
    dividendos: Decimal | None, receita: Decimal | None
) -> ResultadoMargem:
    """Calcula ``Dividendos / Receita`` com as regras de sinal e divisão por zero."""
    if dividendos is None or receita is None or receita == Decimal(0):
        return ResultadoMargem(None)
    if receita < Decimal(0):
        return ResultadoMargem(None, MotivoMargem.RECEITA_NEGATIVA)
    return ResultadoMargem(dividendos / receita)


def dividendos_ffo(
    dividendos: Decimal | None, ffo: Decimal | None
) -> ResultadoMargem:
    """Calcula ``Dividendos / FFO`` com as regras de sinal e divisão por zero."""
    if dividendos is None or ffo is None or ffo == Decimal(0):
        return ResultadoMargem(None)
    if ffo < Decimal(0):
        return ResultadoMargem(None, MotivoMargem.FFO_NEGATIVO)
    return ResultadoMargem(dividendos / ffo)


def tendencia_margem_ffo(
    margem_12m: Decimal | None, margem_3m: Decimal | None
) -> TendenciaFfo | None:
    """Classifica a tendência pela diferença, em pontos percentuais, das margens.

    As margens são frações; a diferença ``margem_3m - margem_12m`` equivale à
    diferença em pontos percentuais e reutiliza as faixas determinísticas de
    ``classificar_tendencia_ffo``. Retorna ``None`` quando faltar uma margem.
    """
    if margem_12m is None or margem_3m is None:
        return None
    return classificar_tendencia_ffo(margem_3m - margem_12m)


def preco_tipico(
    maxima_52: Decimal | None,
    minima_52: Decimal | None,
    cotacao: Decimal | None,
) -> Decimal | None:
    """Calcula o Preço Típico como a média das cotações de 52 semanas.

    Retorna ``None`` quando qualquer insumo estiver ausente, evitando uma média
    parcial que não represente o preço típico.
    """
    if maxima_52 is None or minima_52 is None or cotacao is None:
        return None
    return (maxima_52 + minima_52 + cotacao) / Decimal(3)


def percentual_preco_tipico(
    cotacao: Decimal | None, preco_tipico: Decimal | None
) -> Decimal | None:
    """Calcula o desvio percentual da cotação em relação ao Preço Típico.

    Retorna ``None`` quando a cotação ou o preço típico estão ausentes ou o
    preço típico é zero, evitando uma divisão indefinida.
    """
    if cotacao is None or preco_tipico is None or preco_tipico == Decimal(0):
        return None
    return (cotacao - preco_tipico) / preco_tipico


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


@dataclass(frozen=True)
class _Indicadores:
    """Indicadores intermediários do cálculo de um snapshot."""

    ffo_na: bool
    yield_ffo: Decimal | None
    multiplo_ffo: Decimal | None
    variacao: Decimal | None
    tendencia: TendenciaFfo | None
    nav_positivo: bool
    valor_vp: Decimal | None
    rendimento: Decimal
    payout: Decimal | None


def _calcular_indicadores(
    snapshot: FiiSnapshot, valor_mercado: Decimal
) -> _Indicadores:
    """Calcula os indicadores derivados, respeitando as regras de N/A."""
    ffo_positivo = snapshot.ffo_12m > Decimal(0)
    ffo_na = not ffo_positivo
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
    return _Indicadores(
        ffo_na=ffo_na,
        yield_ffo=yield_ffo,
        multiplo_ffo=multiplo_ffo,
        variacao=variacao,
        tendencia=tendencia,
        nav_positivo=nav_positivo,
        valor_vp=valor_vp,
        rendimento=rendimento,
        payout=payout,
    )


def _montar_evidencias(
    snapshot: FiiSnapshot,
    valor_mercado: Decimal,
    ind: _Indicadores,
    fontes: tuple[str, ...],
) -> list[MetricEvidence]:
    """Monta a lista de evidências das métricas calculadas."""
    evidencias = [
        _evidencia(
            "MARKET_VALUE",
            valor_mercado,
            "price * shares_outstanding",
            {"price": snapshot.price, "shares_outstanding": snapshot.shares_outstanding},
            fontes,
            snapshot,
        )
    ]
    if ind.yield_ffo is not None:
        evidencias.append(
            _evidencia(
                "FFO_YIELD",
                ind.yield_ffo,
                "ffo_12m / market_value",
                {"ffo_12m": snapshot.ffo_12m, "market_value": valor_mercado},
                fontes,
                snapshot,
            )
        )
    if ind.multiplo_ffo is not None:
        evidencias.append(
            _evidencia(
                "P_FFO",
                ind.multiplo_ffo,
                "market_value / ffo_12m",
                {"market_value": valor_mercado, "ffo_12m": snapshot.ffo_12m},
                fontes,
                snapshot,
            )
        )
    if ind.valor_vp is not None:
        evidencias.append(
            _evidencia(
                "P_VP",
                ind.valor_vp,
                "market_value / net_asset_value",
                {"market_value": valor_mercado, "net_asset_value": snapshot.net_asset_value},
                fontes,
                snapshot,
            )
        )
    evidencias.append(
        _evidencia(
            "DIVIDEND_YIELD",
            ind.rendimento,
            "dividends_12m / market_value",
            {"dividends_12m": snapshot.dividends_12m, "market_value": valor_mercado},
            fontes,
            snapshot,
        )
    )
    if ind.variacao is not None:
        evidencias.append(
            _evidencia(
                "FFO_MOMENTUM",
                ind.variacao,
                "(ffo_3m * 4) / ffo_12m - 1",
                {"ffo_3m": snapshot.ffo_3m, "ffo_12m": snapshot.ffo_12m},
                fontes,
                snapshot,
            )
        )
    return evidencias


def _coletar_alertas(ind: _Indicadores, tolerance: Decimal) -> list[str]:
    """Coleta as inconsistências e alertas aplicáveis ao snapshot."""
    warnings: list[str] = []
    if ind.ffo_na:
        warnings.append(Inconsistencia.NEGATIVE_FFO.value)
    if ind.yield_ffo is not None and ind.rendimento > ind.yield_ffo * FATOR_ALERTA_DISTRIBUICAO:
        warnings.append(Inconsistencia.HIGH_DISTRIBUTION_VS_FFO.value)
    if not verificar_consistencia(ind.multiplo_ffo, ind.yield_ffo, tolerance):
        warnings.append(Inconsistencia.DATA_INCONSISTENCY.value)
    if ind.ffo_na and not warnings:
        warnings.append(Inconsistencia.FFO_NOT_AVAILABLE.value)
    return warnings


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

    ind = _calcular_indicadores(snapshot, valor_mercado)
    evidencias = _montar_evidencias(snapshot, valor_mercado, ind, fontes)
    warnings = _coletar_alertas(ind, tolerance)
    qualidade = _qualidade(
        ffo_na=ind.ffo_na,
        nav_positivo=ind.nav_positivo,
        warnings=tuple(warnings),
    )
    return MetricasFii(
        market_value=valor_mercado,
        ffo_yield=ind.yield_ffo,
        dividend_yield=ind.rendimento,
        p_ffo=ind.multiplo_ffo,
        p_vp=ind.valor_vp,
        ffo_momentum=ind.variacao,
        ffo_trend=ind.tendencia,
        ffo_trend_change=ind.variacao,
        ffo_payout=ind.payout,
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
