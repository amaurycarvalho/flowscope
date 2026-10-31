"""Tipos compartilhados do catálogo MCP."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    """Especificação de uma tool MCP."""

    nome: str
    operacao: str
    titulo: str
    descricao: str
    schema: dict


__all__ = ["Tool"]
