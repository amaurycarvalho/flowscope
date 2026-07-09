## Context

The codebase uses Clean Architecture with ports/adapters (e.g., `DataRepository` Protocol in `application/ports.py`). Currently logging is minimal and completely silenced at runtime — `main.py` installs `logging.NullHandler`, so all `logger.info/error/warning` calls go nowhere. Errors bubble up to the controller, which calls `presenter.on_error(e)` showing a generic message in the Tkinter status bar. There is no log persistence, no centralized logging abstraction, and no way to diagnose issues post-facto.

The B3 data source (HTTP API) is transient — network errors, parse failures, and server timeouts are expected but currently invisible to the user beyond a vague status bar message.

## Goals / Non-Goals

**Goals:**
- Add a `LogPort` Protocol in the application layer so logging is abstracted (follows existing `DataRepository` pattern)
- Implement `PythonLogAdapter` in infrastructure that delegates to Python's stdlib `logging` module
- Configure platform-appropriate handlers in `main.py`: `SysLogHandler` (Linux/macOS), `NTEventLogHandler` (Windows), `RotatingFileHandler` (universal fallback)
- Inject `LogPort` into `FlowScopeController` and log technical errors (HTTP failures, parse errors, unexpected exceptions) before showing status bar message
- Add `on_technical_error(error, ref)` to `FlowScopePresenter` with a user-friendly message pointing to the log
- Make existing `logger` calls in `infrastructure/b3/client.py` and `repository.py` actually work by removing `NullHandler`

**Non-Goals:**
- No changes to domain layer logging (domain entities/strategies don't need logging today)
- No async logging or log queue (blocking on log write is acceptable; this is a desktop app, not a server)
- No log level configuration UI or log viewer (logs are consumed via OS-native tools)
- No structured log format beyond what stdlib provides
- No changes to business/domain error handling in status bar (PortfolioNotFoundError, InvalidIndexError remain unchanged)
- No removal of bare `except Exception` in `app.py` (those are separate scope)

## Decisions

### Architecture: Adapter wrapping stdlib, not per-OS custom adapter

```
┌─────────────────────────────────────────────┐
│  Controller (presentation)                  │
│    dependency → LogPort                     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  PythonLogAdapter (infrastructure)          │
│    delegates to → logging.Logger            │
│                   managed by → logging cfg  │
└──────────────────┬──────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
SysLogHandler  NTEventLogHandler  RotatingFileHandler
(Linux/macOS)   (Windows)         (~/.flowscope/logs/)
```

Alternative considered: writing a separate adapter per platform using native APIs via ctypes. Rejected because Python's stdlib `logging.handlers` already wraps the three native targets — `SysLogHandler` talks to `/dev/log` (Linux) or `/var/run/syslog` (macOS), and `NTEventLogHandler` talks to the Windows Event Log via `ReportEvent`. There is zero benefit in reimplementing what stdlib already provides.

Alternative considered: using a third-party lib like `loguru`. Rejected because this project uses stdlib `logging` already and prefers zero external dependencies.

### Port in `application/logging_port.py` (separate from `ports.py`)

The `LogPort` Protocol goes in its own file rather than in `application/ports.py` alongside `DataRepository`. Rationale: `DataRepository` is a data port, `LogPort` is an observability port — they have different consumers and different evolution paths. A separate file keeps each port independently discoverable and importable.

```python
@dataclass
class LogEntry:
    message: str
    level: str                          # "ERROR" | "WARNING" | "INFO"
    component: str                      # "Controller.on_index_clicked"
    exception: Exception | None = None
    context: dict | None = None

@dataclass(frozen=True)
class LogReference:
    source: str                         # "syslog" | "eventlog" | "file"
    identifier: str                     # timestamp ISO
    hint: str                           # user-facing guidance

class LogPort(Protocol):
    def error(self, entry: LogEntry) -> LogReference: ...
    def warning(self, entry: LogEntry) -> LogReference: ...
    def info(self, entry: LogEntry) -> LogReference: ...
```

### Logging configuration in `main.py`, not in infrastructure

The `_open_gui()` function in `presentation/main.py` is the composition root — it already configures logging with `NullHandler`. This is the right place to configure the real handlers. The `PythonLogAdapter` does not configure logging; it receives a pre-configured `logging.Logger`.

```python
def _configure_logging():
    log_dir = Path.home() / ".flowscope" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handlers = [
        RotatingFileHandler(log_dir / "flowscope.log", maxBytes=1_000_000, backupCount=3),
    ]
    system = platform.system()
    if system in ("Linux", "Darwin"):
        try:
            handlers.append(SysLogHandler(address="/dev/log" if system == "Linux" else "/var/run/syslog"))
        except OSError:
            pass
    elif system == "Windows":
        try:
            from logging.handlers import NTEventLogHandler
            handlers.append(NTEventLogHandler("FlowScope"))
        except ImportError:
            pass
    logging.basicConfig(level=logging.WARNING, handlers=handlers, force=True)
```

### Injection point: controller, not use cases

The `LogPort` is injected into `FlowScopeController`, not into individual use cases. Rationale: the controller already has `except Exception` blocks that catch all technical errors — this is the single chokepoint. If a use case later needs to log something domain-specific, `LogPort` can be injected there as well. But today, all errors flow through the controller.

```python
class FlowScopeController:
    def __init__(
        self,
        guard: OperationGuard,
        load_portfolio: LoadIndexPortfolioUseCase,
        analyze: AnalyzeTickersUseCase,
        presenter: FlowScopePresenter,
        logger: LogPort,                            # NEW
    ):
        self._logger = logger
```

### Status bar message: single unified message, not platform-specific

Alternative considered: different messages per platform ("Veja o syslog", "Veja o Visualizador de Eventos"). Rejected because:
- Users may not know their platform's log viewer name
- The status bar is small — a long message gets truncated
- All platforms have a file fallback anyway

Final approach: a single short message pointing to the file log. The OS-native handlers are a bonus; the file `~/.flowscope/logs/flowscope.log` is guaranteed.

```python
def on_technical_error(self, error: Exception, ref: LogReference) -> None:
    self._view.set_status(
        "⚠ Erro técnico. Consulte o arquivo de log em "
        "~/.flowscope/logs/flowscope.log",
    )
```

### No `NullHandler` removal — just overriding it

The current `logging.basicConfig(handlers=[NullHandler()], force=True)` will be replaced by the real config. No need to remove the NullHandler import — just don't use it.

## Risks / Trade-offs

- **`NTEventLogHandler` requires `pywin32`** → `try/except ImportError` swallows the missing dependency gracefully; logging falls back to file. The user sees no difference. Can be documented in README as optional Windows enhancement.
- **`SysLogHandler` may fail on macOS without syslogd** → The `try/except OSError` catches it. File log is always available.
- **Log file in `~/.flowscope/logs/` may grow** → `RotatingFileHandler` with 3 backups of 1MB caps it at ~3MB. More than enough for a desktop app used daily.
- **User may not find `~/.flowscope/logs/`** → The status bar message shows the exact path. Future enhancement could add a "Open log folder" button.
- **Existing bare `except Exception` in `app.py` bypass the controller** → These are outside this change's scope. They'll continue swallowing silently. A separate change should address them.
