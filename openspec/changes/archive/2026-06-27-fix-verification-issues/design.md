## Context

The `core-implementation` change delivered all features but a verification audit found 7 issues: 1 critical (ticker flag not wired to export), 5 warnings (missing CSV columns, quiver stub, no auto-refresh on ticker edit/load), and 1 suggestion (non-Linux exit code). All fixes are local to existing modules — no architectural changes needed.

## Goals / Non-Goals

**Goals:**
- Wire `--tickers` flag to `--vwap`/`--cvd` export in `main.py`
- Add daily date columns to VWAP and CVD CSV exports
- Implement quiver arrows in the scatter plot
- Auto-refresh charts when user edits or loads ticker list
- Change `--create-shortcut` non-Linux exit code to 0

**Non-Goals:**
- No new capabilities, dependencies, or architectural changes
- No redesign of existing modules — only targeted fixes

## Decisions

### 1. CSV export: include daily columns

**Approach**: `ExportVWAPUseCase` and `ExportCVDUseCase` already compute `daily_vwap` and `daily_cvd` dicts. The sorted date keys from these dicts become CSV column headers. Output format:

```
Ticker;VWAP_Periodo;2026-06-25;2026-06-24;2026-06-23
PETR4;28.60;28.80;28.40;
VALE3;62.50;;62.80
```

### 2. Chart refresh on ticker edit

**Approach**: Bind `<KeyRelease>` on the `tk.Text` widget to a callback provided by `FlowScopeGUI`. The same callback is called by "Carregar Tickers" after loading. `TickerList` accepts an `on_change` callback parameter.

### 3. Quiver arrows

**Approach**: `matplotlib.pyplot.quiver` is not suited for this use case (each point needs a directed arrow to its previous position). Use `matplotlib.pyplot.annotate` with `arrowprops` or individual `matplotlib.patches.FancyArrowPatch` for each ticker, connecting its d-1 → d VWAP×CVD coordinates. Data structure: for each ticker, compute VWAP and CVD for the two most recent consecutive dates in the window.

## Risks / Trade-offs

- **[Risk] Missing daily data for a ticker in d-1** → If a ticker has data in d but not in d-1, skip the arrow for that ticker. Don't fail.
- **[Risk] Quiver with many tickers (15+) may clutter** → Acceptable for a 15-ticker default. If performance is an issue, can be optimized later.
