"""Testes de leitura, gravação e detecção de dependências da config de LLM."""

import json

import pytest

from flowscope.infrastructure.llm import config as config_module
from flowscope.infrastructure.llm.config import (
    DEFAULT_LLM_CONFIG,
    check_llm_deps,
    get_presets,
    load_llm_config,
    load_provider_configs,
    save_llm_config,
)
from flowscope.infrastructure.llm.presets import PROVIDER_PRESETS

pytestmark = pytest.mark.llm


class TestLoad:
    def test_arquivo_ausente_retorna_defaults(self, tmp_path):
        config = load_llm_config(tmp_path / "config.json")
        assert config == DEFAULT_LLM_CONFIG
        assert config["provider"] == "none"

    def test_config_completa(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps(
                {
                    "llm": {
                        "chat": {
                            "provider": "deepseek",
                            "api_url": "https://api.deepseek.com/v1",
                            "model": "deepseek-chat",
                            "api_key": "sk-123",
                            "rpm": 15,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        config = load_llm_config(caminho)
        assert config["provider"] == "deepseek"
        assert config["api_key"] == "sk-123"
        assert config["rpm"] == 15

    def test_leitura_parcial_preenche_defaults(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps({"llm": {"chat": {"provider": "openai"}}}),
            encoding="utf-8",
        )
        config = load_llm_config(caminho)
        assert config["provider"] == "openai"
        assert config["api_url"] == ""
        assert config["rpm"] == 5

    def test_rpm_invalido_usa_default(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps({"llm": {"chat": {"rpm": "abc"}}}),
            encoding="utf-8",
        )
        assert load_llm_config(caminho)["rpm"] == 5

    def test_json_invalido_retorna_defaults(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text("{invalido", encoding="utf-8")
        assert load_llm_config(caminho) == DEFAULT_LLM_CONFIG


class TestProviderConfigs:
    def test_novo_formato(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps(
                {
                    "llm": {
                        "chat": {
                            "provider": "deepseek",
                            "providers": {
                                "openai": {
                                    "api_url": "https://api.openai.com/v1",
                                    "model": "gpt-4o-mini",
                                    "api_key": "sk-open",
                                    "rpm": 3,
                                },
                                "deepseek": {
                                    "api_url": "https://api.deepseek.com/v1",
                                    "model": "deepseek-chat",
                                    "api_key": "sk-deep",
                                    "rpm": 7,
                                },
                            },
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        providers = load_provider_configs(caminho)
        assert set(providers) == {"openai", "deepseek"}
        assert providers["deepseek"]["api_key"] == "sk-deep"
        assert providers["deepseek"]["rpm"] == 7

    def test_migra_formato_plano(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps(
                {
                    "llm": {
                        "chat": {
                            "provider": "deepseek",
                            "api_url": "https://api.deepseek.com/v1",
                            "model": "deepseek-chat",
                            "api_key": "sk-123",
                            "rpm": 15,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        providers = load_provider_configs(caminho)
        assert providers == {
            "deepseek": {
                "api_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "api_key": "sk-123",
                "rpm": 15,
            }
        }

    def test_ausente_retorna_vazio(self, tmp_path):
        assert load_provider_configs(tmp_path / "config.json") == {}


class TestSave:
    def test_gravacao_preserva_outras_chaves(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps(
                {
                    "last_tab": "Análise Geral",
                    "llm": {
                        "embedding": {"provider": "local"},
                        "chat": {"provider": "none"},
                    },
                }
            ),
            encoding="utf-8",
        )
        save_llm_config(
            {
                "provider": "openai",
                "api_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini",
                "api_key": "sk-1",
                "rpm": 5,
            },
            caminho,
        )
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        assert dados["last_tab"] == "Análise Geral"
        assert dados["llm"]["embedding"] == {"provider": "local"}
        assert dados["llm"]["chat"]["provider"] == "openai"

    def test_roundtrip(self, tmp_path):
        caminho = tmp_path / "config.json"
        original = {
            "provider": "ollama",
            "api_url": "http://localhost:11434/v1",
            "model": "llama3.2",
            "api_key": "",
            "rpm": 7,
        }
        save_llm_config(original, caminho)
        assert load_llm_config(caminho) == original

    def test_cria_diretorio(self, tmp_path):
        caminho = tmp_path / "sub" / "config.json"
        save_llm_config({"provider": "openai"}, caminho)
        assert caminho.exists()

    def test_campos_ausentes_usam_default(self, tmp_path):
        caminho = tmp_path / "config.json"
        save_llm_config({"provider": "openai"}, caminho)
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        assert dados["llm"]["chat"]["providers"]["openai"]["rpm"] == 5

    def test_salvar_preserva_outros_provedores(self, tmp_path):
        caminho = tmp_path / "config.json"
        save_llm_config(
            {
                "provider": "openai",
                "api_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini",
                "api_key": "sk-open",
                "rpm": 3,
            },
            caminho,
        )
        save_llm_config(
            {
                "provider": "deepseek",
                "api_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "api_key": "sk-deep",
                "rpm": 7,
            },
            caminho,
        )
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        assert dados["llm"]["chat"]["provider"] == "deepseek"
        assert (
            dados["llm"]["chat"]["providers"]["openai"]["api_key"] == "sk-open"
        )
        assert (
            dados["llm"]["chat"]["providers"]["deepseek"]["api_key"] == "sk-deep"
        )

    def test_salvar_none_preserva_provedores(self, tmp_path):
        caminho = tmp_path / "config.json"
        save_llm_config(
            {
                "provider": "deepseek",
                "api_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "api_key": "sk-deep",
                "rpm": 7,
            },
            caminho,
        )
        save_llm_config({"provider": "none"}, caminho)
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        assert dados["llm"]["chat"]["provider"] == "none"
        assert (
            dados["llm"]["chat"]["providers"]["deepseek"]["api_key"] == "sk-deep"
        )

    def test_migracao_grava_formato_novo(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps(
                {
                    "llm": {
                        "chat": {
                            "provider": "deepseek",
                            "api_url": "https://api.deepseek.com/v1",
                            "model": "deepseek-chat",
                            "api_key": "sk-123",
                            "rpm": 15,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        save_llm_config(load_llm_config(caminho), caminho)
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        assert "providers" in dados["llm"]["chat"]
        entrada = dados["llm"]["chat"]["providers"]["deepseek"]
        assert entrada["api_key"] == "sk-123"
        assert entrada["rpm"] == 15


class TestGuidanceBlockRemovido:
    def test_flag_nao_existe_mais(self):
        assert not hasattr(config_module, "load_guidance_llm_enabled")
        assert not hasattr(config_module, "save_guidance_llm_enabled")
        assert not hasattr(config_module, "guidance_llm_disponivel")
        assert not hasattr(config_module, "DEFAULT_GUIDANCE_ENABLED")

    def test_bloco_legado_nao_afeta_a_leitura(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps(
                {
                    "llm": {
                        "chat": {"provider": "none"},
                        "guidance": {"enabled": True},
                    }
                }
            ),
            encoding="utf-8",
        )
        assert load_llm_config(caminho)["provider"] == "none"

    def test_bloco_legado_removido_na_gravacao(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps(
                {
                    "llm": {
                        "chat": {"provider": "none"},
                        "guidance": {"enabled": True},
                    }
                }
            ),
            encoding="utf-8",
        )
        save_llm_config(load_llm_config(caminho), caminho)
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        assert "guidance" not in dados["llm"]


class TestInputLimitadoRemovido:
    def test_chave_ausente_do_config(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps({"llm": {"chat": {"provider": "openai"}}}),
            encoding="utf-8",
        )
        assert "input_limitado" not in load_llm_config(caminho)

    def test_chave_antiga_ignorada_na_leitura(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps(
                {
                    "llm": {
                        "chat": {
                            "provider": "openai",
                            "providers": {"openai": {"input_limitado": "true"}},
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        assert "input_limitado" not in load_provider_configs(caminho)["openai"]

    def test_chave_antiga_nao_e_gravada(self, tmp_path):
        caminho = tmp_path / "config.json"
        save_llm_config(
            {
                "provider": "gemini",
                "api_url": "https://x/v1",
                "model": "gemini",
                "api_key": "k",
                "rpm": 5,
                "input_limitado": True,
            },
            caminho,
        )
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        assert "input_limitado" not in dados["llm"]["chat"]["providers"]["gemini"]


class TestDeps:
    def test_get_presets_expoe_provider_presets(self):
        assert get_presets() is PROVIDER_PRESETS

    def test_check_llm_deps_verdadeiro_quando_instalado(self):
        assert check_llm_deps() is True

    def test_check_llm_deps_falso_quando_ausente(self, monkeypatch):
        def _ausente(_nome):
            raise ModuleNotFoundError("No module named 'litellm'")

        monkeypatch.setattr(
            config_module.importlib.util, "find_spec", _ausente
        )
        assert check_llm_deps() is False
