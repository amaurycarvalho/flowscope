## Why

The `flowscope.log` file is written with the default Python logging format, which does not include date/time. When debugging issues (e.g., the "Failed to fetch portfolio IDIV" error), there is no way to know *when* an event happened, which hinders correlating logs with actions or crashes.

## What Changes

- Configure `logging.basicConfig` in `src/flowscope/presentation/main.py` with a log format that includes a timestamp.
- Timestamps use ISO 8601 format **with milliseconds** (e.g., `2026-08-11 14:23:07,120`).
- The format applies globally to all handlers via `basicConfig` (single `format` for the whole process).
- Adjust existing logging tests to match the new format if they assert on log output.

## Capabilities

### New Capabilities
- `logging`: Controls how FlowScope emits log records, including the timestamped log line format used by the file handler.

### Modified Capabilities
<!-- No existing spec-level behavior changes. -->

## Impact

- `src/flowscope/presentation/main.py` — `_configure_logging()`: add `format`/`datefmt` to `logging.basicConfig`.
- `tests/test_presentation/test_main.py` — logging-related assertions may need updates to match the new format.
- Log consumers (syslog on Linux/macOS, NT Event Log on Windows) are unaffected beyond the shared format string.
