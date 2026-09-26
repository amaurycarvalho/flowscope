"""Resumo textual do fluxo financeiro do último pregão.

Contém as funções puras que interpretam as métricas do pregão (intensidade do
fluxo, posição do fechamento, dominância no range e convicção) e compõem a
frase de análise exibida no painel.
"""

from flowscope.domain.strategies.classifiers import MoneyFlowClassification


def flow_intensity_part(
    dmf: float, classification: MoneyFlowClassification,
) -> str:
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
