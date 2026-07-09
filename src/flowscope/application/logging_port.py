from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass
class LogEntry:
    message: str
    level: str
    component: str
    exception: Exception | None = None
    context: dict | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class LogReference:
    source: str
    identifier: str
    hint: str


class LogPort(Protocol):
    def error(self, entry: LogEntry) -> LogReference: ...
    def warning(self, entry: LogEntry) -> LogReference: ...
    def info(self, entry: LogEntry) -> LogReference: ...
