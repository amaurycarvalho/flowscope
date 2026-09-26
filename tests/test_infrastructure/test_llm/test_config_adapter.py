"""Testes do adaptador da porta de configuração de LLM."""

from flowscope.infrastructure.llm.config_adapter import InfrastructureLLMConfig


class TestInfrastructureLLMConfig:
    def test_presets_e_defaults(self):
        port = InfrastructureLLMConfig()
        assert "deepseek" in port.get_presets()
        assert "rpm" in port.default_config()
        assert isinstance(port.check_llm_deps(), bool)

    def test_salvar_e_carregar(self, tmp_path):
        port = InfrastructureLLMConfig()
        caminho = tmp_path / "config.json"
        config = {
            "provider": "openai",
            "api_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "api_key": "sk-2",
            "rpm": 5,
        }
        port.save_llm_config(config, caminho)

        assert port.load_llm_config(caminho)["provider"] == "openai"
        assert port.load_provider_configs(caminho)["openai"]["model"] == (
            "gpt-4o-mini"
        )

    def test_create_provider_delega(self, monkeypatch):
        from flowscope.infrastructure.llm import config_adapter

        monkeypatch.setattr(
            config_adapter, "create_llm_provider", lambda config: ("prov", config)
        )
        config = {"provider": "none"}
        assert InfrastructureLLMConfig().create_provider(config) == (
            "prov",
            config,
        )
