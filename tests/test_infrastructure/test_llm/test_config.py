"""Testes de leitura, gravação e detecção de dependências da config de LLM."""

import json

import pytest

from flowscope.infrastructure.llm import config as config_module
from flowscope.infrastructure.llm.config import (
    DEFAULT_LLM_CONFIG,
    check_llm_deps,
    get_presets,
    load_llm_config,
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
        assert dados["llm"]["chat"]["rpm"] == 5


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
