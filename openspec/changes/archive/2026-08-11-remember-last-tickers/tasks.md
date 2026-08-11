## 1. Persistence Layer

- [x] 1.1 Add `"last_tickers": None` to `DEFAULT_CONFIG` in `src/flowscope/presentation/gui/app.py`
- [x] 1.2 Guard `load_preferences`/restore path against a non-list `last_tickers` value (fall back to blank)

## 2. Save on Close

- [x] 2.1 In `_on_close()`, store `self._prefs["last_tickers"] = self._ticker_list.get_all_listbox_tickers()` before `save_preferences(self._prefs)`

## 3. Save on Change

- [x] 3.1 Extend `_on_ticker_dir_changed` to also refresh `last_tickers` with the current ticker list before saving preferences

## 4. Restore on Startup

- [x] 4.1 In `FlowScopeGUI.__init__`, after `_build_main_area()` and before `_wire_controller()`, restore the ticker listbox from `self._prefs.get("last_tickers")` when it is a non-empty list of non-empty strings
- [x] 4.2 Adjust the startup counter so a restored list shows `Tickers (N)` instead of `Exibindo 0 de N ativos` (e.g., guard `_update_ticker_counter` when `_current_data` is empty)

## 5. Tests

- [x] 5.1 Add unit tests for `load_preferences` / `save_preferences` covering `last_tickers` round-trip, missing key (blank), and empty-list persistence
- [x] 5.2 Run `make lint test` and confirm all tests pass
