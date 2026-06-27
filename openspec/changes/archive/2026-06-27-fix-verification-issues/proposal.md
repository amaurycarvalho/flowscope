## Why

A verification audit of the `core-implementation` change found 1 critical, 5 warnings, and 1 suggestion issues across the CLI, GUI, and chart modules. These must be fixed to align implementation with spec requirements before the change can be archived.

## What Changes

- **CLI export**: Wire `--tickers` flag to `--vwap`/`--cvd` export paths so `flowscope --vwap --tickers lista.txt` filters by the provided tickers
- **CSV export columns**: Add daily VWAP/CVD columns to CSV export output (one column per window date)
- **Quiver arrows**: Implement temporal arrow visualization connecting each ticker's d-1 → d position in the scatter plot
- **Auto-refresh on edit**: Trigger chart refresh when user edits the ticker list text field
- **Ticker load refresh**: Trigger chart refresh after loading tickers from a `.txt` file
- **Non-Linux exit code**: Change `--create-shortcut` on non-Linux to exit with code 0 instead of 1

## Capabilities

### New Capabilities

*(none — all changes modify existing capabilities)*

### Modified Capabilities

- `cli-interface`: Add ticker filtering to VWAP/CVD export; add daily date columns to CSV output
- `gui-interface`: Implement quiver arrows in scatter plot; auto-refresh charts on ticker field edit and load
- `desktop-shortcut`: Exit with code 0 (instead of 1) on non-Linux platforms

## Impact

- **src/flowscope/presentation/main.py**: `_export()` signature and dispatch; `_create_desktop_shortcut()` exit code
- **src/flowscope/application/use_cases.py**: `ExportVWAPUseCase.execute()` and `ExportCVDUseCase.execute()` output format
- **src/flowscope/presentation/gui/charts/scatter.py**: `_draw_quiver()` implementation
- **src/flowscope/presentation/gui/app.py**: Ticker list → chart refresh wiring
- **src/flowscope/presentation/gui/widgets/ticker_list.py**: Load callback propagation
