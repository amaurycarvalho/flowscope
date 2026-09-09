"""Implementações de ``DocumentSource`` para alimentar o VectorStore do llm-chat."""

from flowscope.infrastructure.document_sources.material_facts_source import (
    MaterialFactsSource,
)
from flowscope.infrastructure.document_sources.noticias_source import NoticiasSource

__all__ = ["MaterialFactsSource", "NoticiasSource"]
