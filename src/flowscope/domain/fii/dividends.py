"""Métricas de dividendo por ticker, limitadas a proventos de Rendimento.

Os dividendos são consolidados a partir de B3 (primário), CVM (secundário) e
Fundamentus (fallback), preservando a origem de cada valor. A tendência compara
o último dividendo com o imediatamente anterior por comparação direta
(``Crescimento``/``Redução``/``Neutro``), sem banda de tolerância.
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from flowscope.domain.structured import Provento

#: Tipo de provento considerado como dividendo.
TIPO_RENDIMENTO = "Rendimento"

#: Meses do período de acumulação do Dividend Yield de 12 meses.
JANELA_MESES_12M = 12


class TendenciaDividendo(Enum):
    """Tendência do último dividendo em relação ao anterior."""

    CRESCIMENTO = "Crescimento"
    REDUCAO = "Redução"
    NEUTRO = "Neutro"
    N_A = "N/A"


@dataclass(frozen=True)
class DividendoConsolidado:
    """Dividendo normalizado com a fonte que o forneceu."""

    data_base: date | None
    valor: Decimal
    fonte: str


@dataclass(frozen=True)
class UltimoDividendo:
    """Último dividendo de um ticker com a respectiva tendência."""

    data_com: date | None
    valor: Decimal | None
    valor_anterior: Decimal | None
    tendencia: TendenciaDividendo


def dividendos_de_proventos(
    proventos: list[Provento], fonte: str = "B3"
) -> list[DividendoConsolidado]:
    """Dividendos consolidados a partir de proventos de ``Rendimento``.

    Proventos de ``Amortização`` e sem data-base são ignorados.
    """
    dividendos: list[DividendoConsolidado] = []
    for provento in proventos:
        if provento.tipo != TIPO_RENDIMENTO or provento.data_base is None:
            continue
        dividendos.append(
            DividendoConsolidado(
                data_base=provento.data_base,
                valor=provento.valor_por_unidade.value,
                fonte=fonte,
            )
        )
    return dividendos


def consolidar_dividendos(
    *fontes: list[DividendoConsolidado],
) -> list[DividendoConsolidado]:
    """Consolida dividendos de várias fontes, preservando a origem.

    As fontes são aplicadas em ordem de prioridade e duplicatas por
    ``(data_base, valor)`` mantêm a primeira ocorrência. O resultado é ordenado
    por ``data_base`` crescente.
    """
    vistos: set[tuple[date | None, Decimal]] = set()
    resultado: list[DividendoConsolidado] = []
    for fonte in fontes:
        for dividendo in fonte:
            chave = (dividendo.data_base, dividendo.valor)
            if chave in vistos:
                continue
            vistos.add(chave)
            resultado.append(dividendo)
    resultado.sort(key=lambda dividendo: dividendo.data_base or date.min)
    return resultado


def calcular_tendencia(
    dividendos: list[DividendoConsolidado],
) -> TendenciaDividendo:
    """Classifica a tendência comparando o último dividendo com o anterior.

    ``CRESCIMENTO`` quando o último é maior, ``REDUCAO`` quando é menor e
    ``NEUTRO`` quando é igual. Sem dividendo anterior a tendência é ``N/A``.
    """
    if len(dividendos) < 2:
        return TendenciaDividendo.N_A
    ultimo = dividendos[-1].valor
    anterior = dividendos[-2].valor
    if ultimo > anterior:
        return TendenciaDividendo.CRESCIMENTO
    if ultimo < anterior:
        return TendenciaDividendo.REDUCAO
    return TendenciaDividendo.NEUTRO


def calcular_ultimo_dividendo_consolidado(
    dividendos: list[DividendoConsolidado],
    reference_date: date | None = None,
) -> UltimoDividendo:
    """Calcula a última data-com, o último dividendo e sua tendência."""
    validos = [
        dividendo
        for dividendo in dividendos
        if dividendo.data_base is None
        or reference_date is None
        or dividendo.data_base <= reference_date
    ]
    validos.sort(key=lambda dividendo: dividendo.data_base or date.min)
    if not validos:
        return UltimoDividendo(
            data_com=None,
            valor=None,
            valor_anterior=None,
            tendencia=TendenciaDividendo.N_A,
        )
    anterior = validos[-2].valor if len(validos) > 1 else None
    return UltimoDividendo(
        data_com=validos[-1].data_base,
        valor=validos[-1].valor,
        valor_anterior=anterior,
        tendencia=calcular_tendencia(validos),
    )


def calcular_ultimo_dividendo(
    proventos: list[Provento],
    reference_date: date | None = None,
) -> UltimoDividendo:
    """Calcula a última data-com, o último dividendo e sua tendência (B3)."""
    return calcular_ultimo_dividendo_consolidado(
        dividendos_de_proventos(proventos), reference_date
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
