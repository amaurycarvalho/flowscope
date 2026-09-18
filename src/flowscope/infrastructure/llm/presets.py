"""Presets de provedores de LLM e resolução de modelo e API URL.

Cada preset adota endpoints OpenAI-compatible, de modo que o adaptador envia
sempre ``custom_llm_provider="openai"``. O preset ``custom`` deixa modelo e API
URL em branco para preenchimento manual pelo usuário.
"""

from flowscope.domain.llm import LLMConfigurationError

#: Provedores suportados com seus defaults de modelo e API URL.
PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "none": {"model": "", "api_url": ""},
    "openai": {
        "model": "gpt-4o-mini",
        "api_url": "https://api.openai.com/v1",
    },
    "gemini": {
        "model": "gemini-3.1-flash-lite",
        "api_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    },
    "copilot": {
        "model": "gpt-4o",
        "api_url": "https://models.inference.ai.azure.com",
    },
    "claude": {
        "model": "claude-sonnet-4-20250514",
        "api_url": "https://api.anthropic.com/v1",
    },
    "deepseek": {
        "model": "deepseek-chat",
        "api_url": "https://api.deepseek.com/v1",
    },
    "ollama": {
        "model": "llama3.2",
        "api_url": "http://localhost:11434/v1",
    },
    "custom": {"model": "", "api_url": ""},
}


def resolve_provider(
    provider: str,
    model: str | None = None,
    api_url: str | None = None,
) -> tuple[str, str]:
    """Resolve o modelo e a API URL de um provedor, aplicando defaults do preset.

    Lança ``LLMConfigurationError`` para provedor desconhecido ou para o
    provedor ``custom`` sem modelo/API URL informados.
    """
    if provider not in PROVIDER_PRESETS:
        raise LLMConfigurationError(f"Provedor de LLM desconhecido: {provider}")
    preset = PROVIDER_PRESETS[provider]
    resolved_model = model or preset["model"]
    resolved_url = api_url or preset["api_url"]
    if not resolved_model or not resolved_url:
        raise LLMConfigurationError(
            f"Provedor {provider} requer model e api_url configurados"
        )
    return resolved_model, resolved_url
