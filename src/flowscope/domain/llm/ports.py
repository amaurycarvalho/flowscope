"""Porta genérica de completion de LLM.

Define o contrato consumido pela aplicação e pela GUI. Adaptadores concretos
(como o adaptador sobre o liteLLM) implementam este protocolo, de modo que os
consumidores nunca dependam diretamente de uma biblioteca de LLM.
"""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class LLMUsage:
    """Uso de tokens reportado pelo provedor em uma completion.

    ``entrada`` e ``saida`` valem zero quando o provedor não reporta o dado.
    ``entrada_cache`` são os tokens de entrada servidos por cache de prompt
    (leitura) e ``cache_write`` os de criação de cache, também zero quando
    ausentes.
    """

    entrada: int = 0
    saida: int = 0
    entrada_cache: int = 0
    cache_write: int = 0


@dataclass(frozen=True)
class LLMResposta:
    """Resposta de completion com o texto e o uso de tokens."""

    texto: str = ""
    uso: LLMUsage = field(default_factory=LLMUsage)


class LLMPort(Protocol):
    """Porta de completion que recebe mensagens e devolve texto e uso."""

    def complete(
        self: "LLMPort",
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> LLMResposta:
        """Envia mensagens no formato ``{"role", "content"}`` e retorna a resposta."""
        ...
