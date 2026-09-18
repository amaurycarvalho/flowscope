"""Factory que instancia um provedor de LLM a partir da configuração.

Concentra as validações de configuração e de dependências, devolvendo sempre
a porta de domínio ``LLMPort`` (nunca o adaptador concreto).
"""

from flowscope.domain.llm import (
    LLMPort,
    LLMUnavailableError,
)
from flowscope.infrastructure.llm.adapter import (
    MENSAGEM_DEPS_AUSENTES,
    LiteLLMChatAdapter,
)
from flowscope.infrastructure.llm.config import (
    DEFAULT_LLM_CONFIG,
    check_llm_deps,
)
from flowscope.infrastructure.llm.presets import resolve_provider


def create_llm_provider(config: dict) -> LLMPort:
    """Cria um ``LLMPort`` pronto para uso a partir do bloco ``llm.chat``.

    Lança ``LLMUnavailableError`` para o provedor ``none`` ou dependências
    ausentes, e ``LLMConfigurationError`` (via ``resolve_provider``) para
    provedor desconhecido ou ``custom`` incompleto.
    """
    provider = config.get("provider") or "none"
    if provider == "none":
        raise LLMUnavailableError("Nenhum provedor de LLM configurado.")
    model, api_url = resolve_provider(
        provider, config.get("model"), config.get("api_url")
    )
    if not check_llm_deps():
        raise LLMUnavailableError(MENSAGEM_DEPS_AUSENTES)
    return LiteLLMChatAdapter(
        model=model,
        api_url=api_url,
        api_key=config.get("api_key") or "",
        rpm=config.get("rpm") or DEFAULT_LLM_CONFIG["rpm"],
    )
