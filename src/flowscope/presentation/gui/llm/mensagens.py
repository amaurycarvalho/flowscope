"""Tradução de erros da camada de LLM para mensagens exibíveis na interface.

A GUI depende apenas do domínio; este módulo mantém o texto amigável separado
da mensagem técnica do erro, que permanece intacta nos registros de log.
"""

from flowscope.domain.llm import (
    LLMCommunicationError,
    LLMConfigurationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
)

#: Mensagem genérica para falhas do provedor sem tradução específica.
MENSAGEM_PROVEDOR = (
    "O provedor de I.A. retornou um erro. Consulte o log para mais detalhes."
)

#: Mapeamento ordenado de erros de domínio para mensagens exibíveis.
_MENSAGENS: tuple[tuple[type[BaseException], str], ...] = (
    (
        LLMServiceUnavailableError,
        (
            "O serviço de I.A. está temporariamente indisponível (alta demanda). "
            "Tente novamente em instantes."
        ),
    ),
    (
        LLMRateLimitError,
        "Limite de uso da I.A. atingido. Aguarde um momento e tente novamente.",
    ),
    (
        LLMCommunicationError,
        (
            "Não foi possível conectar ao serviço de I.A. "
            "Verifique a conexão e a API URL."
        ),
    ),
    (
        LLMConfigurationError,
        "Configuração de I.A. inválida. Verifique o modelo e a API URL.",
    ),
    (LLMProviderError, MENSAGEM_PROVEDOR),
)


def mensagem_erro_llm(exc: BaseException) -> str:
    """Traduz uma exceção para uma mensagem curta exibível na interface.

    Erros sem tradução específica (``LLMUnavailableError`` e exceções fora da
    hierarquia de LLM) preservam ``str(exc)``, mantendo o texto técnico útil.
    """
    for tipo, mensagem in _MENSAGENS:
        if isinstance(exc, tipo):
            return mensagem
    return str(exc)
