## Context

The `refactor-loading-architecture` change added new components (`FlowScopeController`, `FlowScopePresenter`, `OperationGuard`, `LoadIndexPortfolioUseCase`) and modified `FlowScopeGUI._disable_all_buttons()` / `_restore_all_buttons()`. None of these have unit tests. A production bug — `reporter.advance` passed directly as callback with mismatched signature — was not caught because the orchestration layer has zero coverage.

## Goals / Non-Goals

**Goals:**
- Full unit test coverage for `FlowScopeController` (orchestration logic, error handling, guard interaction)
- Full unit test coverage for `FlowScopePresenter` (requires extracting `GUIView` protocol)
- Full unit test coverage for `_disable_all_buttons()` / `_restore_all_buttons()` (with Tkinter headless)
- Coverage for remaining untested paths in `OperationGuard` and `LoadIndexPortfolioUseCase`

**Non-Goals:**
- No changes to business logic (domain strategies, engine, entities remain untouched)
- No integration tests (HTTP calls, real Tkinter event loop)
- No tests for `TickerList.all_buttons()` / `rebind()` (requires complex Tkinter widget setup)

## Decisions

### Decision 1: `GUIView` protocol for testable presenter

**Choice**: Extract `GUIView` protocol class that `FlowScopePresenter` depends on. `FlowScopeGUI` structurally matches it (duck typing via Protocol). Tests inject a `unittest.mock.Mock`.

**Rationale**: Currently `FlowScopePresenter.__init__` takes `FlowScopeGUI` directly, making every method test require Tkinter. A Protocol breaks this dependency without adding a base class or modifying inheritance. The Protocol lives in `presenter.py` alongside the presenter.

```python
class GUIView(Protocol):
    def disable_all_buttons(self) -> None: ...
    def restore_all_buttons(self) -> None: ...
    def set_wait_cursor(self) -> None: ...
    def clear_wait_cursor(self) -> None: ...
    def set_progress(self, current: int, total: int, label: str) -> None: ...
    def set_status(self, msg: str, icon: str) -> None: ...
    ... etc
```

### Decision 2: Controller tests with mocked dependencies

**Choice**: Test `FlowScopeController` by injecting `unittest.mock.Mock` instances for `guard`, `load_portfolio`, `analyze`, and `presenter`. Verify call order and arguments on the presenter mock.

**Rationale**: The controller's only output is calls to presenter + use cases. With mocks, we can assert the exact sequence of presenter calls, which is the orchestration contract.

### Decision 3: `_disable_all_buttons()` tested via `Tk()` headless

**Choice**: Create a `tk.Tk()` instance in test setup, build a minimal widget tree with real `tk.Button` widgets, call `_disable_all_buttons()` and `_restore_all_buttons()`, assert states.

**Rationale**: While Tkinter tests are slow and fragile, these two methods are the core of the button state feature and contain complex logic (snapshot dict, iteration over buttons from GUI + TickerList). Without testing, regressions go unnoticed. Use `tk.Tk()` without `mainloop()`.

### Decision 4: `_make_progress_cb` tested directly with mock reporter

**Choice**: Create a `FlowScopeController`, call `_make_progress_cb(mock_reporter)`, invoke the returned closure with `("detail", True)` and `("detail", False)`, assert `reporter.fail` / `reporter.advance` called correctly.

**Rationale**: This is pure function-like behavior. No mocks needed for guard, portfolio, analyze, or presenter — only a `Mock` reporter.

## Risks / Trade-offs

- **[Risk]** `GUIView` protocol may diverge from `FlowScopeGUI` API over time → **Mitigation**: The protocol is co-located with the presenter. Any change to `FlowScopeGUI` that breaks the protocol will fail type checking immediately.
- **[Risk]** Tkinter headless tests are fragile (display-dependent) → **Mitigation**: Tests use `tk.Tk()` without `mainloop()` and destroy after each test. Can be skipped on CI if display is unavailable via `@pytest.mark.skipif`.
- **[Trade-off]** Not testing `TickerList.all_buttons()` and `rebind()` → **Accepted**: These require a fully constructed `TickerList` widget tree, which is disproportionate effort for the value.
