## Why

The `refactor-loading-architecture` change introduced new files (`FlowScopeController`, `FlowScopePresenter`, `OperationGuard`, `LoadIndexPortfolioUseCase`) and modified button state logic in `FlowScopeGUI`, but zero tests were added for these new/modified components. A bug in `controller.py` — passing `reporter.advance` directly instead of wrapping it — escaped into production because the orchestration layer has no test coverage.

## What Changes

- **New**: Unit tests for `FlowScopeController.on_index_clicked()` and `on_load_data()` with mocked dependencies
- **New**: Unit tests for `FlowScopeController._make_progress_cb()` closure
- **New**: Unit tests for `FlowScopePresenter` (requires extracting a `GUIView` protocol to break Tkinter dependency)
- **New**: Unit tests for `OperationGuard.is_busy` property
- **New**: Unit test verifying `LoadIndexPortfolioUseCase.execute()` forwards `progress_callback`
- **New**: Unit tests for `FlowScopeGUI._disable_all_buttons()` and `_restore_all_buttons()` (with Tkinter headless)
- **Refactor**: `FlowScopePresenter` depends on `GUIView` protocol instead of concrete `FlowScopeGUI`
- **Modified**: `FlowScopeGUI` implements `GUIView` protocol

## Capabilities

### New Capabilities
- `presentation-test-coverage`: Unit tests for the GUI controller, presenter, button state management, and new application-layer components

### Modified Capabilities
- *(no requirement changes — only adding tests)*

## Impact

- `src/flowscope/presentation/gui/presenter.py` — refactored to accept `GUIView` protocol instead of concrete `FlowScopeGUI`
- `src/flowscope/presentation/gui/app.py` — `FlowScopeGUI` implements `GUIView` protocol (structural typing, no runtime change)
- `tests/test_presentation/` — new test files: `test_controller.py`, `test_presenter.py`, `test_operation_guard.py`, `test_button_state.py`
- `tests/test_application/` — updated: `test_load_portfolio.py` gains `progress_callback` test
