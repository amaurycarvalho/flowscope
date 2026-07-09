## Why

The index buttons (IBOV, IFIX, IDIV) do not disable other buttons during portfolio download and data processing, allowing concurrent clicks that can trigger overlapping operations. The root cause is architectural: `_fill_with_index()` bypasses the application layer to call the repository directly, and there is no mechanism to prevent concurrent operations. This change fixes the behavior and closes the architectural gap.

## What Changes

- **New**: `LoadIndexPortfolioUseCase` — application-layer use case for loading index portfolio tickers, so the GUI no longer talks to the repository directly
- **New**: `OperationGuard` — a context manager in the application layer that prevents concurrent operations, ensuring atomic button-to-chart flows
- **New**: `FlowScopeController` — extracts orchestration logic from `FlowScopeGUI` into a separate controller class in the adapter layer
- **New**: `FlowScopePresenter` — extracts UI update logic from `FlowScopeGUI` into a separate presenter class
- **Refactor**: `DataRepository` port gains `get_index_tickers()` to close the current protocol gap
- **Behavior**: all buttons (index buttons, load, save, edit, select-all, deselect-all) disable during the full portfolio + analysis pipeline and restore to their previous states on completion
- **Removed**: `_fill_with_index()` and `_ensure_tickers()` from `FlowScopeGUI` — orchestration moves to the controller

## Capabilities

### New Capabilities
- `loading-state-management`: Behavior and architecture for disabling all buttons during portfolio download and data processing, with automatic restoration of previous states

### Modified Capabilities
- `gui-interface`: The index buttons requirement is updated to specify that all buttons shall be disabled during processing and restored on completion

## Impact

- `src/flowscope/application/ports.py` — `DataRepository` port gains `get_index_tickers()`
- `src/flowscope/application/` — new files: `load_portfolio_use_case.py`, `operation_guard.py`
- `src/flowscope/presentation/gui/` — new files: `controller.py`, `presenter.py`
- `src/flowscope/presentation/gui/app.py` — significant refactor: `FlowScopeGUI` becomes a pure view, orchestration extracted
- `src/flowscope/presentation/gui/widgets/ticker_list.py` — minor: `rebind()` method added for late callback wiring
- `openspec/specs/gui-interface/spec.md` — delta spec for index button loading state
