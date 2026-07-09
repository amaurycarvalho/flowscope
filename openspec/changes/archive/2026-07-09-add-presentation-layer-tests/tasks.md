## 1. Refactor Presenter with GUIView Protocol

- [x] 1.1 Define `GUIView` protocol class in `presenter.py` with methods: `disable_all_buttons`, `restore_all_buttons`, `set_wait_cursor`, `clear_wait_cursor`, `set_progress`, `set_status`, `get_reference_date`, `get_current_tickers`, `set_tickers`, `set_counter`, `config_copy_button_state`, `on_tab_changed`
- [x] 1.2 Update `FlowScopePresenter.__init__` to accept `GUIView` instead of `FlowScopeGUI`
- [x] 1.3 Ensure `FlowScopeGUI` structurally matches `GUIView` (add missing public methods if needed)

## 2. Test `_make_progress_cb`

- [x] 2.1 Create `tests/test_presentation/test_controller.py` with test class
- [x] 2.2 Test that callback with `failed=False` calls `reporter.advance(1, detail)`
- [x] 2.3 Test that callback with `failed=True` calls `reporter.fail(1, detail)`

## 3. Test `FlowScopeController.on_index_clicked`

- [x] 3.1 Create test that verifies success path: guard acquired, presenter receives `on_operation_started` → `on_portfolio_loaded` → `on_result` → `on_operation_finished` in order
- [x] 3.2 Create test that verifies guard blocks second concurrent click
- [x] 3.3 Create test that verifies `PortfolioNotFoundError` calls `on_operation_finished` without `on_result`
- [x] 3.4 Create test that verifies generic exception calls `on_error` + `on_operation_finished`

## 4. Test `FlowScopeController.on_load_data`

- [x] 4.1 Create test for success path with existing tickers
- [x] 4.2 Create test for success path with empty tickers (triggers IDIV fallback)
- [x] 4.3 Create test for `PortfolioNotFoundError` when IDIV fallback fails
- [x] 4.4 Create test for guard protecting concurrent calls

## 5. Test `FlowScopePresenter` with mock GUIView

- [x] 5.1 Create `tests/test_presentation/test_presenter.py`
- [x] 5.2 Test `on_operation_started()` calls `disable_all_buttons` + `set_wait_cursor` on view
- [x] 5.3 Test `on_operation_finished()` calls `restore_all_buttons` + `clear_wait_cursor` + clears progress bar
- [x] 5.4 Test `on_progress(current, total, label)` delegates to `set_progress` on view
- [x] 5.5 Test `on_result()` sets copy button NORMAL, updates counter, date label, calls `on_tab_changed` + `set_status`
- [x] 5.6 Test `on_error()` calls `set_status` with error message
- [x] 5.7 Test `get_reference_date()` reads from view
- [x] 5.8 Test `get_current_tickers()` reads from view

## 6. Test `_disable_all_buttons` and `_restore_all_buttons`

- [x] 6.1 Create `tests/test_presentation/test_button_state.py` with Tk headless
- [x] 6.2 Build minimal `FlowScopeGUI` or test with standalone Tk root + real buttons
- [x] 6.3 Test `_disable_all_buttons` saves snapshot and disables all buttons
- [x] 6.4 Test `_restore_all_buttons` restores to previous states (including copy button that started DISABLED)

## 7. Cover remaining gaps in Application Layer

- [x] 7.1 Add test for `OperationGuard.is_busy` property to `tests/test_application/test_operation_guard.py`
- [x] 7.2 Add test verifying `LoadIndexPortfolioUseCase.execute()` forwards `progress_callback` to repository
- [x] 7.3 Add `_gui` property alias on `FlowScopePresenter` for backward compatibility
- [x] 7.4 Add tests for `on_today()` and `on_ticker_edit()` to prevent `_gui` AttributeError regression
