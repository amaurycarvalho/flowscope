## ADDED Requirements

### Requirement: Technical errors are logged to OS-native facilities

When a technical error occurs during data loading or analysis, the system SHALL record the error details to the operating system's native logging facility (syslog on Linux/macOS, Event Log on Windows) AND to a rotating file at `~/.flowscope/logs/flowscope.log`.

Each log entry MUST contain: timestamp, error level, component name, exception message, and stack trace (when available).

#### Scenario: HTTP error during portfolio fetch is logged to syslog (Linux)
- **WHEN** `B3Client.fetch_portfolio()` raises a `RuntimeError` due to HTTP 500
- **THEN** the error is recorded via `SysLogHandler` with level `ERROR` and component `"B3Client.fetch_portfolio"`
- **AND** the same error is recorded in `~/.flowscope/logs/flowscope.log`

#### Scenario: HTTP error during portfolio fetch is logged to Event Log (Windows)
- **WHEN** `B3Client.fetch_portfolio()` raises a `RuntimeError` due to HTTP 500
- **THEN** the error is recorded via `NTEventLogHandler` with source `"FlowScope"` and level `EVENTLOG_ERROR_TYPE`

#### Scenario: OS-native handler unavailable falls back to file logging
- **WHEN** `SysLogHandler` constructor raises `OSError` (e.g., `/dev/log` does not exist)
- **THEN** the error is logged only to `~/.flowscope/logs/flowscope.log`
- **AND** the application continues to operate normally without crashing

### Requirement: Status bar guides user to log file on technical error

When a technical error occurs and is logged, the status bar SHALL display a message indicating that the error details are available in the log file at `~/.flowscope/logs/flowscope.log`.

Domain-level errors (e.g., `PortfolioNotFoundError`, `InvalidIndexError`) MUST continue to display their existing status bar messages and MUST NOT trigger the technical error flow.

#### Scenario: Technical error shows guided message in status bar
- **WHEN** an unexpected `Exception` is raised during `on_index_clicked()` or `on_load_data()`
- **THEN** the status bar displays `"⚠ Erro técnico. Consulte o arquivo de log em ~/.flowscope/logs/flowscope.log"`

#### Scenario: Domain error does not trigger technical error message
- **WHEN** a `PortfolioNotFoundError` is raised during `on_load_data()`
- **THEN** the status bar displays the existing domain-specific message
- **AND** no entry is written to the log

### Requirement: Log level is configurable to WARNING by default

The logging configuration SHALL set the default level to `WARNING`. This means `logger.info()` and `logger.debug()` messages are suppressed by default, while `logger.warning()` and `logger.error()` messages are recorded.

#### Scenario: Info messages are suppressed at default config
- **WHEN** `B3Client` logs `"Fetching portfolio %s via %s"` at `INFO` level
- **THEN** the message does NOT appear in any log output

#### Scenario: Error messages are recorded at default config
- **WHEN** `B3Client` logs `"Failed to fetch portfolio %s: %s"` at `ERROR` level
- **THEN** the message appears in `~/.flowscope/logs/flowscope.log`

### Requirement: Log file is managed with rotation

The file log SHALL use `RotatingFileHandler` with a maximum file size of 1MB and up to 3 backup files. Older log files SHALL be named `flowscope.log.1`, `flowscope.log.2`, `flowscope.log.3`.

#### Scenario: Log rotation preserves recent entries
- **WHEN** `~/.flowscope/logs/flowscope.log` exceeds 1MB
- **THEN** the file is renamed to `flowscope.log.1`
- **AND** a new `flowscope.log` is created for subsequent entries
