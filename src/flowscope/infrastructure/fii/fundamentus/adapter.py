"""Adaptador do provider do Fundamentus para a porta ``FundamentalDataProvider``.

Converte o ``AtivoFundamental`` normalizado nos campos fundamentalistas
consumidos pela análise, registrando o Fundamentus como origem de cada valor.
"""

from datetime import date
from decimal import Decimal

from flowscope.application.fundamental_ports import (
    CAMPO_COTACAO,
    CAMPO_DATA_REFERENCIA,
    CAMPO_DISCRIMINADOR,
    CAMPO_DIVIDEND_YIELD,
    CAMPO_DIVIDENDO_POR_COTA,
    CAMPO_ESPECIE,
    CAMPO_FFO_3M,
    CAMPO_FFO_12M,
    CAMPO_FFO_TREND,
    CAMPO_FFO_YIELD,
    CAMPO_GESTAO,
    CAMPO_NOME,
    CAMPO_P_FFO,
    CAMPO_P_VP,
    CAMPO_PATRIMONIO,
    CAMPO_QTD_IMOVEIS,
    CAMPO_SEGMENTO,
    CAMPO_SETOR,
    CAMPO_SUBSETOR,
    CAMPO_VP_COTA,
    CampoFundamental,
    OrigemDados,
)
from flowscope.domain.fii.fundamentus import AtivoFundamental
from flowscope.infrastructure.conditional_cache import CacheOutcome

from .provider import FONTE_FUNDAMENTUS, FundamentusProvider

_INDICADOR_DIV_YIELD = "Div. Yield"
_INDICADOR_FFO_YIELD = "FFO Yield"
_INDICADOR_FFO_COTA = "FFO/Cota"
_INDICADOR_DIVIDENDO_COTA = "Dividendo/cota"
_INDICADOR_P_VP = "P/VP"
_INDICADOR_VP_COTA = "VP/Cota"
_DEMONSTRATIVO_FFO = "FFO"
_BALANCO_PATRIMONIO_LIQ = "Patrim. Líq"
_BALANCO_PATRIMONIO_LIQUIDO = "Patrim Líquido"
_IMOVEL_QTD = "qtd_imoveis"
_CEM = Decimal(100)
_QUATRO = Decimal(4)


class FundamentusFundamentalDataProvider:
    """Implementa ``FundamentalDataProvider`` sobre o provider do Fundamentus."""

    def __init__(
        self: "FundamentusFundamentalDataProvider",
        provider: FundamentusProvider | None = None,
    ) -> None:
        """Inicializa o adaptador com o provider do Fundamentus."""
        self._provider = provider or FundamentusProvider()

    def obter(
        self: "FundamentusFundamentalDataProvider",
        ticker: str,
        reference_date: date,
    ) -> dict[str, CampoFundamental]:
        """Obtém os campos normalizados do ticker no Fundamentus."""
        campos, _ = self.obter_com_resultado(ticker, reference_date)
        return campos

    def obter_com_resultado(
        self: "FundamentusFundamentalDataProvider",
        ticker: str,
        reference_date: date,
    ) -> tuple[dict[str, CampoFundamental], OrigemDados]:
        """Obtém os campos e a origem (cache ou rede) do snapshot."""
        get_with_outcome = getattr(self._provider, "get_with_outcome", None)
        if callable(get_with_outcome):
            ativo, outcome = get_with_outcome(ticker)
            origem = (
                OrigemDados.CACHE
                if outcome in (CacheOutcome.HIT, CacheOutcome.REVALIDATED)
                else OrigemDados.REDE
            )
            return campos_do_ativo(ativo), origem
        ativo = self._provider.get(ticker)
        return campos_do_ativo(ativo), OrigemDados.REDE


