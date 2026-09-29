"""Testes dos presets de provedores de LLM."""

import pytest

from flowscope.domain.llm import LLMConfigurationError
from flowscope.infrastructure.llm import presets as presets_module
from flowscope.infrastructure.llm.presets import (
    PROVIDER_PRESETS,
    cache_suportado,
    resolve_context_window,
    resolve_provider,
    token_counter_for,
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


class TestJanelaECache:
    @pytest.mark.parametrize(
        ("provider", "esperado"),
        [
            ("openai", 128000),
            ("gemini", 1048576),
            ("ollama", 131072),
            ("custom", 0),
            ("none", 0),
        ],
    )
    def test_preset_tem_context_window(self, provider, esperado):
        assert PROVIDER_PRESETS[provider]["context_window"] == esperado

    def test_cache_suportado_por_preset(self):
        assert cache_suportado("openai") is True
        assert cache_suportado("ollama") is False
        assert cache_suportado("none") is False
        assert cache_suportado("inexistente") is False

    def test_resolve_prefere_litellm(self, monkeypatch):
        monkeypatch.setattr(
            presets_module, "_janela_litellm", lambda model: 777
        )
        assert resolve_context_window("openai", "gpt-4o-mini") == 777

    def test_resolve_cai_no_preset_sem_litellm(self, monkeypatch):
        monkeypatch.setattr(presets_module, "_janela_litellm", lambda model: 0)
        assert resolve_context_window("openai", "gpt-4o-mini") == 128000

    def test_resolve_sem_modelo_usa_preset(self, monkeypatch):
        monkeypatch.setattr(presets_module, "_janela_litellm", lambda model: 999)
        assert resolve_context_window("openai", "") == 128000
        assert resolve_context_window("custom", None) == 0

    def test_contador_memoiza_por_texto(self, monkeypatch):
        chamadas: list[str] = []

        def contar(model, texto):
            chamadas.append(texto)
            return len(texto)

        monkeypatch.setattr(presets_module, "_contar_litellm", contar)
        presets_module._CONTADORES.pop("modelo-teste", None)
        contador = token_counter_for("modelo-teste")
        assert contador("abc") == 3
        assert contador("abc") == 3
        assert chamadas == ["abc"]
