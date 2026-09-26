"""Classificação de pregão a partir da amplitude relativa e da eficiência.

Combina a amplitude relativa (abaixo ou acima da mediana das amplitudes) com a
eficiência diária para nomear o movimento do último pregão. É uma regra de
domínio consumida pela apresentação, que apenas fornece as séries já extraídas.
"""


def median_value(values: list[float]) -> float:
    """Calcula a mediana de uma lista de valores já ordenáveis.

    Para uma quantidade par de elementos, retorna a média dos dois valores
    centrais; caso contrário, retorna o elemento central da lista.
    """
    sorted_vals = sorted(values)
    n_vals = len(sorted_vals)
    if n_vals % 2 == 0:
        return (sorted_vals[n_vals // 2 - 1] + sorted_vals[n_vals // 2]) / 2
    return sorted_vals[n_vals // 2]


def classify_trend(current_rp: float, median_rp: float, current_eff: float) -> str:
    """Classifica o pregão atual a partir da amplitude e da eficiência.

    Combina a amplitude relativa (abaixo ou acima da mediana) com a eficiência
    diária para nomear o movimento: lateral, volátil, consistente ou direcional.
    """
    if current_rp <= median_rp and current_eff <= 0.30:
        return "Pregão Lateral"
    if current_rp > median_rp and current_eff <= 0.30:
        return "Volatilidade sem Direção"
    if current_rp <= median_rp and current_eff > 0.30:
        return "Movimento Consistente"
    return "Movimento Direcional Forte"


def classify_session(last_date: object, range_pct_dict: dict,
                     eff_dict: dict) -> str | None:
    """Classifica o último pregão usando as séries de amplitude e eficiência.

    Recebe a data do último pregão e os mapas de amplitude relativa e de
    eficiência diária. Retorna ``None`` quando faltam dados, quando não há
    percentuais de amplitude ou quando o último pregão não possui métricas
    completas.
    """
    if last_date is None or not range_pct_dict or not eff_dict:
        return None

    range_pct_values = [
        float(v) for v in range_pct_dict.values() if v is not None
    ]
    if not range_pct_values:
        return None

    current_rp = range_pct_dict.get(last_date)
    current_eff = eff_dict.get(last_date)
    if current_rp is None or current_eff is None:
        return None

    return classify_trend(float(current_rp), median_value(range_pct_values),
                          float(current_eff))
