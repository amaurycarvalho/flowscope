"""Métricas de dividendo por ticker, limitadas a proventos de Rendimento.

A Fase A da tabela fundamentalista consome apenas proventos do tipo
``Rendimento``; ``Amortização`` é sempre ignorada. A tendência compara o
último rendimento com o imediatamente anterior usando uma banda configurável
(padrão ±5%), espelhando a RFC-006.
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from flowscope.domain.structured import Provento

#: Tipo de provento considerado como dividendo.
TIPO_RENDIMENTO = "Rendimento"

#: Banda de tolerância padrão da tendência do dividendo.
BANDA_PADRAO = Decimal("0.05")

#: Meses do período de acumulação do Dividend Yield de 12 meses.
JANELA_MESES_12M = 12


class TendenciaDividendo(Enum):
    """Tendência do último dividendo em relação ao anterior."""

    SUBINDO = "SUBINDO"
    CAINDO = "CAINDO"
    MANTEVE = "MANTEVE"
    N_A = "N/A"


@dataclass(frozen=True)
class UltimoDividendo:
    """Último dividendo de um ticker com a respectiva tendência."""

    data_com: date | None
    valor: Decimal | None
    valor_anterior: Decimal | None
    tendencia: TendenciaDividendo


def _rendimentos_ordenados(
    proventos: list[Provento], reference_date: date | None
) -> list[Provento]:
    """Filtra rendimentos válidos e os ordena por data-base crescente."""
    rendimentos: list[Provento] = []
    for provento in proventos:
        if provento.tipo != TIPO_RENDIMENTO or provento.data_base is None:
            continue
        if reference_date is not None and provento.data_base > reference_date:
            continue
        rendimentos.append(provento)
    rendimentos.sort(key=lambda provento: provento.data_base or date.min)
    return rendimentos


def ultima_data_com(rendimentos: list[Provento]) -> date | None:
    """Retorna a data-base (data-com) do rendimento mais recente."""
    if not rendimentos:
        return None
    return rendimentos[-1].data_base


def ultimo_valor(rendimentos: list[Provento]) -> Decimal | None:
    """Retorna o valor do rendimento mais recente."""
    if not rendimentos:
        return None
    return rendimentos[-1].valor_por_unidade.value


def calcular_tendencia(
    rendimentos: list[Provento], banda: Decimal = BANDA_PADRAO
) -> TendenciaDividendo:
    """Classifica a tendência comparando o último com o anterior.

    ``SUBINDO`` quando ``último ≥ anterior × (1 + banda)``, ``CAINDO`` quando
    ``último ≤ anterior × (1 − banda)`` e ``MANTEVE`` caso contrário. Sem
    dividendo anterior a tendência é ``N/A``.
    """
    if len(rendimentos) < 2:
        return TendenciaDividendo.N_A
    ultimo = rendimentos[-1].valor_por_unidade.value
    anterior = rendimentos[-2].valor_por_unidade.value
    if ultimo >= anterior * (Decimal(1) + banda):
        return TendenciaDividendo.SUBINDO
    if ultimo <= anterior * (Decimal(1) - banda):
        return TendenciaDividendo.CAINDO
    return TendenciaDividendo.MANTEVE


def calcular_ultimo_dividendo(
    proventos: list[Provento],
    reference_date: date | None = None,
    banda: Decimal = BANDA_PADRAO,
) -> UltimoDividendo:
    """Calcula a última data-com, o último dividendo e sua tendência."""
    rendimentos = _rendimentos_ordenados(proventos, reference_date)
    if not rendimentos:
        return UltimoDividendo(
            data_com=None,
            valor=None,
            valor_anterior=None,
            tendencia=TendenciaDividendo.N_A,
        )
    anterior = (
        rendimentos[-2].valor_por_unidade.value if len(rendimentos) > 1 else None
    )
    return UltimoDividendo(
        data_com=ultima_data_com(rendimentos),
        valor=ultimo_valor(rendimentos),
        valor_anterior=anterior,
        tendencia=calcular_tendencia(rendimentos, banda),
    )


def _subtrair_meses(data: date, meses: int) -> date:
    """Subtrai um número de meses de uma data, ajustando o dia ao mês."""
    total = data.year * 12 + (data.month - 1) - meses
    ano, mes = divmod(total, 12)
    dia = min(data.day, monthrange(ano, mes + 1)[1])
    return date(ano, mes + 1, dia)


def dividendos_12m(
    proventos: list[Provento], reference_date: date
) -> Decimal:
    """Soma os rendimentos pagos nos 12 meses anteriores à data de referência.

    Considera ``data_pagamento`` em ``(reference_date − 12m, reference_date]``,
    conforme a convenção da RFC-007. Proventos sem data de pagamento são
    ignorados.
    """
    corte = _subtrair_meses(reference_date, JANELA_MESES_12M)
    total = Decimal(0)
    for provento in proventos:
        if provento.tipo != TIPO_RENDIMENTO:
            continue
        pagamento = provento.data_pagamento
        if pagamento is None:
            continue
        if corte < pagamento <= reference_date:
            total += provento.valor_por_unidade.value
    return total
