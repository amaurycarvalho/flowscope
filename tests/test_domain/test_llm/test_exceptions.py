"""Testes da hierarquia de exceções do domínio de LLM."""

import pytest

from flowscope.domain.llm import (
    LLMCommunicationError,
    LLMConfigurationError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMUnavailableError,
)

pytestmark = pytest.mark.llm


class TestHierarquia:
    @pytest.mark.parametrize(
        "excecao",
        [
            LLMUnavailableError,
            LLMConfigurationError,
            LLMCommunicationError,
            LLMProviderError,
            LLMRateLimitError,
            LLMServiceUnavailableError,
        ],
    )
    def test_subclasses_de_llm_error(self, excecao):
        assert issubclass(excecao, LLMError)

    def test_llm_error_e_exception(self):
        assert issubclass(LLMError, Exception)

    def test_mensagem_preservada(self):
        erro = LLMProviderError("falha do provedor")
        assert str(erro) == "falha do provedor"
