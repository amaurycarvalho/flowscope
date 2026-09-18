"""Testes da factory de provedores de LLM."""

from unittest.mock import MagicMock

import pytest

from flowscope.domain.llm import (
    LLMConfigurationError,
    LLMPort,
    LLMUnavailableError,
)
from flowscope.infrastructure.llm import factory as factory_module
from flowscope.infrastructure.llm.factory import create_llm_provider

pytestmark = pytest.mark.llm


@pytest.fixture
def deps_ok(monkeypatch):
    monkeypatch.setattr(factory_module, "check_llm_deps", lambda: True)


class TestCreateLLMProvider:
    def test_provider_configurado(self, monkeypatch, deps_ok):
        construtor = MagicMock(return_value=MagicMock(spec=LLMPort))
        monkeypatch.setattr(factory_module, "LiteLLMChatAdapter", construtor)
        provedor = create_llm_provider(
            {
                "provider": "deepseek",
                "api_key": "sk-1",
                "rpm": 9,
            }
        )
        assert provedor is construtor.return_value
        construtor.assert_called_once_with(
            model="deepseek-chat",
            api_url="https://api.deepseek.com/v1",
            api_key="sk-1",
            rpm=9,
        )

    def test_custom_usa_valores_informados(self, monkeypatch, deps_ok):
        construtor = MagicMock(return_value=MagicMock(spec=LLMPort))
        monkeypatch.setattr(factory_module, "LiteLLMChatAdapter", construtor)
        create_llm_provider(
            {
                "provider": "custom",
                "model": "meu-modelo",
                "api_url": "https://meu/v1",
                "api_key": "k",
            }
        )
        _, kwargs = construtor.call_args
        assert kwargs["model"] == "meu-modelo"
        assert kwargs["api_url"] == "https://meu/v1"
        assert kwargs["rpm"] == 5

    def test_provider_none(self, deps_ok):
        with pytest.raises(LLMUnavailableError):
            create_llm_provider({"provider": "none"})

    def test_provider_ausente_e_none(self, deps_ok):
        with pytest.raises(LLMUnavailableError):
            create_llm_provider({})

    def test_deps_ausentes(self, monkeypatch):
        monkeypatch.setattr(factory_module, "check_llm_deps", lambda: False)
        with pytest.raises(LLMUnavailableError):
            create_llm_provider({"provider": "openai"})

    def test_custom_incompleto(self, deps_ok):
        with pytest.raises(LLMConfigurationError):
            create_llm_provider({"provider": "custom", "model": "m"})

    def test_provedor_desconhecido(self, deps_ok):
        with pytest.raises(LLMConfigurationError):
            create_llm_provider({"provider": "inexistente"})
