## Context

The `FlowScopeGUI` class currently plays three roles: composition root (wires dependencies), controller (orchestrates operations), and view (manages widgets). `_fill_with_index()` calls `B3DataRepository.get_index_tickers()` directly, bypassing the application layer entirely. The `DataRepository` port is missing `get_index_tickers`. `_enter_loading_state()` only disables three widgets (load button, today button, date entry) — index buttons and all TickerList buttons remain active during processing. There is no mechanism to prevent concurrent operations.

## Goals / Non-Goals

**Goals:**
- Extract `LoadIndexPortfolioUseCase` so portfolio loading goes through the application layer
- Create `OperationGuard` (context manager) to prevent concurrent operations
- Add `get_index_tickers` to the `DataRepository` port
- Extract orchestration into `FlowScopeController` (adapter layer)
- Extract UI formatting into `FlowScopePresenter` (adapter layer)
- Disable ALL buttons during the full portfolio + analysis pipeline and restore previous states
- Remove `_fill_with_index()` and `_ensure_tickers()` from `FlowScopeGUI`

**Non-Goals:**
- No changes to the domain layer (strategies, engine, entities)
- `AnalyzeTickersUseCase` remains unmodified
- No changes to chart widgets
- No changes to `ProgressReporter` itself (only how it's created and managed)
- No threading or async — the app remains single-thread synchronous

## Decisions

### Decision 1: `OperationGuard` as context manager via `@contextmanager`

**Choice**: `acquire()` yields `True`/`False` and releases on `__exit__`.

**Alternatives considered**: Explicit `acquire()`/`release()` methods; blocking lock; exception on busy.

**Rationale**: Context manager guarantees release even on exceptions. Non-blocking (returns `False`) is correct for single-thread Tkinter — blocking would freeze the event loop. Yield-based pattern lets callers decide how to handle "busy" (return early vs show message).

Result:
```python
@contextmanager
def acquire(self):
    if self._busy:
        yield False
        return
    self._busy = True
    try:
        yield True
    finally:
        self._busy = False
```

### Decision 2: `LoadIndexPortfolioUseCase` as a self-contained use case

**Choice**: New use case class in `application/`, depends on `DataRepository` port (with `get_index_tickers` added).

**Alternatives considered**: Add loading to `AnalyzeTickersUseCase`; keep in GUI but route through port.

**Rationale**: A dedicated use case follows the Single Responsibility Principle, is testable without Tkinter, and matches the existing `AnalyzeTickersUseCase` pattern. The GUI should not know about repositories.

### Decision 3: Controller + Presenter separation in the adapter layer

**Choice**: `FlowScopeController` orchestrates use cases; `FlowScopePresenter` formats for GUI.

**Alternatives considered**: Keep orchestration in `FlowScopeGUI`; merge controller and presenter.

**Rationale**: Separating orchestration from widget updates makes the controller testable. The presenter encapsulates all `tk.Button.config()` calls, `_ticker_list.set_tickers()` calls, and `_set_status()` calls — the view class no longer makes decisions, only executes widget commands.

### Decision 4: Late callback wiring via `TickerList.rebind()`

**Choice**: `TickerList` stores callbacks in a dict; `rebind(**callbacks)` updates them.

**Alternatives considered**: Pass controller to TickerList constructor; build widgets in two passes.

**Rationale**: `TickerList` is created in `_build_main_area()` which runs before the controller exists. Rebinding is simpler than two-pass construction and keeps `TickerList` independent of the controller interface. The callbacks dict pattern is already used internally in `TickerList`.

### Decision 5: `ProgressReporter` stays in the adapter layer

**Choice**: Controller creates `ProgressReporter` and manages phase lifecycle. Use cases receive simple `Callable[[str, bool], None]`.

**Alternatives considered**: Move `ProgressReporter` to application layer; embed phase management in use cases.

**Rationale**: ProgressReporter's throttling, weight calculation, and phase tracking are adapter concerns (presentation policy). Different UIs (CLI, headless) would want different progress formatting. The application layer abstraction remains the simple callback.

### Decision 6: Button state snapshot and restore pattern

**Choice**: `_disable_all_buttons()` saves each button's current state then disables; `_restore_all_buttons()` restores saved states.

**Alternatives considered**: Re-enable all to NORMAL unconditionally; track busy state per button.

**Rationale**: The `_copy_data_btn` starts DISABLED and becomes NORMAL after a successful load. A naive re-enable would incorrectly set it to NORMAL on subsequent operations. Snapshot ensures correct restoration regardless of prior state. Implementation: store `dict[tk.Widget, str]` mapping widget → prior state.

## Risks / Trade-offs

- **[Risk]** `TickerList.rebind()` could be called after callbacks already fired → **Mitigation**: rebind is called once in `_wire_controller()` before any user interaction, during `__init__`.
- **[Risk]** OperationGuard single `_busy` flag protects only one operation at a time → **Intentional**: the entire app is single-thread and non-reentrant. Multiple guards would be overengineering.
- **[Risk]** Controller knows about `ProgressReporter` (adapter class) → **Intentional**: the controller IS in the adapter layer (`presentation/gui/controller.py`), same as `ProgressReporter`.
- **[Risk]** `FlowScopePresenter` knows widget names (`_ticker_list`, `_copy_data_btn`) → **Intentional**: it's in the same layer and same module. Abstracting behind a view interface would add indirection without testability benefit (Tkinter can't be unit-tested anyway).
- **[Trade-off]** Extracting controller/presenter adds ~150 lines of new adapter code → **Benefit**: `FlowScopeGUI` shrinks, each class has one responsibility, orchestration is testable.
