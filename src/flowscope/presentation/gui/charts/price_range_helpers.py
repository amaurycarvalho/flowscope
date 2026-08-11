"""Funções de renderização do painel de amplitude de preços do FlowScope.

Este módulo concentra a lógica de desenho do gráfico de amplitude de preços
e do medidor de CLV, mantendo o painel enxuto e as funções testáveis.
"""

from collections.abc import Callable

from matplotlib.axes import Axes


def normalize(close: float, min_p: float, max_p: float) -> float:
    """Normaliza um preço para a faixa entre a mínima e a máxima do dia.

    Quando a amplitude do dia é nula, retorna o ponto médio ``0.5`` para
    evitar divisão por zero durante o posicionamento dos marcadores.
    """
    rng = max_p - min_p
    if rng == 0:
        return 0.5
    return (close - min_p) / rng


def efficiency_color(eff: float) -> str:
    """Seleciona a cor da barra de eficiência conforme a faixa do indicador.

    Tons avermelhados representam eficiência baixa, âmbar eficiência média
    e tons esverdeados representam eficiência alta do pregão.
    """
    if eff <= 0.30:
        return "#CC6666"
    if eff <= 0.60:
        return "#CCAA44"
    return "#44AA66"


def as_dict(value: object) -> dict:
    """Preserva a semântica de ``all_inds.get(...) or {}`` para indicadores.

    Retorna um dicionário vazio quando o valor é nulo ou vazio, evitando que
    os chamadores precisem repetir a expressão com ``or {}``.
    """
    if not value:
        return {}
    return value


def size_mapper(range_pct_dict: dict) -> Callable[[float | None], float]:
    """Cria a função que converte a amplitude relativa no tamanho do marcador.

    A função resultante mapeia percentuais entre o 5º e o 95º percentil para
    um tamanho entre 40 e 200 pontos; valores fora da faixa são limitados.
    Quando não há percentuais, todos os marcadores usam o tamanho fixo 60.
    """
    pct_values = [float(v) for v in range_pct_dict.values() if v is not None]
    if not pct_values:
        return _constant_size

    sorted_pcts = sorted(pct_values)
    n_pcts = len(sorted_pcts)
    lo = sorted_pcts[max(0, int(n_pcts * 0.05))]
    hi = sorted_pcts[min(n_pcts - 1, int(n_pcts * 0.95))]
    if hi <= lo:
        hi = lo + 0.01

    def scale_size(value: float | None) -> float:
        if value is None:
            return 60
        clamped = max(lo, min(hi, float(value)))
        return 40 + (clamped - lo) / (hi - lo) * 160

    return scale_size


def _constant_size(value: float | None) -> float:
    return 60.0


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


def classify_session(daily: list[dict], range_pct_dict: dict,
                     eff_dict: dict) -> str | None:
    """Classifica o último pregão usando as séries de amplitude e eficiência.

    Retorna ``None`` quando faltam dados, quando não há percentuais de
    amplitude ou quando o último pregão não possui métricas completas.
    """
    if not daily or not range_pct_dict or not eff_dict:
        return None

    range_pct_values = [
        float(v) for v in range_pct_dict.values() if v is not None
    ]
    if not range_pct_values:
        return None

    last_date = daily[-1]["date"]
    current_rp = range_pct_dict.get(last_date)
    current_eff = eff_dict.get(last_date)
    if current_rp is None or current_eff is None:
        return None

    return classify_trend(float(current_rp), median_value(range_pct_values),
                          float(current_eff))


def _scatter_marker(ax: Axes, value: float, min_p: float, max_p: float,
                    i: int, letter: str, color: str, marker: str) -> None:
    """Desenha um marcador normalizado e a letra identificadora ao lado."""
    norm = normalize(float(value), min_p, max_p)
    ax.scatter(norm, i, marker=marker, color=color, s=50, zorder=5)
    ax.annotate(letter, (norm, i), xytext=(4, 4),
                textcoords="offset points", fontsize=8, color=color,
                fontweight="bold")


