## Context

`_configure_logging()` in `src/flowscope/presentation/main.py` calls `logging.basicConfig(level=logging.WARNING, handlers=handlers, force=True)` without a `format`, so the default `%(levelname)s:%(name)s:%(message)s` is used. `flowscope.log` lines therefore carry no date/time. The `logging` capability does not exist yet in `openspec/specs/`; this change introduces it.

## Goals / Non-Goals

**Goals:**
- Every line in `flowscope.log` starts with an ISO 8601 timestamp including milliseconds.
- Single global format configured once in `_configure_logging()` via `basicConfig` (applies to the rotating file handler and platform handlers alike).

**Non-Goals:**
- Per-handler formats (e.g., different format for syslog vs file).
- Structured logging (JSON), log levels change, or rotation policy changes.

## Decisions

### Decision: Configure format via `logging.basicConfig`
Use `format` and `datefmt` arguments of `logging.basicConfig`:

```python
logging.basicConfig(
    level=logging.WARNING,
    handlers=handlers,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S,%f",
    force=True,
)
```

- `%(asctime)s` is replaced by the timestamp; `datefmt` controls its representation.
- `%f` produces milliseconds. Note: Python formats `%f` as 6 digits (microseconds), so to show 3-digit milliseconds the trailing digits are trimmed via a custom `Formatter` subclass with `formatTime()` — this is a known Python logging limitation.
- Alternative considered: `time.strftime` + `%f` truncation inside a `logging.Formatter` subclass. This is the cleaner approach and is **selected**; alternative (leaving 6-digit microseconds or using `time.time()` in the message) was rejected for non-standard or noisy output.

Rationale for `basicConfig` scope: the user explicitly scoped this via `basicConfig`, all handlers share the format, and no handler needs a distinct layout.

### Decision: Formatter emits millisecond-precision timestamps
Implement a small `Formatter` subclass that overrides `formatTime()` to produce `YYYY-MM-DD HH:MM:SS,mmm` (3-digit milliseconds, comma separator), matching ISO 8601 fraction convention. This keeps the format ISO-compliant and human-readable.

Alternative considered: relying on default `asctime` (no ms) — rejected because milliseconds were explicitly requested.

## Risks / Trade-offs

- [Milliseconds via `%f` default to 6 digits] → Custom `formatTime()` truncates to 3 digits; covered by a unit test.
- [Existing tests assert on default log output] → Update assertions in `tests/test_presentation/test_main.py` (and any other logging tests) to the new format.
- [Global format also affects syslog/Event Log handlers] → Accepted: consistent behavior, non-goal to differentiate per handler.
