"""Hierarquia de exceções tipadas da camada de LLM.

Os consumidores (chat RAG, resumo de documentos) dependem apenas destas
exceções de domínio para decidir como reagir a cada falha, sem acoplar-se às
exceções nativas do liteLLM.
"""


class LLMError(Exception):
    """Erro base de toda a camada de LLM."""


class LLMUnavailableError(LLMError):
    """LLM indisponível (provedor ``none`` ou dependências ``[llm]`` ausentes)."""


class LLMConfigurationError(LLMError):
    """Configuração de LLM inválida (ex.: provedor ``custom`` incompleto)."""


class LLMCommunicationError(LLMError):
    """Falha de comunicação com o provedor (timeout, conexão)."""


class LLMProviderError(LLMError):
    """Erro retornado pelo provedor (autenticação, requisição inválida)."""


class LLMServiceUnavailableError(LLMError):
    """Provedor temporariamente indisponível (sobrecarga ou erro 5xx)."""


class LLMRateLimitError(LLMError):
    """Cota do provedor excedida."""
