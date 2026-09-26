"""Porta de configuração do provedor de LLM.

A apresentação lê/grava a configuração ``llm.chat``, consulta presets e
dependências e cria o provedor por meio desta porta, implementada em
``infrastructure``. Assim o diálogo de configuração não depende de
``infrastructure``.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from flowscope.domain.llm import LLMPort


@runtime_checkable
class LLMConfigPort(Protocol):
    """Contrato de leitura/gravação e construção do provedor de LLM."""

    def get_presets(self: "LLMConfigPort") -> dict[str, dict[str, str]]:
        """Retorna os presets de provedores disponíveis."""
        ...

    def load_provider_configs(
        self: "LLMConfigPort", path: Path | None = None,
    ) -> dict[str, dict]:
        """Retorna a configuração salva de cada provedor."""
        ...

    def load_llm_config(self: "LLMConfigPort", path: Path | None = None) -> dict:
        """Retorna a configuração do provedor ativo."""
        ...

    def save_llm_config(
        self: "LLMConfigPort", config: dict, path: Path | None = None,
    ) -> None:
        """Grava o bloco ``llm.chat`` preservando os demais blocos."""
        ...

    def check_llm_deps(self: "LLMConfigPort") -> bool:
        """Indica se as dependências opcionais ``[llm]`` estão instaladas."""
        ...

    def default_config(self: "LLMConfigPort") -> dict:
        """Retorna a configuração padrão do provedor."""
        ...

    def create_provider(self: "LLMConfigPort", config: dict) -> LLMPort:
        """Cria a porta de completion a partir da configuração informada."""
        ...