def render_last_day_markers(ax: Axes, d: dict, i: int,
                            typical_dict: dict, median_dict: dict,
                            weighted_dict: dict, range_pct_dict: dict,
                            marker_size: float,
                            hover_data: list[dict]) -> tuple[str, str]:
    """Desenha os marcadores do último pregão e coleta os dados de hover.

    Renderiza o preço de fechamento, as médias (M, T, V, W) e retorna os
    textos de mínima e máxima exibidos abaixo do eixo do gráfico.
    """
    dt = d["date"]
    min_p = float(d["min_price"])
    max_p = float(d["max_price"])
    close = float(d["last_price"])
    avg_p = float(d["avg_price"])

    today_min_text = f"Min: {min_p:.2f}"
    today_max_text = f"Max: {max_p:.2f}"

    norm_close = normalize(close, min_p, max_p)

    ax.scatter(norm_close, i, marker="o", color="blue", s=marker_size,
               zorder=5, label="Close")

    typical = typical_dict.get(dt)
    median = median_dict.get(dt)
    weighted = weighted_dict.get(dt)

    if median is not None:
        _scatter_marker(ax, median, min_p, max_p, i, "M", "orange", "s")

    if typical is not None:
        _scatter_marker(ax, typical, min_p, max_p, i, "T", "green", "^")

    _scatter_marker(ax, avg_p, min_p, max_p, i, "V", "purple", "D")

    if weighted is not None:
        _scatter_marker(ax, weighted, min_p, max_p, i, "W", "brown", "v")

    hover_data.append({
        "date": dt,
        "close": close,
        "typical": typical,
        "median": median,
        "vwap": avg_p,
        "weighted": weighted,
        "min_p": min_p,
        "max_p": max_p,
        "amplitude_relativa": range_pct_dict.get(dt),
    })

    return today_min_text, today_max_text


def _draw_background_row(ax: Axes, d: dict, i: int, eff_dict: dict,
                         map_size: Callable[[float | None], float],
                         range_pct_dict: dict) -> float:
    """Desenha a barra de eficiência e a linha de base de um dia."""
    dt = d["date"]
    eff = float(eff_dict.get(dt, 0) or 0)
    ax.barh(i, eff, height=0.9, left=0, color=efficiency_color(eff),
            alpha=0.3, zorder=1)
    ax.plot([0, 1], [i, i], color="#CCCCCC", linewidth=3, zorder=2)
    return map_size(range_pct_dict.get(dt))


def _draw_history_point(ax: Axes, d: dict, i: int,
                        map_size: Callable[[float | None], float],
                        range_pct_dict: dict,
                        hover_data: list[dict]) -> None:
    """Desenha o fechamento de um dia histórico e registra o hover."""
    dt = d["date"]
    min_p = float(d["min_price"])
    max_p = float(d["max_price"])
    close = float(d["last_price"])

    norm_close = normalize(close, min_p, max_p)
    marker_size = map_size(range_pct_dict.get(dt))

    ax.scatter(norm_close, i, marker="o", color="blue", s=marker_size,
               alpha=0.35, zorder=3)
    hover_data.append({
        "date": dt,
        "close": close,
        "min_p": min_p,
        "max_p": max_p,
        "amplitude_relativa": range_pct_dict.get(dt),
    })


def draw_connectors(ax: Axes, rev_daily: list[dict]) -> None:
    """Une os fechamentos de dias consecutivos com linhas suaves."""
    n = len(rev_daily)
    if n < 2:
        return
    for i in range(n - 1):
        curr = rev_daily[i]
        next_d = rev_daily[i + 1]

        x0 = normalize(float(curr["last_price"]), float(curr["min_price"]),
                       float(curr["max_price"]))
        x1 = normalize(float(next_d["last_price"]),
                       float(next_d["min_price"]),
                       float(next_d["max_price"]))

        ax.plot([x0, x1], [i, i + 1], color="gray", linewidth=1,
                alpha=0.3, zorder=4)


def draw_classification_text(ax: Axes, daily: list[dict],
                             range_pct_dict: dict,
                             eff_dict: dict) -> None:
    """Exibe a classificação do último pregão no canto superior do gráfico."""
    classification = classify_session(daily, range_pct_dict, eff_dict)
    if not classification:
        return
    ax.text(0.98, 0.98, classification, transform=ax.transAxes,
            ha="right", va="top", fontsize=10, fontweight="bold",
            bbox={"boxstyle": "round,pad=0.3", "fc": "lightyellow",
                  "ec": "gray", "alpha": 0.9},
            zorder=10)


def _configure_main_axes(ax: Axes, rev_daily: list[dict],
                         ticker: str | None) -> None:
    """Configura rótulos, limites e título do eixo principal."""
    n = len(rev_daily)
    ax.set_yticks(range(n))
    ax.set_yticklabels([str(d["date"]) for d in rev_daily], fontsize=8)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.5, n - 0.5)
    ax.set_xlabel("Faixa de Preço Normalizada (%)", fontsize=8)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=7)
    title = f"Amplitude de Preço — {ticker}" if ticker else "Amplitude de Preço"
    ax.set_title(title, fontsize=10)


def _draw_today_labels(ax: Axes, today_min_text: str,
                       today_max_text: str) -> None:
    """Desenha os textos de mínima e máxima abaixo do eixo principal."""
    ax.text(0, -0.08, today_min_text, transform=ax.get_xaxis_transform(),
            ha="center", va="top", fontsize=7, color="gray")
    ax.text(1, -0.08, today_max_text, transform=ax.get_xaxis_transform(),
            ha="center", va="top", fontsize=7, color="gray")


