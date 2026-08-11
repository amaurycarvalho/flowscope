"""Funções de renderização do painel de fluxo financeiro do FlowScope.

Este módulo concentra a lógica de desenho do cartão de resumo, das barras
de CLV e de pressões, além da geração do resumo textual do painel.
"""

from matplotlib.axes import Axes
from matplotlib.patches import FancyBboxPatch

from flowscope.domain.strategies.classifiers import MoneyFlowClassification


def as_float(value: object) -> float:
    """Preserva a semântica de ``or 0`` ao converter um valor para float.

    Valores nulos, vazios ou zero produzem ``0.0``; os demais valores são
    convertidos com ``float()`` antes do retorno.
    """
    if not value:
        return 0.0
    return float(value)


def extract_session_metrics(daily_sorted: list[dict], all_inds: dict,
                            info: dict) -> dict:
    """Extrai as métricas do último pregão para renderização do painel.

    Retorna um dicionário com CLV, DMF, pressões de compra e venda, range
    percentual, volume financeiro e o MFV acumulado do ativo consultado.
    """
    last = daily_sorted[-1]
    last_date = last["date"]

    clv_dict = all_inds.get("clv") or {}
    dmf_dict = all_inds.get("daily_money_flow") or {}
    bp_dict = all_inds.get("buying_pressure") or {}
    sp_dict = all_inds.get("selling_pressure") or {}
    rp_dict = all_inds.get("range_percentual") or {}
    accumulated_mfv = info.get("money_flow_volume")

    clv = as_float(clv_dict.get(last_date))
    dmf = as_float(dmf_dict.get(last_date))
    bp = as_float(bp_dict.get(last_date))
    sp = as_float(sp_dict.get(last_date))
    rp = as_float(rp_dict.get(last_date))
    fin_vol = as_float(last.get("fin_vol"))

    return {
        "last_date": last_date,
        "clv": clv,
        "dmf": dmf,
        "bp": bp,
        "sp": sp,
        "rp": rp,
        "fin_vol": fin_vol,
        "fin_vol_millions": fin_vol / 1_000_000,
        "accumulated_mfv": accumulated_mfv,
    }


def format_accumulated_mfv(value: object) -> tuple[str, float]:
    """Formata o MFV acumulado em texto monetário e em milhões de reais.

    Quando não há MFV acumulado, retorna um texto vazio e o valor ``0.0``.
    """
    if value is None:
        return "", 0.0
    return f"R${float(value):+,.0f}", float(value) / 1_000_000


def format_dmf_value(dmf: float) -> tuple[float, str]:
    """Normaliza o DMF para exibição em milhões ou bilhões de reais.

    Valores com módulo maior ou igual a 1 bilhão usam a unidade "Bi";
    caso contrário, o valor é apresentado em milhões com a unidade "M".
    """
    unit = "M"
    dmf_display = abs(dmf) / 1_000_000
    if abs(dmf) >= 1e9:
        return abs(dmf) / 1e9, "Bi"
    return dmf_display, unit


def format_dmf_text(dmf: float, dmf_display: float, unit: str) -> str:
    """Formata o texto monetário do DMF com sinal e unidade de medida."""
    if dmf != 0:
        return f"R$ {dmf_display:+,.1f}{unit}"
    return "R$ 0,00"


def draw_card(ax: Axes, dmf: float, classification: MoneyFlowClassification,
              mfv_value: str, rp: float, ticker: str,
              fin_vol_millions: float, mfv_millions: float) -> None:
    """Desenha o cartão de resumo do fluxo financeiro no eixo superior.

    Inclui o título, o rótulo de classificação colorido e as métricas do
    último pregão: volume financeiro, DMF, MFV acumulado e amplitude.
    """
    ax.axis("off")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(0, 0.7)

    chart_title_y = 0.67
    ax.text(0, chart_title_y, f"Fluxo Financeiro — {ticker}",
            ha="center", va="center", fontsize=10, fontweight="bold",
            color="#333333")

    dmf_display, unit = format_dmf_value(dmf)
    dmf_value = format_dmf_text(dmf, dmf_display, unit)

    cls_label = classification.label
    cls_color = classification.color

    card_x0, card_x1 = -0.95, 0.95
    card_y0, card_y1 = 0.10, 0.55

    card = FancyBboxPatch(
        (card_x0, card_y0), card_x1 - card_x0, card_y1 - card_y0,
        boxstyle="round,pad=0.05", fc="#FAFAFA", ec=cls_color, lw=1.5,
        alpha=0.9, zorder=1,
    )
    ax.add_patch(card)

    cls_label_y = card_y1 - 0.04
    ax.text(0, cls_label_y, cls_label, ha="center", va="center", fontsize=10,
            fontweight="bold", color=cls_color)

    left_text_y = cls_label_y - 0.08
    left_text = "Último pregão:\nDMF:\nAcumulado\nAmplitude de preço:"
    ax.text(card_x0 + 0.08, left_text_y, left_text, ha="left", va="top",
            fontsize=8, color="#666666")

    right_text_y = left_text_y
    right_text = (
        f"R$ {fin_vol_millions:+,.1f}M\n"
        f"{dmf_value}\n"
        f"R$ {mfv_millions:+,.1f}M\n"
        f"{rp:.1f}%"
    )
    ax.text(card_x1 - 0.08, right_text_y, right_text, ha="right", va="top",
            fontsize=8, color="#444444")


