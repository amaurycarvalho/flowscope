import logging
import traceback

from flowscope.application.logging_port import LogEntry, LogPort, LogReference


class PythonLogAdapter:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def error(self, entry: LogEntry) -> LogReference:
        self._log(logging.ERROR, entry)
        return self._make_reference(entry)

    def warning(self, entry: LogEntry) -> LogReference:
        self._log(logging.WARNING, entry)
        return self._make_reference(entry)

    def info(self, entry: LogEntry) -> LogReference:
        self._log(logging.INFO, entry)
        return self._make_reference(entry)

    def _log(self, level: int, entry: LogEntry) -> None:
        extra = {"component": entry.component, "context": entry.context or {}}
        message = f"[{entry.component}] {entry.message}"
        if entry.exception:
            message += "\n" + "".join(traceback.format_exception(type(entry.exception), entry.exception, entry.exception.__traceback__))
        self._logger.log(level, message, exc_info=entry.exception is not None, extra=extra)

    def _make_reference(self, entry: LogEntry) -> LogReference:
        return LogReference(
            source="flowscope.log",
            identifier=entry.timestamp.isoformat(),
            hint="Consulte o arquivo de log em ~/.flowscope/logs/flowscope.log",
        )
