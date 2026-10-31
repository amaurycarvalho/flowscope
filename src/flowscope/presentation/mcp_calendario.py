"""Execução das tools MCP de calendário sobre o serviço de aplicação."""

from __future__ import annotations

from flowscope.application.calendar.service import CalendarService
from flowscope.presentation.mcp_types import Tool

_ANO = {"type": "integer", "minimum": 1, "description": "Ano do calendário."}
_DATA = {"type": "string", "description": "Data no formato AAAA-MM-DD."}
_FORMATO = {
    "type": "string",
    "enum": ["csv", "json"],
    "description": "Formato de exportação.",
}

CATALOGO_CALENDARIO: tuple[Tool, ...] = (
    Tool(
        nome="calendario_classificar",
        operacao="calendario_classificar",
        titulo="Classificar data",
        descricao="Classifica uma data como dia útil ou não, com motivo e origem.",
        schema={
            "type": "object",
            "properties": {"data": _DATA},
            "required": ["data"],
            "additionalProperties": False,
        },
    ),
    Tool(
        nome="calendario_exportar",
        operacao="calendario_exportar",
        titulo="Exportar feriados",
        descricao="Exporta o calendário de um ano em CSV ou JSON, sem gravar arquivo.",
        schema={
            "type": "object",
            "properties": {"ano": _ANO, "formato": _FORMATO},
            "required": ["ano", "formato"],
            "additionalProperties": False,
        },
    ),
    Tool(
        nome="calendario_listar",
        operacao="calendario_listar",
        titulo="Listar feriados",
        descricao="Lista os feriados de um ano a partir do cache local.",
        schema={
            "type": "object",
            "properties": {"ano": _ANO},
            "required": ["ano"],
            "additionalProperties": False,
        },
    ),
)


class ErroCalendario(Exception):
    """Erro recuperável de uma tool de calendário."""


class FerramentasCalendario:
    """Executa as tools ``calendario_*`` sobre o serviço de aplicação."""

    def __init__(
        self: FerramentasCalendario, service: CalendarService | None
    ) -> None:
        """Store the optional calendar service."""
        self._service = service

    def executar(self: FerramentasCalendario, nome: str, argumentos: dict) -> object:
        """Execute one calendar tool and return structured content."""
        if self._service is None:
            return {"estado": "calendario_indisponivel"}
        try:
            if nome == "calendario_listar":
                return self._service.listar_ano(int(argumentos["ano"]))
            if nome == "calendario_classificar":
                return self._service.classificar(str(argumentos["data"]))
            return {
                "ano": int(argumentos["ano"]),
                "formato": str(argumentos["formato"]),
                "conteudo": self._service.exportar_ano(
                    int(argumentos["ano"]), str(argumentos["formato"])
                ),
            }
        except (ValueError, KeyError) as exc:
            raise ErroCalendario(str(exc)) from exc


def executar_calendario(
    ferramentas: FerramentasCalendario, nome: str, argumentos: dict
) -> tuple[object, bool]:
    """Execute a calendar tool, converting recoverable errors to content."""
    try:
        return ferramentas.executar(nome, argumentos), False
    except ErroCalendario as exc:
        return {
            "erro": {
                "motivo": "calendario_invalido",
                "detalhe": str(exc),
                "dica": "revise a data, o ano ou o formato informado",
            }
        }, False


__all__ = [
    "CATALOGO_CALENDARIO",
    "ErroCalendario",
    "FerramentasCalendario",
    "executar_calendario",
]
