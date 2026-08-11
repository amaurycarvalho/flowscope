## 1. Implement Timestamped Log Format

- [x] 1.1 Add a `logging.Formatter` subclass in `src/flowscope/presentation/main.py` that overrides `formatTime()` to emit `YYYY-MM-DD HH:MM:SS,mmm` (ISO 8601 with 3-digit milliseconds)
- [x] 1.2 Update `_configure_logging()` to pass `format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"` and the custom formatter to `logging.basicConfig` (or to each handler), keeping `force=True`
- [x] 1.3 Verify the format applies globally to the rotating file handler and platform-specific handlers (syslog, NT Event Log)

## 2. Update Tests

- [x] 2.1 Add/adjust a test asserting that a line written to `flowscope.log` starts with a timestamp matching `\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}`
- [x] 2.2 Update existing logging tests in `tests/test_presentation/test_main.py` (e.g., `test_escreve_mensagem_no_arquivo`) if they assert on the default log format
- [x] 2.3 Run the test suite and confirm all logging tests pass
