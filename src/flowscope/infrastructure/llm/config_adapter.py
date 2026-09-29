"""Adaptador da porta de configuração de LLM sobre a infraestrutura.

Liga ``application.llm_config_port.LLMConfigPort`` às funções de leitura,
gravação, presets e dependências de ``infrastructure.llm.config`` e à fábrica
``create_llm_provider``.
"""

from collections.abc import Callable
from pathlib import Path

from flowscope.domain.llm import LLMPort
from flowscope.infrastructure.llm.config import (
    DEFAULT_LLM_CONFIG,
    check_llm_deps,
    get_presets,
    load_llm_config,
    load_provider_configs,
    save_llm_config,
)
from flowscope.infrastructure.llm.factory import create_llm_provider
from flowscope.infrastructure.llm.presets import (
    cache_suportado,
    resolve_context_window,
    token_counter_for,
)


class InfrastructureLLMConfig:
    """Implementação de ``LLMConfigPort`` sobre a infraestrutura de LLM."""

    def get_presets(self: "InfrastructureLLMConfig") -> dict[str, dict[str, object]]:
        """Retorna os presets de provedores disponíveis."""
        return get_presets()

    def context_window(self: "InfrastructureLLMConfig", config: dict) -> int:
        """Retorna a janela de contexto do modelo da configuração."""
        provider = str(config.get("provider") or "none")
        model = str(config.get("model") or "")
        return resolve_context_window(provider, model)

    def cache_suportado(self: "InfrastructureLLMConfig", config: dict) -> bool:
        """Indica se o provedor da configuração suporta cache de prompt."""
        return cache_suportado(str(config.get("provider") or "none"))

    def input_limitado(self: "InfrastructureLLMConfig", config: dict) -> bool:
        """Indica se o modelo da configuração tem janela de entrada limitada."""
        return bool(config.get("input_limitado", False))

    def token_counter(
        self: "InfrastructureLLMConfig", config: dict
    ) -> Callable[[str], int] | None:
        """Retorna um contador de tokens do modelo, ou ``None`` sem provedor."""
        provider = str(config.get("provider") or "none")
        model = str(config.get("model") or "")
        if provider == "none" or not model:
            return None
        return token_counter_for(model)

    def load_provider_configs(
        self: "InfrastructureLLMConfig", path: Path | None = None,
    ) -> dict[str, dict]:
        """Retorna a configuração salva de cada provedor."""
        return load_provider_configs(path)

    def load_llm_config(
        self: "InfrastructureLLMConfig", path: Path | None = None,
    ) -> dict:
        """Retorna a configuração do provedor ativo."""
        return load_llm_config(path)

    def save_llm_config(
        self: "InfrastructureLLMConfig", config: dict,
        path: Path | None = None,
    ) -> None:
        """Grava o bloco ``llm.chat`` preservando os demais blocos."""
        save_llm_config(config, path)

    def check_llm_deps(self: "InfrastructureLLMConfig") -> bool:
        """Indica se as dependências opcionais ``[llm]`` estão instaladas."""
        return check_llm_deps()

    def default_config(self: "InfrastructureLLMConfig") -> dict:
        """Retorna a configuração padrão do provedor."""
        return dict(DEFAULT_LLM_CONFIG)

    def create_provider(self: "InfrastructureLLMConfig", config: dict) -> LLMPort:
        """Cria a porta de completion a partir da configuração informada."""
        return create_llm_provider(config)
