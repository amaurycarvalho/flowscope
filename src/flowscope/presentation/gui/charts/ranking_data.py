"""Preparação dos dados do gráfico de ranking de dominância.

Contém as funções puras de construção das linhas do ranking, dos
comprimentos das hastes de volume e do posicionamento dos rótulos
dos tickers ao lado de cada barra.
"""

from flowscope.presentation.gui.charts.dominance_data import stem_length


def build_rows(data: dict) -> list[dict]:
    """Extrai as linhas do ranking a partir dos dados brutos do pregão.

    Cada linha guarda o último CLV e o fluxo monetário de cada ativo,
    ignorando ativos sem indicadores de CLV disponíveis.
    """
    rows: list[dict] = []
    for ticker, info in data.items():
        clv_dict = info.get("all_indicators", {}).get("clv")
        if not clv_dict:
            continue
        last_date = max(clv_dict.keys())
        clv = clv_dict[last_date]
        if clv is None:
            continue
        mfv = info.get("money_flow_volume")
        rows.append({
            "ticker": ticker,
            "clv": float(clv),
            "mfv": float(mfv) if mfv is not None else 0.0,
            "date": last_date,
        })
    return rows


def stem_lengths(
    mfvs: list[float],
    max_val: float,
    scale: float = 0.10,
) -> list[float]:
    """Calcula o comprimento da haste de volume de cada linha do ranking."""
    return [stem_length(mfv, max_val, scale) for mfv in mfvs]


def draw_ticker_labels(
    axes: object,
    tickers: list[str],
    clvs: list[float],
    stem_lens: list[float],
    y_pos: list[int],
) -> None:
    """Desenha os rótulos dos tickers ao lado de cada barra do ranking.

    O rótulo é posicionado na extremidade livre da haste e limitado
    aos extremos do eixo para não ultrapassar a área útil do gráfico.
    """
    for i, (ticker, clv) in enumerate(zip(tickers, clvs)):
        stem_len = stem_lens[i]
        if clv >= 0:
            label_x = clv + stem_len + 0.02
            ha = "left"
        else:
            label_x = clv - stem_len - 0.02
            ha = "right"
        if label_x > 1.18:
            label_x = 1.18
            ha = "right"
        elif label_x < -1.18:
            label_x = -1.18
            ha = "left"
        axes.text(
            label_x, y_pos[i], ticker,
            ha=ha, va="center", fontsize=8, zorder=4,
        )
