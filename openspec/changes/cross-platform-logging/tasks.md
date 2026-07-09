## 1. Application Layer — LogPort

- [ ] 1.1 Create `application/logging_port.py` with `LogEntry` and `LogReference` dataclasses and `LogPort` Protocol

## 2. Infrastructure Layer — PythonLogAdapter

- [ ] 2.1 Create `infrastructure/logging/__init__.py` (empty)
- [ ] 2.2 Create `infrastructure/logging/python_log_adapter.py` implementing `LogPort` via stdlib `logging.Logger`

## 3. Presentation Layer — Logging Configuration

- [ ] 3.1 Replace `NullHandler` in `presentation/main.py` with real handlers: `RotatingFileHandler` + platform-detected `SysLogHandler` or `NTEventLogHandler`

## 4. Presentation Layer — Controller Integration

- [ ] 4.1 Add `logger: LogPort` parameter to `FlowScopeController.__init__`
- [ ] 4.2 Call `self._logger.error()` in `on_index_clicked()` `except Exception` block before presenter call
- [ ] 4.3 Call `self._logger.error()` in `on_load_data()` `except Exception` block before presenter call
- [ ] 4.4 Remove `except PortfolioNotFoundError` block from `on_load_data()` technical error handling (it's already handled above the general except)

## 5. Presentation Layer — Presenter Integration

- [ ] 5.1 Add `on_technical_error(error, ref)` method to `FlowScopePresenter` with guided log file message

## 6. Presentation Layer — Composition Root

- [ ] 6.1 Wire `PythonLogAdapter` in `app.py:_wire_controller()` and pass to controller
- [ ] 6.2 Verify `main.py` `_configure_logging()` is called before GUI starts

## 7. Verification

- [ ] 7.1 Run existing test suite to confirm no regressions
- [ ] 7.2 Launch application and verify log file is created at `~/.flowscope/logs/flowscope.log`
- [ ] 7.3 Trigger a technical error and verify status bar shows guided message
- [ ] 7.4 Verify `PortfolioNotFoundError` still shows domain-specific message without logging
