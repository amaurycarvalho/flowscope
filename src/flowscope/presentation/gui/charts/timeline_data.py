"""Preparação dos dados do gráfico de evolução da dominância.

Contém as funções puras de construção das linhas da linha do tempo e
do cálculo do balanço entre dias compradores e vendedores de um ativo.
"""


def _get_dict(mapping: dict, key: str) -> dict:
    """Devolve um dicionário vazio quando o valor mapeado é nulo."""
    return mapping.get(key) or {}


def _to_float(value: object) -> float:
    """Devolve o valor em float, tratando valores nulos como zero."""
    return float(value or 0)


def build_rows(info: dict) -> list[dict]:
    """Constroi as linhas da linha do tempo a partir dos indicadores.

    As linhas são geradas em ordem cronológica decrescente, sempre que
    houver um CLV válido para a data analisada.
    """
    all_inds = info.get("all_indicators", {})
    clv_dict = _get_dict(all_inds, "clv")
    eff_dict = _get_dict(all_inds, "daily_efficiency")
    dmf_dict = _get_dict(all_inds, "daily_money_flow")

    common_dates = sorted(d for d in clv_dict if clv_dict[d] is not None)
    rows: list[dict] = []
    for dt in reversed(common_dates):
        rows.append({
            "date": dt,
            "clv": float(clv_dict[dt]),
            "efficiency": _to_float(eff_dict.get(dt)),
            "daily_mfv": _to_float(dmf_dict.get(dt)),
        })
    return rows


def direction_balance(rows: list[dict]) -> tuple[int, int]:
    """Conta os dias com dominância compradora e vendedora.

    Returns:
        Tupla com a quantidade de dias compradores e vendedores,
        desconsiderando os dias sem direção definida (CLV nulo).
    """
    buyer_days = sum(1 for r in rows if r["clv"] > 0)
    seller_days = sum(1 for r in rows if r["clv"] < 0)
    return buyer_days, seller_days
