"""Preparação das métricas do pregão do painel de fluxo financeiro.

Contém o view-model com as métricas do último pregão e a função pura que o
constroi a partir dos indicadores brutos; a formatação e o desenho permanecem
na apresentação.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SessionFlowMetrics:
    """Métricas do último pregão exibidas no painel de fluxo financeiro."""

    last_date: object
    clv: float
    dmf: float
    bp: float
    sp: float
    rp: float
    fin_vol: float
    fin_vol_millions: float
    accumulated_mfv: float | None


def _get_dict(mapping: dict, key: str) -> dict:
    """Devolve um dicionário vazio quando o valor mapeado é nulo."""
    return mapping.get(key) or {}


def _as_float(value: object) -> float:
    """Preserva a semântica de ``or 0`` ao converter um valor para float.

    Valores nulos, vazios ou zero produzem ``0.0``; os demais valores são
    convertidos com ``float()`` antes do retorno.
    """
    if not value:
        return 0.0
    return float(value)


def build_session_metrics(
    daily_sorted: list[dict], all_inds: dict, info: dict,
) -> SessionFlowMetrics:
    """Extrai as métricas do último pregão para renderização do painel.

    Retorna CLV, DMF, pressões de compra e venda, range percentual, volume
    financeiro e o MFV acumulado do ativo consultado.
    """
    last = daily_sorted[-1]
    last_date = last["date"]

    clv_dict = _get_dict(all_inds, "clv")
    dmf_dict = _get_dict(all_inds, "daily_money_flow")
    bp_dict = _get_dict(all_inds, "buying_pressure")
    sp_dict = _get_dict(all_inds, "selling_pressure")
    rp_dict = _get_dict(all_inds, "range_percentual")
    accumulated_mfv = info.get("money_flow_volume")

    fin_vol = _as_float(last.get("fin_vol"))

    return SessionFlowMetrics(
        last_date=last_date,
        clv=_as_float(clv_dict.get(last_date)),
        dmf=_as_float(dmf_dict.get(last_date)),
        bp=_as_float(bp_dict.get(last_date)),
        sp=_as_float(sp_dict.get(last_date)),
        rp=_as_float(rp_dict.get(last_date)),
        fin_vol=fin_vol,
        fin_vol_millions=fin_vol / 1_000_000,
        accumulated_mfv=(
            float(accumulated_mfv) if accumulated_mfv is not None else None
        ),
    )