def draw_clv_bar(ax: Axes, clv: float, dmf: float) -> None:
    """Desenha a barra de CLV posicionada conforme o sinal do DMF.

    Quando o DMF é positivo, a barra cresce para a direita em tons verdes;
    quando negativo, para a esquerda em tons vermelhos, com a marca do CLV.
    """
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(0.0, 1.0)

    bar_y = 0.5
    bar_height = 0.40

    if dmf > 0:
        ax.barh(bar_y, abs(clv), height=bar_height, color="#4CAF50",
                zorder=2, left=0, alpha=0.85)
        ax.barh(bar_y, 1, height=bar_height, color="#E8F5E9",
                zorder=1, left=0, alpha=0.3)
    elif dmf < 0:
        ax.barh(bar_y, abs(clv), height=bar_height, color="#EF5350",
                zorder=2, left=clv, alpha=0.85)
        ax.barh(bar_y, 1, height=bar_height, color="#FFEBEE",
                zorder=1, left=-1, alpha=0.3)
    else:
        ax.barh(bar_y, 1, height=bar_height, color="#F5F5F5",
                zorder=1, left=-1)

    ax.axvline(x=0, color="#9E9E9E", linewidth=1, linestyle="-", zorder=3)

    ax.plot(clv, bar_y, marker="v", color="#333333", markersize=9,
            zorder=5, clip_on=False)
    ax.plot(clv, bar_y, marker="v", color="white", markersize=5,
            zorder=6, clip_on=False)

    clv_annot_x = clv + 0.08 if clv >= 0 else clv - 0.08
    clv_ha = "left" if clv >= 0 else "right"
    ax.text(clv_annot_x, bar_y, f"CLV {clv:+.2f}", ha=clv_ha, va="center",
            fontsize=7, color="#555555", fontweight="bold",
            bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "#CCCCCC",
                  "alpha": 0.85})

    ax.text(-1.15, bar_y, "◄ Vendedor", ha="left", va="center", fontsize=7.5,
            color="#EF5350", fontweight="bold")
    ax.text(1.15, bar_y, "Comprador ►", ha="right", va="center", fontsize=7.5,
            color="#4CAF50", fontweight="bold")

    ax.set_yticks([])
    ax.set_xticks([-1, -0.5, 0, 0.5, 1])
    ax.set_xticklabels(["-100%", "-50%", "0%", "50%", "100%"], fontsize=7)
    ax.set_xlabel("CLV / Score Normalizado", fontsize=7, color="#666666")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)


def pressure_percentages(bp: float, sp: float) -> tuple[float, float]:
    """Calcula os percentuais de compra e venda sobre a pressão total.

    Quando não há pressão acumulada, retorna 50% para cada lado do range.
    """
    if bp + sp > 0:
        total = bp + sp
        return bp / total * 100, sp / total * 100
    return 50.0, 50.0


