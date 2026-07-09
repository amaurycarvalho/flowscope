## 1. Application Layer — LogPort

- [x] 1.1 Create `application/logging_port.py` with `LogEntry` and `LogReference` dataclasses and `LogPort` Protocol

## 2. Infrastructure Layer — PythonLogAdapter

- [x] 2.1 Create `infrastructure/logging/__init__.py` (empty)
- [x] 2.2 Create `infrastructure/logging/python_log_adapter.py` implementing `LogPort` via stdlib `logging.Logger`

## 3. Presentation Layer — Logging Configuration

- [x] 3.1 Replace `NullHandler` in `presentation/main.py` with real handlers: `RotatingFileHandler` + platform-detected `SysLogHandler` or `NTEventLogHandler`

## 4. Presentation Layer — Controller Integration

- [x] 4.1 Add `logger: LogPort` parameter to `FlowScopeController.__init__`
- [x] 4.2 Call `self._logger.error()` in `on_index_clicked()` `except Exception` block before presenter call
- [x] 4.3 Call `self._logger.error()` in `on_load_data()` `except Exception` block before presenter call
- [ ] ~~4.4 Remove `except PortfolioNotFoundError` block from `on_load_data()` — kept as-is per spec requirement that domain errors retain their existing handling~~

## 5. Presentation Layer — Presenter Integration

- [x] 5.1 Add `on_technical_error(error, ref)` method to `FlowScopePresenter` with guided log file message

## 6. Presentation Layer — Composition Root

- [x] 6.1 Wire `PythonLogAdapter` in `app.py:_wire_controller()` and pass to controller
- [x] 6.2 Verify `main.py` `_configure_logging()` is called before GUI starts

## 7. Verification

- [x] 7.1 Run existing test suite to confirm no regressions
- [x] 7.2 Launch application and verify log file is created at `~/.flowscope/logs/flowscope.log`
- [x] 7.3 Trigger a technical error and verify status bar shows guided message
- [x] 7.4 Verify `PortfolioNotFoundError` still shows domain-specific message without logging

## 8. Tests

- [x] 8.1 Create `tests/test_application/test_logging_port.py` — dataclass creation, immutability, Protocol acceptance
- [x] 8.2 Create `tests/test_infrastructure/test_python_log_adapter.py` — levels, exception stack, real handler output
- [x] 8.3 Add `test_on_technical_error` to `tests/test_presentation/test_presenter.py`
- [x] 8.4 Add `TestConfigureLogging` to `tests/test_presentation/test_main.py` — dir creation, file writing, platform handlers, syslog fallback
