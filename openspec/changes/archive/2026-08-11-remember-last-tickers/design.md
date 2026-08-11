## Context

The GUI (`FlowScopeGUI` in `src/flowscope/presentation/gui/app.py`) persists UI state in `~/.flowscope/config.json` via `load_preferences()` / `save_preferences()` and a `DEFAULT_CONFIG` dict. The ticker list lives in the `TickerList` widget (`ticker_list.py`) as a `Listbox`, populated by `set_tickers()` (which also selects all and syncs the edit-text). The app currently starts with an empty listbox and only saves window/date/tab state on close.

## Goals / Non-Goals

**Goals:**
- Restore the last-used ticker list at startup without triggering downloads.
- Persist the list on close and on in-session changes (load-from-file / directory change).
- Leave the listbox blank when there is no prior list.
- Show a sensible counter (`Tickers (N)`) after restore.
- Unit tests for the preference read/write helpers.

**Non-Goals:**
- Auto-downloading data for the restored list.
- Persisting list *selection* state (only the set of tickers).
- Changing the config file location or format.

## Decisions

### Decision: Store tickers in `config.json` under a new key
Add `"last_tickers": None` to `DEFAULT_CONFIG`. Persist as a JSON array of ticker strings. This matches the existing single-config pattern (`last_date`, `last_ticker_dir`) and needs no new files or migration.

Alternative considered: a separate `~/.flowscope/last_tickers.txt` — rejected because it duplicates the persistence mechanism and splits UI state across two files for no benefit.

### Decision: Save on close and on in-session change
- In `_on_close()`: store `self._prefs["last_tickers"] = self._ticker_list.get_all_listbox_tickers()` before `save_preferences(self._prefs)`.
- On change paths (`_on_ticker_dir_changed` and the load-from-file callback in `TickerList._load`), also refresh `last_tickers`. `_on_ticker_dir_changed` already calls `save_preferences`; extend it to write the current list. For the file-load path, persist via the same `on_dir_changed` callback (already invoked after a successful load), keeping the change localized to `app.py`.

Rationale: close-time save is the explicit requirement; change-time save adds crash resilience at near-zero cost.

### Decision: Restore before wiring controller
In `__init__`, after `_build_main_area()` and before `_wire_controller()`, populate the listbox from `self._prefs.get("last_tickers")` (filtering to non-empty strings) using `self._ticker_list.set_tickers(...)`. Because callbacks are not yet bound, `set_tickers`' internal selection won't fire `on_ticker_edit`, so no download or IDIV fallback happens.

### Decision: Counter shows total at startup
After restore, call a small counter update that shows `Tickers (N)` when `_current_data` is empty. Reuse `_update_ticker_counter()` logic but guard the "Exibindo X de Y" branch: when there is no loaded data yet, show the total count. Simplest approach: extend `_update_ticker_counter()` to treat an empty `_current_data` as "not yet filtered" and print `Tickers (N)`.

## Risks / Trade-offs

- [Restoring the list might confuse users expecting data to load] → Intended: restore is list-only; the user still clicks "Carregar".
- [Crash between change and close still loses list] → Mitigated by saving on change; an abrupt process kill (SIGKILL) can still lose the last few seconds of edits.
- [Config grows with very large lists] → Negligible: a JSON array of ticker strings is tiny.
- [Corrupt/non-list `last_tickers` in config] → `load_preferences` already falls back to defaults on JSON errors; additionally guard the restore with a type check so a non-list value yields a blank list.

## Migration Plan

No schema migration: new key is additive; existing `config.json` files continue to work and simply lack `last_tickers` (restored as blank).

## Open Questions

None.
