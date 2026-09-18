"""Teste de fumaça dos pontos de extensão entregues pela change ``llm-core``.

Garante que os símbolos consumidos pelas changes seguintes (porta, factory,
verificação de dependências e exceções tipadas) permanecem importáveis sem
carregar a dependência opcional ``litellm`` no momento do import.
"""

from flowscope.domain.llm import (
    LLMCommunicationError,
    LLMConfigurationError,
    LLMError,
    LLMPort,
    LLMProviderError,
    LLMRateLimitError,
    LLMUnavailableError,
)
from flowscope.infrastructure.llm.config import check_llm_deps
from flowscope.infrastructure.llm.factory import create_llm_provider


def test_simbolos_da_llm_core_importaveis():
    assert LLMPort is not None
    assert callable(create_llm_provider)
    assert callable(check_llm_deps)


def test_excecoes_tipadas_herdam_de_llm_error():
    for excecao in (
        LLMUnavailableError,
        LLMConfigurationError,
        LLMCommunicationError,
        LLMProviderError,
        LLMRateLimitError,
    ):
        assert issubclass(excecao, LLMError)
