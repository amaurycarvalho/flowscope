"""Motor determinístico de Funds From Operations (RFC-010).

Funções puras que classificam componentes, somam apenas os recorrentes e
produzem FFO mensal, 12m, por cota, FFO Yield e P/FFO, com qualidade,
proveniência e reconciliação. O cálculo é independente do ticker e do gestor.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from flowscope.domain.ffo.components import (
    FFOComponent,
    FFOComponentType,
    FFOQuality,
)

#: Versão do cálculo do FFO.
FFO_CALCULATION_VERSION = "FFO_V1"

#: Limite de materialidade abaixo do qual a qualidade é ``HIGH``.
LIMITE_MATERIALIDADE_MEDIO = Decimal("0.01")

#: Limite de materialidade abaixo do qual a qualidade é ``MEDIUM``.
LIMITE_MATERIALIDADE_BAIXO = Decimal("0.05")

#: Limite de divergência relativa aceito na reconciliação.
LIMITE_RECONCILIACAO = Decimal("0.01")

_MESES_12 = 12
_MESES_3 = 3


@dataclass(frozen=True)
class FFOResult:
    """Resultado do motor determinístico de FFO."""

    reference_date: date
    ffo_12m: Decimal | None
    ffo_3m: Decimal | None
    ffo_month: Decimal | None
    weighted_average_shares: Decimal | None
    ffo_per_share: Decimal | None
    market_price: Decimal | None
    market_price_date: date | None
    ffo_yield: Decimal | None
    p_ffo: Decimal | None
    quality: FFOQuality
    warnings: tuple[str, ...]
    components: tuple[FFOComponent, ...]
    calculation_version: str = FFO_CALCULATION_VERSION


def calculate_ffo(components: Iterable[FFOComponent]) -> Decimal:
    """Soma os valores dos componentes recorrentes, excluindo os demais."""
    total = Decimal(0)
    for componente in components:
        if componente.classification is FFOComponentType.RECURRING:
            total += componente.value
    return total


def media_ponderada_cotas(
    observacoes: Sequence[tuple[Decimal, int]],
) -> Decimal | None:
    """Calcula a média ponderada das cotas pelo tempo de cada observação."""
    total_dias = sum(dias for _, dias in observacoes)
    if total_dias <= 0:
        return None
    ponderado = sum(cotas * dias for cotas, dias in observacoes)
    return ponderado / Decimal(total_dias)


def _resolver_shares(
    weighted_average_shares: Decimal | None,
    cotas_observacoes: Sequence[tuple[Decimal, int]] | None,
) -> Decimal | None:
    """Resolve as cotas médias, recorrendo às observações quando necessário."""
    if weighted_average_shares is not None:
        return weighted_average_shares
    if cotas_observacoes:
        return media_ponderada_cotas(cotas_observacoes)
    return None


def _ffo_por_cota(ffo_12m: Decimal | None, shares: Decimal | None) -> Decimal | None:
    """Calcula o FFO por cota quando base e cotas são positivas."""
    if ffo_12m is not None and shares is not None and shares > 0:
        return ffo_12m / shares
    return None


def _yields(
    ffo_per_share: Decimal | None, market_price: Decimal | None
) -> tuple[Decimal | None, Decimal | None]:
    """Calcula FFO Yield e P/FFO quando preço e FFO por cota são válidos."""
    if (
        ffo_per_share is not None
        and market_price is not None
        and market_price > 0
    ):
        return ffo_per_share / market_price, market_price / ffo_per_share
    return None, None


def _reconciliar_se_aplicavel(
    reported: Decimal | None, ffo_12m: Decimal | None, limite: Decimal
) -> str | None:
    """Reconcilia o FFO calculado com o reportado, quando ambos existem."""
    if reported is not None and ffo_12m is not None:
        return _reconciliar(ffo_12m, reported, limite)
    return None


def calcular_ffo(
    components: Iterable[FFOComponent],
    reference_date: date,
    *,
    market_price: Decimal | None = None,
    market_price_date: date | None = None,
    weighted_average_shares: Decimal | None = None,
    cotas_observacoes: Sequence[tuple[Decimal, int]] | None = None,
    reported: Decimal | None = None,
    limite_materialidade_medio: Decimal = LIMITE_MATERIALIDADE_MEDIO,
    limite_materialidade_baixo: Decimal = LIMITE_MATERIALIDADE_BAIXO,
    limite_reconciliacao: Decimal = LIMITE_RECONCILIACAO,
) -> FFOResult:
    """Calcula o FFO completo a partir dos componentes normalizados."""
    componentes = tuple(components)
    warnings: list[str] = []
    por_mes = _recorrentes_por_mes(componentes)

    ffo_12m = _soma_janela(por_mes, reference_date, _MESES_12)
    if ffo_12m is None:
        warnings.append("INSUFFICIENT_BASE")
    ffo_3m = _soma_janela(por_mes, reference_date, _MESES_3)
    ffo_month = por_mes.get(_mes(reference_date))

    shares = _resolver_shares(weighted_average_shares, cotas_observacoes)
    ffo_per_share = _ffo_por_cota(ffo_12m, shares)
    ffo_yield, p_ffo = _yields(ffo_per_share, market_price)

    quality = _qualidade(
        componentes, limite_materialidade_medio, limite_materialidade_baixo
    )
    aviso = _reconciliar_se_aplicavel(reported, ffo_12m, limite_reconciliacao)
    if aviso is not None:
        warnings.append(aviso)

    return FFOResult(
        reference_date=reference_date,
        ffo_12m=ffo_12m,
        ffo_3m=ffo_3m,
        ffo_month=ffo_month,
        weighted_average_shares=shares,
        ffo_per_share=ffo_per_share,
        market_price=market_price,
        market_price_date=market_price_date,
        ffo_yield=ffo_yield,
        p_ffo=p_ffo,
        quality=quality,
        warnings=tuple(warnings),
        components=componentes,
    )


def _recorrentes_por_mes(
    componentes: Sequence[FFOComponent],
) -> dict[tuple[int, int], Decimal]:
    """Agrupa a soma dos componentes recorrentes por competência."""
    por_mes: dict[tuple[int, int], Decimal] = {}
    for componente in componentes:
        if not componente.included_in_ffo:
            continue
        data = componente.provenance.reference_date if componente.provenance else None
        if data is None:
            continue
        chave = _mes(data)
        por_mes[chave] = por_mes.get(chave, Decimal(0)) + componente.value
    return por_mes


def _mes(data: date) -> tuple[int, int]:
    """Retorna a competência (ano, mês) de uma data."""
    return (data.year, data.month)


def _meses_janela(reference_date: date, quantidade: int) -> list[tuple[int, int]]:
    """Retorna as competências da janela terminando no mês de referência."""
    total = reference_date.year * 12 + (reference_date.month - 1)
    meses: list[tuple[int, int]] = []
    for offset in range(quantidade - 1, -1, -1):
        ano, mes = divmod(total - offset, 12)
        meses.append((ano, mes + 1))
    return meses


def _soma_janela(
    por_mes: dict[tuple[int, int], Decimal],
    reference_date: date,
    quantidade: int,
) -> Decimal | None:
    """Soma a janela de meses, ou ``None`` quando a base está incompleta."""
    meses = _meses_janela(reference_date, quantidade)
    if not all(mes in por_mes for mes in meses):
        return None
    return sum((por_mes[mes] for mes in meses), Decimal(0))


def _qualidade(
    componentes: Sequence[FFOComponent],
    limite_medio: Decimal,
    limite_baixo: Decimal,
) -> FFOQuality:
    """Deriva a qualidade a partir da materialidade dos componentes UNKNOWN."""
    total = sum((abs(componente.value) for componente in componentes), Decimal(0))
    if total <= 0:
        return FFOQuality.HIGH
    desconhecido = sum(
        (
            abs(componente.value)
            for componente in componentes
            if componente.classification is FFOComponentType.UNKNOWN
        ),
        Decimal(0),
    )
    razao = desconhecido / total
    if razao <= limite_medio:
        return FFOQuality.HIGH
    if razao <= limite_baixo:
        return FFOQuality.MEDIUM
    return FFOQuality.LOW


def _reconciliar(
    calculado: Decimal, reportado: Decimal, limite: Decimal
) -> str | None:
    """Retorna um aviso quando a divergência relativa excede o limite."""
    if reportado == 0:
        return None
    diferenca = abs(calculado - reportado) / abs(reportado)
    if diferenca > limite:
        return "RECONCILIATION_DIVERGENCE"
    return None
