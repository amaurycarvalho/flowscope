## ADDED Requirements

### Requirement: Log records include timestamp
The system SHALL include a timestamp with date and time in every log record written to the `flowscope.log` file.

#### Scenario: Log record contains timestamp
- **WHEN** any log record is written to `flowscope.log`
- **THEN** the record line SHALL start with a timestamp in ISO 8601 format (YYYY-MM-DD HH:MM:SS,mmm) including milliseconds

### Requirement: Timestamp format configured globally
The timestamp format SHALL be configured via the `format`/`datefmt` arguments of `logging.basicConfig`, applying to all log handlers used by the application.

#### Scenario: Format applies to all handlers
- **WHEN** the application configures logging in `_configure_logging()`
- **THEN** the single format string defined for `logging.basicConfig` is used by the rotating file handler and any platform-specific handlers (syslog, NT Event Log)