def campos_do_ativo(ativo: AtivoFundamental) -> dict[str, CampoFundamental]:
    """Mapeia um ``AtivoFundamental`` para os campos da análise."""
    campos: dict[str, CampoFundamental] = {}
    if ativo.nome:
        campos[CAMPO_NOME] = CampoFundamental(ativo.nome, FONTE_FUNDAMENTUS)
    if ativo.cotacao is not None:
        campos[CAMPO_COTACAO] = CampoFundamental(ativo.cotacao, FONTE_FUNDAMENTUS)

    campos.update(_campos_classificacao(ativo))

    indicadores = ativo.indicadores
    dividend_yield = _percentual(indicadores.get(_INDICADOR_DIV_YIELD))
    if dividend_yield is not None:
        campos[CAMPO_DIVIDEND_YIELD] = CampoFundamental(
            dividend_yield, FONTE_FUNDAMENTUS
        )
    ffo_yield = _percentual(indicadores.get(_INDICADOR_FFO_YIELD))
    if ffo_yield is not None:
        campos[CAMPO_FFO_YIELD] = CampoFundamental(ffo_yield, FONTE_FUNDAMENTUS)
    p_vp = indicadores.get(_INDICADOR_P_VP)
    if p_vp is not None:
        campos[CAMPO_P_VP] = CampoFundamental(p_vp, FONTE_FUNDAMENTUS)
    vp_cota = indicadores.get(_INDICADOR_VP_COTA)
    if vp_cota is not None:
        campos[CAMPO_VP_COTA] = CampoFundamental(vp_cota, FONTE_FUNDAMENTUS)
    dividendo_cota = indicadores.get(_INDICADOR_DIVIDENDO_COTA)
    if dividendo_cota is not None:
        campos[CAMPO_DIVIDENDO_POR_COTA] = CampoFundamental(
            dividendo_cota, FONTE_FUNDAMENTUS
        )
    p_ffo = _p_ffo(ativo, indicadores, ffo_yield)
    if p_ffo is not None:
        campos[CAMPO_P_FFO] = CampoFundamental(p_ffo, FONTE_FUNDAMENTUS)

    ffo_12m = ativo.demonstrativos_12m.get(_DEMONSTRATIVO_FFO)
    ffo_3m = ativo.demonstrativos_3m.get(_DEMONSTRATIVO_FFO)
    if ffo_12m is not None:
        campos[CAMPO_FFO_12M] = CampoFundamental(ffo_12m, FONTE_FUNDAMENTUS)
    if ffo_3m is not None:
        campos[CAMPO_FFO_3M] = CampoFundamental(ffo_3m, FONTE_FUNDAMENTUS)
    trend = _ffo_trend(ffo_12m, ffo_3m)
    if trend is not None:
        campos[CAMPO_FFO_TREND] = CampoFundamental(trend, FONTE_FUNDAMENTUS)
    _adicionar_patrimonio(ativo, campos)
    qtd_imoveis = ativo.imoveis.get(_IMOVEL_QTD)
    if qtd_imoveis is not None:
        campos[CAMPO_QTD_IMOVEIS] = CampoFundamental(qtd_imoveis, FONTE_FUNDAMENTUS)
    if ativo.data_ultima_cotacao is not None:
        campos[CAMPO_DATA_REFERENCIA] = CampoFundamental(
            ativo.data_ultima_cotacao, FONTE_FUNDAMENTUS
        )
    return campos


def _campos_classificacao(
    ativo: AtivoFundamental,
) -> dict[str, CampoFundamental]:
    """Mapeia discriminador e rótulos de classificação do ativo."""
    campos: dict[str, CampoFundamental] = {}
    if ativo.discriminador:
        campos[CAMPO_DISCRIMINADOR] = CampoFundamental(
            ativo.discriminador, FONTE_FUNDAMENTUS
        )
    for chave, valor in (
        (CAMPO_ESPECIE, ativo.especie),
        (CAMPO_SETOR, ativo.setor),
        (CAMPO_SUBSETOR, ativo.subsetor),
        (CAMPO_SEGMENTO, ativo.segmento),
        (CAMPO_GESTAO, ativo.gestao),
    ):
        if valor:
            campos[chave] = CampoFundamental(valor, FONTE_FUNDAMENTUS)
    return campos


def _adicionar_patrimonio(
    ativo: AtivoFundamental, campos: dict[str, CampoFundamental]
) -> None:
    """Adiciona o patrimônio líquido reportado no balanço, quando presente."""
    patrimonio = ativo.balanco.get(_BALANCO_PATRIMONIO_LIQ)
    if patrimonio is None:
        patrimonio = ativo.balanco.get(_BALANCO_PATRIMONIO_LIQUIDO)
    if patrimonio is not None:
        campos[CAMPO_PATRIMONIO] = CampoFundamental(patrimonio, FONTE_FUNDAMENTUS)


def _percentual(valor: Decimal | None) -> Decimal | None:
    """Retorna um percentual reportado (ex.: ``10,26``) convertido em fração."""
    if valor is None:
        return None
    return valor / _CEM


def _p_ffo(
    ativo: AtivoFundamental,
    indicadores: dict[str, Decimal],
    ffo_yield: Decimal | None,
) -> Decimal | None:
    """Calcula o P/FFO a partir do FFO Yield ou de FFO/Cota e cotação."""
    if ffo_yield is not None and ffo_yield > 0:
        return Decimal(1) / ffo_yield
    ffo_cota = indicadores.get(_INDICADOR_FFO_COTA)
    if ffo_cota is not None and ffo_cota > 0 and ativo.cotacao is not None:
        return ativo.cotacao / ffo_cota
    return None


def _ffo_trend(ffo_12m: Decimal | None, ffo_3m: Decimal | None) -> Decimal | None:
    """Calcula o momentum do FFO como ``(FFO_3m × 4) / FFO_12m − 1``."""
    if ffo_12m is None or ffo_3m is None or ffo_12m <= 0:
        return None
    return (ffo_3m * _QUATRO) / ffo_12m - Decimal(1)
