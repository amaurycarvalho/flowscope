"""Testes dos presets de provedores de LLM."""

import pytest

from flowscope.domain.llm import LLMConfigurationError
from flowscope.infrastructure.llm.presets import (
    PROVIDER_PRESETS,
    resolve_provider,
)

pytestmark = pytest.mark.llm


class TestPresets:
    def test_todos_os_provedores_presentes(self):
        assert set(PROVIDER_PRESETS) == {
            "none",
            "openai",
            "gemini",
            "copilot",
            "claude",
            "deepseek",
            "ollama",
            "custom",
        }

    @pytest.mark.parametrize(
        ("provider", "model", "api_url"),
        [
            ("openai", "gpt-4o-mini", "https://api.openai.com/v1"),
            (
                "gemini",
                "gemini-3.1-flash-lite",
                "https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
            ("copilot", "gpt-4o", "https://models.inference.ai.azure.com"),
            (
                "claude",
                "claude-sonnet-4-20250514",
                "https://api.anthropic.com/v1",
            ),
            ("deepseek", "deepseek-chat", "https://api.deepseek.com/v1"),
            ("ollama", "llama3.2", "http://localhost:11434/v1"),
        ],
    )
    def test_defaults_dos_presets(self, provider, model, api_url):
        resolvido = resolve_provider(provider)
        assert resolvido == (model, api_url)

    def test_custom_usa_valores_informados(self):
        assert resolve_provider(
            "custom", "meu-modelo", "https://meu.endpoint/v1"
        ) == ("meu-modelo", "https://meu.endpoint/v1")

    def test_sobreposicao_de_modelo(self):
        modelo, api_url = resolve_provider("openai", model="outro")
        assert modelo == "outro"
        assert api_url == "https://api.openai.com/v1"

    def test_provedor_desconhecido_rejeitado(self):
        with pytest.raises(LLMConfigurationError):
            resolve_provider("inexistente")

    def test_custom_incompleto_rejeitado(self):
        with pytest.raises(LLMConfigurationError):
            resolve_provider("custom", model="apenas-modelo")
