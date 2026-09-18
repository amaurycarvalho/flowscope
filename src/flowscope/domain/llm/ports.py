"""Porta genérica de completion de LLM.

Define o contrato consumido pela aplicação e pela GUI. Adaptadores concretos
(como o adaptador sobre o liteLLM) implementam este protocolo, de modo que os
consumidores nunca dependam diretamente de uma biblioteca de LLM.
"""

from typing import Protocol


class LLMPort(Protocol):
    """Porta de completion que recebe mensagens e devolve texto."""

    def complete(
        self: "LLMPort",
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        """Envia mensagens no formato ``{"role", "content"}`` e retorna a resposta."""
        ...
