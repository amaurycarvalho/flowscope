## 1. CLI Export — Ticker Filter and Daily Columns

- [x] 1.1 In `presentation/main.py`, modify `_export()` to accept tickers from `args.tickers` and pass to use case
- [x] 1.2 In `application/use_cases.py`, add daily VWAP date columns to CSV output (sorted dates as headers, values per ticker)
- [x] 1.3 In `application/use_cases.py`, add daily CVD date columns to CSV output (sorted dates as headers, values per ticker)

## 2. GUI — Quiver Arrows in Scatter Plot

- [x] 2.1 In `presentation/gui/charts/scatter.py`, implement `_draw_quiver()` using matplotlib annotations/patches to draw arrows connecting d-1 → d for each ticker

## 3. GUI — Auto-refresh Charts on Ticker Edit/Load

- [x] 3.1 In `presentation/gui/widgets/ticker_list.py`, add `on_change` callback parameter and bind `<KeyRelease>` on Text widget
- [x] 3.2 In `presentation/gui/app.py`, pass chart refresh callback to TickerList and wire KeyRelease → refresh
- [x] 3.3 In `presentation/gui/widgets/ticker_list.py`, trigger callback after "Carregar Tickers" loads new content

## 4. Desktop Shortcut — Exit Code on Non-Linux

- [x] 4.1 In `presentation/main.py`, change `sys.exit(1)` to `sys.exit(0)` in `_create_desktop_shortcut()` for non-Linux branch

## 5. Tests

- [x] 5.1 Add tests for export with ticker filter (CLI and use case level)
- [x] 5.2 Add tests for export output format with daily columns
