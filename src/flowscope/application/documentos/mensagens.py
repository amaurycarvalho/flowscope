"""Mensagens de indisponibilidade de resumo dos documentos.

A mensagem depende de a LLM estar configurada e é reutilizada tanto pelo
serviço de resumo quanto pela renderização dos agrupamentos.
"""

#: Prefixo da mensagem exibida quando não há resumo disponível.
RESUMO_INDISPONIVEL = "Resumo indisponível."

#: Sufixo da mensagem de indisponibilidade com a LLM configurada.
SUFIXO_LLM_CONFIGURADA = " Clique no documento para análise."

#: Sufixo da mensagem de indisponibilidade sem a LLM configurada.
SUFIXO_LLM_AUSENTE = " Configure a LLM via o botão I.A. e teste a comunicação."


def mensagem_indisponivel(llm_configurada: bool) -> str:
    """Monta a mensagem de resumo indisponível conforme a LLM esteja pronta."""
    sufixo = SUFIXO_LLM_CONFIGURADA if llm_configurada else SUFIXO_LLM_AUSENTE
    return RESUMO_INDISPONIVEL + sufixo
