"""Portas da camada de aplicação para registro de logs."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass
class LogEntry:
    """Representa uma entrada de log a ser registrada."""

    message: str
    level: str
    component: str
    exception: Exception | None = None
    context: dict | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class LogReference:
    """Referência a uma entrada de log já registrada."""

    source: str
    identifier: str
    hint: str


class LogPort(Protocol):
    """Define o contrato para registro de mensagens de log."""

    def error(self: "LogPort", entry: LogEntry) -> LogReference:
        """Registra a entrada no nível de erro e retorna sua referência."""
        ...

    def warning(self: "LogPort", entry: LogEntry) -> LogReference:
        """Registra a entrada no nível de aviso e retorna sua referência."""
        ...

    def info(self: "LogPort", entry: LogEntry) -> LogReference:
        """Registra a entrada no nível informativo e retorna sua referência."""
        ...
