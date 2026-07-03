## 1. Utility Module

- [x] 1.1 Create `src/flowscope/presentation/gui/charts/empty_state.py` with `create_empty(fig, axes_list)` that adds a `fig.text()` centered "Sem dados" label in light gray and sets `ax.axis("off")` on all axes
- [x] 1.2 Add `show_empty(fig, axes_list, label)` that clears all axes, sets them to `axis("off")`, and makes the label visible
- [x] 1.3 Add `hide_empty(label)` that sets the label invisible

## 2. Single-Axes Charts: VWAPHist, QuadrantChart, DominanceRanking, DominanceTimeline

- [x] 2.1 In each chart's `__init__`, add `self._all_axes = [self._axes]` and call `create_empty(self._figure, self._all_axes)` right after canvas creation
- [x] 2.2 In each chart's `update()` empty data guard, replace `ax.set_title()` + `ax.set_xlim()` with `show_empty(self._figure, self._all_axes, self._empty_label)` + `self._canvas.draw()` + return
- [x] 2.3 In each chart's `update()` data path, add `hide_empty(self._empty_label)` before `self._axes.clear()`

## 3. Multi-Axes Charts: PriceRangePanel, FinancialFlowPanel

- [x] 3.1 In each chart's `__init__`, add `self._all_axes = [ax_main, ax_clv, ...]` listing all subplot axes and call `create_empty(self._figure, self._all_axes)`
- [x] 3.2 In each chart's `update()` empty data guard, replace the per-axes `set_xlim()`/`set_title()` calls with `show_empty(self._figure, self._all_axes, self._empty_label)` + `self._canvas.draw()` + return
- [x] 3.3 In each chart's `update()` data path, add `hide_empty(self._empty_label)` before the axes clear loop

## 4. Registry + Lazy Rendering in app.py

- [x] 4.1 Add `reset()` method to each chart that calls `show_empty()` with its stored axes and label (reusable utility — each chart class gets a tiny new method)
- [x] 4.2 In `app.py.__init__`, build `GENERAL` and `TICKER` registry dicts mapping sub-tab names to chart instances, and build `self._all_charts` list
- [x] 4.3 Add `_resolve_chart(main_tab, sub_tab)` method that returns the chart instance for the current selection
- [x] 4.4 Add `_do_update(chart)` method that dispatches `chart.update()` with correct params (filtered data for general, data+ticker for ticker, show_arrows for QuadrantChart)
- [x] 4.5 Refactor `_on_load_data()` to: fetch data → `_resolve_chart()` → reset non-current charts → `_do_update(current)`
- [x] 4.6 Refactor `_on_tab_changed()` to: detect which notebook changed → `_resolve_chart()` → `_do_update()` if data exists
- [x] 4.7 Remove `_update_charts()`, `_update_ticker_indicator_tabs()`, and `_charts_dirty` flag — replaced by registry + lazy rendering
- [x] 4.8 Remove `_refresh_current_tab()` — logic absorbed by `_on_load_data()` and `_on_tab_changed()`

## 5. Verification

- [x] 5.1 Start the app and confirm all 6 charts show "Sem dados" with axis off
- [x] 5.2 Navigate between all tabs and sub-tabs before loading data — confirm "Sem dados" persists
- [x] 5.3 Load data, confirm only the visible sub-tab's chart renders with data; switch to other sub-tabs and confirm they render now
- [x] 5.4 Reload data, confirm visible chart updates immediately; switch to a different sub-tab and confirm it was reset to "Sem dados" before rendering with new data
- [x] 5.5 Run lint/typecheck and fix any issues
