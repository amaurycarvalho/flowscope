"""Adaptador da porta ``LLMPort`` sobre o ``litellm.completion``.

Traduz as exceções nativas do liteLLM para a hierarquia de domínio, de modo
que os consumidores não dependam da biblioteca opcional. Todas as chamadas
passam pelo rate limiter configurado.
"""

import random
import time
from collections.abc import Callable, Sequence

from flowscope.domain.llm import (
    LLMCommunicationError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMResposta,
    LLMServiceUnavailableError,
    LLMUnavailableError,
    LLMUsage,
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
    ("ServiceUnavailableError", LLMServiceUnavailableError),
    ("InternalServerError", LLMServiceUnavailableError),
    ("APIError", LLMProviderError),
)

#: Erros de domínio considerados transitórios e passíveis de nova tentativa.
_EXCECOES_TRANSITORIAS: tuple[type[LLMError], ...] = (
    LLMServiceUnavailableError,
    LLMRateLimitError,
    LLMCommunicationError,
)

#: Esperas (em segundos) antes de cada tentativa; o primeiro valor zero implica
#: tentativa imediata. O comprimento define o número máximo de tentativas.
RETRY_DELAYS: tuple[float, ...] = (0.0, 1.0, 3.0)


def _import_litellm() -> object:
    """Importa o liteLLM, convertendo a ausência em ``LLMUnavailableError``.

    Desabilita o banner de depuração do liteLLM, que de outro modo é impresso
    na saída padrão sempre que uma exceção do provedor é mapeada.
    """
    try:
        import litellm
    except ImportError as exc:
        raise LLMUnavailableError(MENSAGEM_DEPS_AUSENTES) from exc
    litellm.suppress_debug_info = True
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
        retry_delays: Sequence[float] = RETRY_DELAYS,
        sleeper: Callable[[float], None] | None = None,
        jitter: Callable[[], float] | None = None,
    ) -> None:
        """Guarda os parâmetros de chamada e configura rate limiter e retry."""
        self._model = model
        self._api_key = api_key
        self._api_url = api_url
        self._limiter = rate_limiter or RateLimiter(rpm)
        self._retry_delays = tuple(retry_delays)
        self._sleeper = sleeper or time.sleep
        self._jitter = jitter or random.random

    def complete(
        self: "LiteLLMChatAdapter",
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> LLMResposta:
        """Envia as mensagens ao provedor e devolve texto e uso de tokens."""
        payload = list(messages)
        if system_prompt is not None:
            payload = [
                {"role": "system", "content": system_prompt},
                *payload,
            ]
        litellm = _import_litellm()
        kwargs: dict[str, object] = {
            "model": self._model,
            "messages": payload,
            "api_key": self._api_key,
        }
        if self._api_url:
            kwargs["api_base"] = self._api_url
            kwargs["custom_llm_provider"] = "openai"
        resposta = self._chamar(litellm, kwargs)
        return LLMResposta(
            texto=resposta.choices[0].message.content,
            uso=_extrair_uso(resposta),
        )

    def _chamar(
        self: "LiteLLMChatAdapter",
        litellm: object,
        kwargs: dict[str, object],
    ) -> object:
        """Chama o provedor repetindo erros transitórios com backoff e jitter.

        Cada tentativa física adquire uma permissão do rate limiter. Erros
        permanentes propagam de imediato; ao esgotar as tentativas, a última
        exceção de domínio é propagada, preservando o contrato do chamador.
        """
        delays = self._retry_delays or (0.0,)
        ultima = len(delays) - 1
        for indice, atraso in enumerate(delays):
            self._aguardar(atraso)
            self._limiter.acquire()
            try:
                return litellm.completion(**kwargs)
            except Exception as exc:
                erro = _mapear_excecao(litellm, exc)
                if (
                    isinstance(erro, _EXCECOES_TRANSITORIAS)
                    and indice < ultima
                ):
                    continue
                raise erro from exc
        raise LLMProviderError("Nenhuma tentativa de chamada configurada.")

    def _aguardar(self: "LiteLLMChatAdapter", atraso: float) -> None:
        """Aguarda o backoff da tentativa, acrescido de jitter proporcional."""
        if atraso <= 0:
            return
        self._sleeper(atraso * (1 + self._jitter()))


def _campo(objeto: object, nome: str) -> object:
    """Lê um campo de um objeto ou dicionário, devolvendo ``None`` se ausente."""
    if isinstance(objeto, dict):
        return objeto.get(nome)
    return getattr(objeto, nome, None)


def _inteiro(valor: object) -> int:
    """Retorna o valor de token convertido em inteiro não negativo."""
    try:
        return max(0, int(valor))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _detalhes_cache(usage: object) -> tuple[int, int]:
    """Extrai ``(cache_hit, cache_write)`` do ``usage``, tolerando formatos.

    Prefere ``prompt_tokens_details`` e cai nos nomes nativos do liteLLM
    (``cache_read_input_tokens``, ``prompt_cache_hit_tokens`` e
    ``cache_creation_input_tokens``) quando os detalhes não estão presentes.
    """
    detalhes = _campo(usage, "prompt_tokens_details")
    if detalhes is None:
        hit = _campo(usage, "cached_tokens")
        if hit is None:
            hit = _campo(usage, "cache_read_input_tokens")
        if hit is None:
            hit = _campo(usage, "prompt_cache_hit_tokens")
        write = _campo(usage, "cache_creation_input_tokens")
        if write is None:
            write = _campo(usage, "cache_write_tokens")
        return _inteiro(hit), _inteiro(write)
    hit = _campo(detalhes, "cached_tokens")
    write = _campo(detalhes, "cache_creation_tokens")
    if write is None:
        write = _campo(detalhes, "cache_write_tokens")
    return _inteiro(hit), _inteiro(write)


def _extrair_uso(resposta: object) -> LLMUsage:
    """Traduz o ``usage`` do provedor para ``LLMUsage``, tolerando ausência."""
    usage = getattr(resposta, "usage", None)
    if usage is None:
        return LLMUsage()
    entrada = getattr(usage, "prompt_tokens", 0) or 0
    saida = getattr(usage, "completion_tokens", 0) or 0
    entrada_cache, cache_write = _detalhes_cache(usage)
    return LLMUsage(
        entrada=int(entrada),
        saida=int(saida),
        entrada_cache=entrada_cache,
        cache_write=cache_write,
    )
