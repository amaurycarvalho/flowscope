"""Adaptador da porta ``LLMPort`` sobre o ``litellm.completion``.

Traduz as exceções nativas do liteLLM para a hierarquia de domínio, de modo
que os consumidores não dependam da biblioteca opcional. Todas as chamadas
passam pelo rate limiter configurado.
"""

from flowscope.domain.llm import (
    LLMCommunicationError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMUnavailableError,
)
from flowscope.infrastructure.llm.rate_limiter import DEFAULT_RPM, RateLimiter

#: Mensagem exibida quando a dependência opcional não está instalada.
MENSAGEM_DEPS_AUSENTES = (
    "Dependências de LLM ausentes. "
    "Instale com pip install flowscope[llm]."
)

#: Mapeamento ordenado de exceções do liteLLM para a hierarquia de domínio.
_MAPEAMENTO_EXCECOES: tuple[tuple[str, type[LLMError]], ...] = (
    ("Timeout", LLMCommunicationError),
    ("APIConnectionError", LLMCommunicationError),
    ("RateLimitError", LLMRateLimitError),
    ("AuthenticationError", LLMProviderError),
    ("BadRequestError", LLMProviderError),
    ("APIError", LLMProviderError),
)


def _import_litellm() -> object:
    """Importa o liteLLM, convertendo a ausência em ``LLMUnavailableError``."""
    try:
        import litellm
    except ImportError as exc:
        raise LLMUnavailableError(MENSAGEM_DEPS_AUSENTES) from exc
    return litellm


def _mapear_excecao(litellm: object, exc: Exception) -> LLMError:
    """Traduz uma exceção do liteLLM para o erro de domínio correspondente."""
    for nome, destino in _MAPEAMENTO_EXCECOES:
        classe = getattr(litellm, nome, None)
        if classe is not None and isinstance(exc, classe):
            return destino(str(exc))
    return LLMProviderError(str(exc))


class LiteLLMChatAdapter:
    """Adaptador de completion sobre ``litellm.completion``."""

    def __init__(
        self: "LiteLLMChatAdapter",
        *,
        model: str,
        api_key: str = "",
        api_url: str = "",
        rpm: int = DEFAULT_RPM,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """Guarda os parâmetros de chamada e configura o rate limiter."""
        self._model = model
        self._api_key = api_key
        self._api_url = api_url
        self._limiter = rate_limiter or RateLimiter(rpm)

    def complete(
        self: "LiteLLMChatAdapter",
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        """Envia as mensagens ao provedor e retorna a resposta como string."""
        payload = list(messages)
        if system_prompt is not None:
            payload = [
                {"role": "system", "content": system_prompt},
                *payload,
            ]
        self._limiter.acquire()
        litellm = _import_litellm()
        kwargs: dict[str, object] = {
            "model": self._model,
            "messages": payload,
            "api_key": self._api_key,
        }
        if self._api_url:
            kwargs["api_base"] = self._api_url
            kwargs["custom_llm_provider"] = "openai"
        try:
            resposta = litellm.completion(**kwargs)
        except Exception as exc:
            raise _mapear_excecao(litellm, exc) from exc
        return resposta.choices[0].message.content
