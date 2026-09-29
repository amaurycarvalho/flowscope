"""Porta e exceções do domínio de LLM."""

from flowscope.domain.llm.exceptions import (
    LLMCommunicationError,
    LLMConfigurationError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMUnavailableError,
)
from flowscope.domain.llm.ports import LLMPort, LLMResposta, LLMUsage

__all__ = [
    "LLMCommunicationError",
    "LLMConfigurationError",
    "LLMError",
    "LLMPort",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMResposta",
    "LLMServiceUnavailableError",
    "LLMUnavailableError",
    "LLMUsage",
]
