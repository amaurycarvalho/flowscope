"""Helpers de leitura de campos fundamentalistas e montagem de métricas."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flowscope.application.fundamental_ports import (
    CAMPO_DISCRIMINADOR,
    CAMPO_DIVIDEND_YIELD,
    CAMPO_ESPECIE,
    CAMPO_FFO_TREND,
    CAMPO_FFO_YIELD,
    CAMPO_GESTAO,
    CAMPO_P_FFO,
    CAMPO_P_L,
    CAMPO_P_VP,
    CAMPO_QTD_IMOVEIS,
    CAMPO_SEGMENTO,
    CAMPO_SETOR,
    CAMPO_SUBSETOR,
    CampoFundamental,
)
from flowscope.domain.fii import (
    TIPO_EXIBICAO_FII,
    ClassificacaoAtivo,
    ClassificacaoExibicao,
    FfoObservacao,
    Inconsistencia,
    MetricasFii,
    PatrimonioFii,
    PrecoObservacao,
    Quality,
    TendenciaDividendo,
    UltimoDividendo,
    classificar_exibicao,
    classificar_tendencia_ffo,
    p_l,
)


def _sem_dividendo() -> UltimoDividendo:
    """Retorna um resultado de dividendo vazio (N/A)."""
    return UltimoDividendo(
        data_com=None,
        valor=None,
        valor_anterior=None,
        tendencia=TendenciaDividendo.N_A,
    )


def _avisos_ffo_ausente(metricas: MetricasFii | None) -> tuple[str, ...]:
    """Retorna os avisos quando as métricas FFO esperadas não foram calculadas."""
    if metricas is None:
        return (Inconsistencia.FFO_NOT_AVAILABLE.value,)
    return ()


def _p_l_do_ativo(
    dados: dict[str, CampoFundamental],
    exibicao: ClassificacaoExibicao,
    cotacao: Decimal | None,
    ultimo_dividendo: UltimoDividendo,
) -> Decimal | None:
    """Resolve o P/L: reportado pela fonte ou derivado para FII.

    A derivação usa o tipo de exibição (discriminador da fonte) para cobrir
    todos os FIIs, não apenas os presentes na taxonomia determinística.
    """
    da_fonte = _decimal_campo(dados, CAMPO_P_L)
    if da_fonte is not None:
        return da_fonte
    if exibicao.tipo == TIPO_EXIBICAO_FII and cotacao is not None:
        return p_l(cotacao, ultimo_dividendo.valor)
    return None


def _fontes(
    ffo: FfoObservacao,
    patrimonio: PatrimonioFii,
    preco: PrecoObservacao,
) -> tuple[str, ...]:
    """Combina as fontes dos dados que alimentaram o snapshot."""
    return (ffo.fonte, patrimonio.fonte, preco.fonte)


def _texto(
    dados: dict[str, CampoFundamental], chave: str
) -> str | None:
    """Retorna o valor textual de um campo composto, ou ``None``."""
    campo = dados.get(chave)
    if campo is None or campo.valor is None:
        return None
    return str(campo.valor)


def _decimal_campo(
    dados: dict[str, CampoFundamental], chave: str
) -> Decimal | None:
    """Retorna o valor decimal de um campo composto, ou ``None``."""
    campo = dados.get(chave)
    if campo is None or campo.valor is None:
        return None
    if isinstance(campo.valor, Decimal):
        return campo.valor
    try:
        return Decimal(str(campo.valor))
    except (InvalidOperation, ValueError):
        return None


def _int_campo(
    dados: dict[str, CampoFundamental], chave: str
) -> int | None:
    """Retorna o valor inteiro de um campo composto, ou ``None``."""
    campo = dados.get(chave)
    if campo is None or campo.valor is None:
        return None
    try:
        return int(campo.valor)
    except (TypeError, ValueError):
        return None


def _data_campo(
    dados: dict[str, CampoFundamental], chave: str
) -> date | None:
    """Retorna o valor de data de um campo composto, ou ``None``."""
    campo = dados.get(chave)
    if campo is None:
        return None
    valor = campo.valor
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor)
        except ValueError:
            return None
    return None


def _classificacao_exibicao(
    dados: dict[str, CampoFundamental], fallback: ClassificacaoAtivo | None
) -> ClassificacaoExibicao:
    """Compõe Tipo/Sub-tipo a partir dos campos do Fundamentus, com fallback."""
    return classificar_exibicao(
        discriminador=_texto(dados, CAMPO_DISCRIMINADOR),
        especie=_texto(dados, CAMPO_ESPECIE),
        setor=_texto(dados, CAMPO_SETOR),
        subsetor=_texto(dados, CAMPO_SUBSETOR),
        segmento=_texto(dados, CAMPO_SEGMENTO),
        gestao=_texto(dados, CAMPO_GESTAO),
        qtd_imoveis=_int_campo(dados, CAMPO_QTD_IMOVEIS),
        fallback=fallback,
    )


def _metricas_dos_dados(
    dados: dict[str, CampoFundamental],
) -> MetricasFii | None:
    """Monta as métricas a partir dos campos reportados por uma fonte primária."""
    ffo_yield = _decimal_campo(dados, CAMPO_FFO_YIELD)
    dividend_yield = _decimal_campo(dados, CAMPO_DIVIDEND_YIELD)
    p_ffo = _decimal_campo(dados, CAMPO_P_FFO)
    p_vp = _decimal_campo(dados, CAMPO_P_VP)
    trend_change = _decimal_campo(dados, CAMPO_FFO_TREND)
    if all(
        valor is None
        for valor in (ffo_yield, dividend_yield, p_ffo, p_vp, trend_change)
    ):
        return None
    tendencia = (
        classificar_tendencia_ffo(trend_change)
        if trend_change is not None
        else None
    )
    qualidade = (
        Quality.COMPLETE
        if ffo_yield is not None and p_vp is not None
        else Quality.PARTIAL
    )
    return MetricasFii(
        market_value=None,
        ffo_yield=ffo_yield,
        dividend_yield=dividend_yield,
        p_ffo=p_ffo,
        p_vp=p_vp,
        ffo_momentum=trend_change,
        ffo_trend=tendencia,
        ffo_trend_change=trend_change,
        ffo_payout=None,
        quality=qualidade,
        warnings=(),
        evidence=(),
    )
