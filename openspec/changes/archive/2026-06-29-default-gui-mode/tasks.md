## 1. Modify dispatch logic in main()

- [x] 1.1 Refactor `main()` to detect "no CLI args" and default to GUI — wrap existing CLI path under `has_cli_args` check and fall through to `_open_gui()` otherwise

## 2. Verify

- [x] 2.1 Run `flowscope` (no args) — confirms GUI opens
- [x] 2.2 Run `flowscope --gui` — confirms explicit flag still works
- [x] 2.3 Run `flowscope --version` — confirms meta flag unaffected
- [x] 2.4 Run `flowscope --tickers nonexistent.txt` — confirms CLI mode still works (error expected)
