## Why

Every time the app opens, the ticker list starts blank, forcing the user to reload the portfolio or re-type tickers they already used in a previous session. Since `~/.flowscope/config.json` already persists UI state (`last_date`, `last_tab`, `window_geometry`), remembering the last-used ticker list is a natural, low-cost usability improvement.

## What Changes

- Persist the last-used ticker list in `~/.flowscope/config.json` under a new key `last_tickers`.
- On app close, save the current ticker list (`_on_close`).
- Also persist the list when it changes via load-from-file / directory change, so it survives crashes and non-graceful exits.
- On startup, restore the saved list into the ticker listbox **without** triggering any data download.
- If no previous list exists (or the saved list is empty/corrupt), the listbox stays blank.
- Adjust the ticker counter at startup so it shows `Tickers (N)` instead of `Exibindo 0 de N ativos`.
- Add unit tests for `load_preferences` / `save_preferences` covering the `last_tickers` round-trip.

## Capabilities

### New Capabilities
- `ticker-list-persistence`: Persisting and restoring the last-used ticker list across application sessions via the preferences file.

### Modified Capabilities
<!-- No existing spec-level behavior changes. -->

## Impact

- `src/flowscope/presentation/gui/app.py` — `DEFAULT_CONFIG`, `__init__` (restore), `_on_close` (save), `_on_ticker_dir_changed` / load path (save on change), counter adjustment.
- `src/flowscope/presentation/gui/widgets/ticker_list.py` — load-from-file path may persist the list via callback (or via existing `on_dir_changed`).
- `tests/` — new tests for `load_preferences` / `save_preferences`.