def draw_main_chart(ax: Axes, daily: list[dict], typical_dict: dict,
                    median_dict: dict, weighted_dict: dict,
                    range_pct_dict: dict, eff_dict: dict,
                    ticker: str | None,
                    hover_data: list[dict]) -> None:
    """Desenha o gráfico principal de amplitude de preços.

    Renderiza as barras de eficiência, os fechamentos diários, os marcadores
    do último pregão, as conexões entre dias e a classificação do movimento.
    """
    rev_daily = list(reversed(daily))
    map_size = size_mapper(range_pct_dict)

    today_min_text = ""
    today_max_text = ""

    for i, d in enumerate(rev_daily):
        _draw_background_row(ax, d, i, eff_dict, map_size, range_pct_dict)
        if i == 0:
            marker_size = map_size(range_pct_dict.get(d["date"]))
            today_min_text, today_max_text = render_last_day_markers(
                ax, d, i, typical_dict, median_dict, weighted_dict,
                range_pct_dict, marker_size, hover_data,
            )
        else:
            _draw_history_point(ax, d, i, map_size, range_pct_dict,
                                hover_data)

    draw_connectors(ax, rev_daily)
    draw_classification_text(ax, daily, range_pct_dict, eff_dict)
    _configure_main_axes(ax, rev_daily, ticker)
    _draw_today_labels(ax, today_min_text, today_max_text)


def draw_clv_gauge(ax: Axes, daily: list[dict], clv_dict: dict) -> None:
    """Desenha o medidor de CLV com barra colorida e eixos percentuais.

    A barra cresce para a direita em caso de CLV positivo e para a esquerda
    em caso de CLV negativo, com o valor centralizado no medidor.
    """
    last_date = daily[-1]["date"] if daily else None
    clv = float(clv_dict.get(last_date, 0) or 0) if last_date else 0

    ax.set_xlim(-1, 1)
    ax.set_ylim(0, 1)

    ax.barh(0.5, 2, height=0.35, color="#EEEEEE", zorder=1, left=-1)

    if clv > 0:
        ax.barh(0.5, clv, height=0.35, color="#44AA66", zorder=2, left=0)
    elif clv < 0:
        ax.barh(0.5, abs(clv), height=0.35, color="#CC4444",
                zorder=2, left=clv)

    ax.axvline(x=0, color="gray", linewidth=0.8, linestyle="-", zorder=3)

    clv_pct = clv * 100
    if clv != 0:
        clv_text = f"{clv:+.2f} ({clv_pct:+.0f}%)"
    else:
        clv_text = "0.00"
    ax.text(clv / 2 if clv != 0 else 0, 0.5, clv_text,
            ha="center", va="center", fontsize=9, fontweight="bold",
            color="white" if abs(clv) > 0.15 else "black")

    ax.set_title("CLV (data mais recente)", fontsize=9, loc="left")
    ax.set_yticks([])
    ax.set_xticks([-1, -0.5, 0, 0.5, 1])
    ax.set_xticklabels(["-100%", "-50%", "0%", "50%", "100%"], fontsize=7)

    ax.text(0.05, -0.20, "← Vendedores", transform=ax.transAxes,
            ha="left", va="top", fontsize=9, color="red", fontweight="bold")
    ax.text(0.95, -0.20, "Compradores →", transform=ax.transAxes,
            ha="right", va="top", fontsize=9, color="green", fontweight="bold")


def tooltip_lines(pt: dict) -> list[str]:
    """Monta as linhas do tooltip de hover de um ponto do gráfico.

    Inclui data, fechamento, mínima e máxima e as médias opcionais quando
    estiverem disponíveis no ponto inspecionado.
    """
    lines = [f"Data: {pt['date']}"]
    lines.append(f"Close: {pt['close']:.2f}")
    lines.append(f"Min: {pt['min_p']:.2f}  Max: {pt['max_p']:.2f}")
    if "typical" in pt and pt["typical"] is not None:
        lines.append(f"Typical: {float(pt['typical']):.2f}")
    if "median" in pt and pt["median"] is not None:
        lines.append(f"Median: {float(pt['median']):.2f}")
    if "vwap" in pt:
        lines.append(f"VWAP: {float(pt['vwap']):.2f}")
    if "weighted" in pt and pt["weighted"] is not None:
        lines.append(f"W. Close: {float(pt['weighted']):.2f}")
    if "amplitude_relativa" in pt and pt["amplitude_relativa"] is not None:
        lines.append(f"Amplitude: {float(pt['amplitude_relativa']):.2f}%")
    return lines
