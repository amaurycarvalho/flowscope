"""Cálculo puro do retorno acumulado e do excesso versus um índice."""

import math
from collections.abc import Iterable, Mapping
from datetime import date, timedelta
from itertools import pairwise

from flowscope.application.calendar.ports import BusinessDayLookup
from flowscope.application.performance.modelos import (
    BASE_TOTAL,
    PerformanceTicker,
)
from flowscope.domain.fii.dividends import DividendoConsolidado

#: Fatores usuais de split, grupamento e bonificação.
_FATORES_SOCIETARIOS: tuple[float, ...] = (2.0, 3.0, 4.0, 5.0, 10.0, 20.0)

#: Tolerância relativa para considerar o salto compatível com um fator.
_TOLERANCIA_FATOR = 0.10

#: Movimento mínimo (em log) para acionar a heurística de evento.
_MOVIMENTO_MINIMO = math.log(1.4)


def alinhar_datas(
    serie_ticker: Mapping[date, float], serie_indice: Mapping[date, float]
) -> list[date]:
    """Retorna as datas comuns às duas séries, em ordem crescente."""
    return sorted(set(serie_ticker) & set(serie_indice))


def retorno_preco(serie: Mapping[date, float], datas: list[date]) -> float | None:
    """Calcula o retorno de preço entre a primeira e a última data alinhada."""
    if len(datas) < 2:
        return None
    inicial = serie[datas[0]]
    final = serie[datas[-1]]
    if inicial <= 0:
        return None
    return final / inicial - 1.0


def derivar_data_ex(
    data_com: date, business_day: BusinessDayLookup
) -> date:
    """Deriva a data ex como o próximo dia útil após a data-com."""
    candidato = data_com + timedelta(days=1)
    while not business_day.is_business_day(candidato):
        candidato += timedelta(days=1)
    return candidato


def proventos_por_data_ex(
    dividendos: Iterable[DividendoConsolidado],
    business_day: BusinessDayLookup,
) -> dict[date, float]:
    """Mapeia a data ex para a soma dos proventos, somando os do mesmo dia."""
    resultado: dict[date, float] = {}
    for dividendo in dividendos:
        if dividendo.data_base is None:
            continue
        data_ex = derivar_data_ex(dividendo.data_base, business_day)
        resultado[data_ex] = resultado.get(data_ex, 0.0) + float(dividendo.valor)
    return resultado


def retorno_total(
    serie: Mapping[date, float],
    datas: list[date],
    proventos: Mapping[date, float],
) -> float | None:
    """Acumula ``(P_t + D_t) / P_{t-1} - 1`` para o retorno total."""
    if len(datas) < 2:
        return None
    por_observacao = _proventos_nas_observacoes(datas, proventos)
    acumulado = 1.0
    anterior = serie[datas[0]]
    for momento in datas[1:]:
        if anterior <= 0:
            return None
        fator = (serie[momento] + por_observacao.get(momento, 0.0)) / anterior
        acumulado *= fator
        anterior = serie[momento]
    return acumulado - 1.0


def _proventos_nas_observacoes(
    datas: list[date], proventos: Mapping[date, float]
) -> dict[date, float]:
    """Atribui cada provento à primeira observação igual ou posterior à data ex."""
    resultado: dict[date, float] = {}
    for data_ex, valor in proventos.items():
        alvo = _primeira_observacao_em_ou_apos(datas, data_ex)
        if alvo is None:
            continue
        resultado[alvo] = resultado.get(alvo, 0.0) + valor
    return resultado


def _primeira_observacao_em_ou_apos(
    datas: list[date], alvo: date
) -> date | None:
    """Retorna a primeira data da lista igual ou posterior a ``alvo``."""
    for momento in datas:
        if momento >= alvo:
            return momento
    return None


def detectar_evento_societario(
    serie_ticker: Mapping[date, float],
    serie_indice: Mapping[date, float],
    datas: list[date],
) -> bool:
    """Sinaliza salto de preço compatível com split, grupamento ou bonificação."""
    for anterior, atual in pairwise(datas):
        salto = _salto_excesso(serie_ticker, serie_indice, anterior, atual)
        if salto is not None and _salto_suspeito(salto):
            return True
    return False


def _salto_excesso(
    serie_ticker: Mapping[date, float],
    serie_indice: Mapping[date, float],
    anterior: date,
    atual: date,
) -> float | None:
    """Calcula ``(P_t/P_{t-1}) / (I_t/I_{t-1})`` para um intervalo."""
    p_ant = serie_ticker[anterior]
    p_atual = serie_ticker[atual]
    i_ant = serie_indice[anterior]
    i_atual = serie_indice[atual]
    if p_ant <= 0 or i_ant <= 0:
        return None
    return (p_atual / p_ant) / (i_atual / i_ant)


def _salto_suspeito(salto: float) -> bool:
    """Verifica se o salto está próximo de um fator usual com desvio grande."""
    if salto <= 0 or abs(math.log(salto)) < _MOVIMENTO_MINIMO:
        return False
    for fator in _FATORES_SOCIETARIOS:
        for alvo in (fator, 1.0 / fator):
            if abs(salto - alvo) / alvo <= _TOLERANCIA_FATOR:
                return True
    return False


def montar_ticker(
    ticker: str,
    serie_ticker: Mapping[date, float],
    serie_indice: Mapping[date, float],
    proventos_ex: Mapping[date, float],
    base: str,
) -> PerformanceTicker | None:
    """Monta o resultado de um ticker para a base de retorno informada."""
    datas = alinhar_datas(serie_ticker, serie_indice)
    if len(datas) < 2:
        return None
    if base == BASE_TOTAL:
        retorno_ticker = retorno_total(serie_ticker, datas, proventos_ex)
    else:
        retorno_ticker = retorno_preco(serie_ticker, datas)
    retorno_indice = retorno_preco(serie_indice, datas)
    if retorno_ticker is None or retorno_indice is None:
        return None
    return PerformanceTicker(
        ticker=ticker,
        ticker_return=retorno_ticker,
        index_return=retorno_indice,
        excess_pp=(retorno_ticker - retorno_indice) * 100.0,
        observations=len(datas),
        suspicious_event=detectar_evento_societario(
            serie_ticker, serie_indice, datas
        ),
    )