def draw_pressure_labels(ax: Axes, bp: float, sp: float, bp_pct: float,
                         sp_pct: float, bar_y: float) -> None:
    """Desenha os rótulos de compra e venda dentro ou ao lado da barra."""
    bp_label = f"Compra {bp_pct:.0f}%"
    sp_label = f"Venda {sp_pct:.0f}%"
    if bp > 0.1:
        ax.text(bp / 2, bar_y, bp_label, ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")
    else:
        ax.text(0.02, bar_y, bp_label, ha="left", va="center",
                fontsize=10, fontweight="bold", color="#4CAF50")
    if sp > 0.1:
        ax.text(bp + sp / 2, bar_y, sp_label, ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")
    else:
        ax.text(0.98, bar_y, sp_label, ha="right", va="center",
                fontsize=10, fontweight="bold", color="#EF5350")


def draw_bs_bar(ax: Axes, bp: float, sp: float) -> None:
    """Desenha a barra de pressões de compra e venda do último pregão.

    Inclui a barra empilhada colorida, as fórmulas de pressão e a legenda
    percentual de cada lado do range do pregão mais recente.
    """
    ax.clear()
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.1, 0.6)

    bp_pct, sp_pct = pressure_percentages(bp, sp)

    bar_y = 0.03
    bar_height = 0.24

    if bp > 0:
        ax.barh(bar_y, bp, height=bar_height, color="#4CAF50", zorder=2,
                left=0, alpha=0.85)
    if sp > 0:
        ax.barh(bar_y, sp, height=bar_height, color="#EF5350", zorder=2,
                left=bp, alpha=0.85)
    if bp == 0 and sp == 0:
        ax.barh(bar_y, 1, height=bar_height, color="#E0E0E0", zorder=1, left=0)

    draw_pressure_labels(ax, bp, sp, bp_pct, sp_pct, bar_y)

    ax.text(0, 0.32, "Pressão na amplitude de preço do pregão mais recente",
            ha="left", va="bottom", fontsize=8, fontweight="bold")

    bp_formula = f"BP = (Close \u2212 Min) / (Max \u2212 Min) = {bp:.2f}"
    sp_formula = f"SP = (Max \u2212 Close) / (Max \u2212 Min) = {sp:.2f}"
    ax.text(0, 0.24, bp_formula, ha="left", va="bottom", fontsize=5.5,
            color="#4CAF50")
    ax.text(1, 0.24, sp_formula, ha="right", va="bottom", fontsize=5.5,
            color="#EF5350")

    ax.set_yticks([])
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)


def flow_intensity_part(dmf: float,
                        classification: MoneyFlowClassification) -> str:
    """Gera o trecho do resumo que descreve a intensidade do fluxo.

    Usa o sinal do DMF e o score quantizado da classificação para escolher
    entre fluxo forte, moderado, leve ou neutro em cada direção.
    """
    if dmf > 0:
        if classification.score >= 3:
            return "O ativo fechou com forte fluxo financeiro comprador"
        if classification.score >= 1:
            return "O ativo fechou com fluxo comprador moderado"
        return "O ativo fechou com leve fluxo comprador"
    if dmf < 0:
        if classification.score <= -3:
            return "O ativo fechou com forte fluxo financeiro vendedor"
        if classification.score <= -1:
            return "O ativo fechou com fluxo vendedor moderado"
        return "O ativo fechou com leve fluxo vendedor"
    return "O fluxo financeiro foi neutro"


def close_position_part(clv: float) -> str:
    """Descreve a posição do fechamento em relação ao range do pregão."""
    if clv > 0.3:
        return " e o fechamento ocorreu próximo da máxima"
    if clv < -0.3:
        return " e o fechamento ocorreu próximo da mínima"
    return " e o fechamento ocorreu na região central do range"


def dominance_part(bp: float, sp: float) -> str:
    """Descreve a dominância de compradores ou vendedores no range."""
    if bp > 0.65:
        return ", com ampla dominância compradora no range."
    if sp > 0.65:
        return ", com ampla dominância vendedora no range."
    return ", com disputa equilibrada no range."


def conviction_part(score: int) -> str:
    """Classifica a convicção financeira conforme o score da classificação."""
    if abs(score) >= 3:
        return "elevada"
    if abs(score) >= 1:
        return "moderada"
    return "baixa"


def generate_summary(dmf: float, classification: MoneyFlowClassification,
                     clv: float, bp: float, sp: float) -> str:
    """Gera o resumo textual do fluxo financeiro do último pregão.

    Combina a intensidade do fluxo, a posição do fechamento, a dominância
    no range e a convicção financeira em uma única frase de análise.
    """
    parts = [
        flow_intensity_part(dmf, classification),
        close_position_part(clv),
        dominance_part(bp, sp),
    ]
    conviction = conviction_part(classification.score)
    parts.append(f" Convicção financeira {conviction}.")

    return "".join(parts)


def tooltip_lines(pt: dict) -> list[str]:
    """Monta as linhas do tooltip de hover do cartão de fluxo financeiro.

    Inclui data, DMF, MFV acumulado, CLV, score, classificação, volume
    financeiro e range percentual do último pregão consultado.
    """
    lines = [f"Data: {pt['date']}"]
    lines.append(f"DMF (Daily Money Flow): R${pt['dmf']:+,.2f}")
    if pt["mfv_acum"] is not None:
        lines.append(f"MFV Acumulado: R${pt['mfv_acum']:+,.2f}")
    lines.append(f"CLV: {pt['clv']:+.4f}")
    lines.append(f"Score: {pt['score']:+.4f}")
    lines.append(f"Classificação: {pt['classification']}")
    lines.append(f"Vol. Financeiro: R${pt['fin_vol']:+,.2f}")
    lines.append(f"Range: {pt['range_pct']:.2f}%")
    return lines
