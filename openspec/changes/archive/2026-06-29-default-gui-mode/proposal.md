## Why

Currently `flowscope` (no arguments) launches the CLI analysis mode, but the primary use case is the GUI. Users must remember `--gui` every time. Making GUI the default removes unnecessary friction and matches the most common workflow.

## What Changes

- `flowscope` (no flags) now opens the GUI instead of running CLI mode
- `--gui` flag is kept for backward compatibility (used by desktop shortcut)
- CLI mode (`--tickers`, `--vwap`, etc.) behavior is unchanged
- `--version` and `--create-shortcut` behavior is unchanged

## Capabilities

### New Capabilities

- `default-gui`: Automatic GUI launch when no CLI-specific arguments are provided

### Modified Capabilities

*(No spec-level requirement changes — the CLI and GUI specs remain unchanged. Only the default dispatch at the entry point is altered.)*

## Impact

- `src/flowscope/presentation/main.py` — dispatch logic in `main()` needs to detect "no CLI args" and default to GUI
- `--gui` flag remains defined in `cli.py` but becomes redundant for normal use (kept for shortcut compatibility)
