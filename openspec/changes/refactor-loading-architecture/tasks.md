## 1. Port and Application Layer

- [x] 1.1 Add `get_index_tickers(index, progress_callback)` to `DataRepository` protocol in `application/ports.py`
- [x] 1.2 Create `OperationGuard` with `@contextmanager acquire()` in `application/operation_guard.py`
- [x] 1.3 Create `LoadIndexPortfolioUseCase` in `application/load_portfolio_use_case.py` — `execute(index, progress_callback)` returns `list[str]`, raises on empty result

## 2. Presenter

- [x] 2.1 Create `FlowScopePresenter` in `presentation/gui/presenter.py` with methods: `on_operation_started()`, `on_operation_finished()`, `on_portfolio_loaded(tickers)`, `on_progress(current, total, label)`, `on_result(result, tickers, ref_date)`, `on_error(exception)`, `get_reference_date()`, `get_current_tickers()`

## 3. Controller

- [x] 3.1 Create `FlowScopeController` in `presentation/gui/controller.py` — receives `guard`, `load_portfolio`, `analyze`, `presenter`; implements `on_index_clicked(index)`, `on_load_data()`, `on_today()`, `on_ticker_edit()`; creates `ProgressReporter` and manages phase lifecycle; wraps everything in `guard.acquire()`

## 4. View Refactor (FlowScopeGUI)

- [x] 4.1 Add `_disable_all_buttons()` and `_restore_all_buttons()` to `FlowScopeGUI` using snapshot pattern (`dict[tk.Widget, str]`)
- [x] 4.2 Remove `_fill_with_index()`, `_ensure_tickers()`, `_enter_loading_state()`, `_exit_loading_state()` from `FlowScopeGUI`
- [x] 4.3 Add `_wire_controller()` method to `FlowScopeGUI` — creates all dependencies and wires callbacks
- [x] 4.4 Update `_build_top_bar()` and `_build_main_area()` to defer callback wiring to `_wire_controller()`

## 5. TickerList Widget

- [x] 5.1 Add `_callbacks` dict to `TickerList.__init__()` to store all callbacks
- [x] 5.2 Add `rebind(**callbacks)` method to `TickerList` for late callback wiring
- [x] 5.3 Update all internal button `command=` references to use `self._callbacks`

## 6. Verification

- [x] 6.1 Run tests — 160 passed, 0 failed
- [x] 6.2 Verify manually: click IBOV → all buttons disable → restore on completion; click IBOV twice → second click ignored (manual)
