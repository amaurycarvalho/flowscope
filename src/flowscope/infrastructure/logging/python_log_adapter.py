"""Adaptador do port de logging para o módulo logging padrão do Python."""

import logging
import traceback

from flowscope.application.logging_port import LogEntry, LogReference


class PythonLogAdapter:
    """Registra entradas de log no logger padrão do Python."""

    def __init__(self: "PythonLogAdapter", logger: logging.Logger) -> None:
        """Inicializa o adaptador com o logger Python que receberá as mensagens."""
        self._logger = logger

    def error(self: "PythonLogAdapter", entry: LogEntry) -> LogReference:
        """Registra a entrada no nível de erro e retorna sua referência."""
        self._log(logging.ERROR, entry)
        return self._make_reference(entry)

    def warning(self: "PythonLogAdapter", entry: LogEntry) -> LogReference:
        """Registra a entrada no nível de aviso e retorna sua referência."""
        self._log(logging.WARNING, entry)
        return self._make_reference(entry)

    def info(self: "PythonLogAdapter", entry: LogEntry) -> LogReference:
        """Registra a entrada no nível informativo e retorna sua referência."""
        self._log(logging.INFO, entry)
        return self._make_reference(entry)

    def _log(self: "PythonLogAdapter", level: int, entry: LogEntry) -> None:
        extra = {"component": entry.component, "context": entry.context or {}}
        message = f"[{entry.component}] {entry.message}"
        if entry.exception:
            message += "\n" + "".join(
                traceback.format_exception(
                    type(entry.exception), entry.exception,
                    entry.exception.__traceback__,
                ),
            )
        self._logger.log(level, message, exc_info=entry.exception is not None, extra=extra)

    def _make_reference(self: "PythonLogAdapter", entry: LogEntry) -> LogReference:
        return LogReference(
            source="flowscope.log",
            identifier=entry.timestamp.isoformat(),
            hint="Consulte o arquivo de log em ~/.flowscope/logs/flowscope.log",
        )
