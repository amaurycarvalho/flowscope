## 1. Rename and Enable Tab

- [ ] 1.1 Rename tab `"Participação Institucional"` → `"Participação nas Negociações"` in `app.py:245`
- [ ] 1.2 Add `"Participação nas Negociações"` to `enabled_tabs` set in `app.py:250`

## 2. Create ParticipationPanel

- [ ] 2.1 Create `presentation/gui/charts/participation_panel.py` with class skeleton (`__init__`, `update`, `reset`, `get_figure`) following existing pattern (GridSpec, FigureCanvasTkAgg, ToolbarBR, empty state, hover annotation)
- [ ] 2.2 Implement `_compute_statistics(data, ticker)` — extracts ATS and AFT dicts from `all_indicators`, computes mean, std, z-score, falls back to nominal thresholds when std=0
- [ ] 2.3 Implement `_classify(z_score)` — returns classification label (Muito Fragmentado a Muito Concentrado) and color based on z-score thresholds (±0.8, ±1.5)
- [ ] 2.4 Implement `_build_gauge(ax, score, classification, color)` — horizontal bar with marker at score position 0-1, labels "Fragmentado" left and "Concentrado" right, classification text above
- [ ] 2.5 Implement `_build_card(ax, aft_value, ats_value, aft_var, ats_var, ticker)` — card with AFT (R$) and ATS (ações/negócio), each with % variation vs historical median
- [ ] 2.6 Implement `_build_timeline(ax, aft_dict, median)` — line plot of AFT over dates, horizontal dashed line at median, rotated date labels
- [ ] 2.7 Implement `_generate_summary(classification, z_score, ats_percentile, td_percentile)` — generates contextual text; incorporates Trade Density qualifier when ATS is above P70 and TD is above P70 or below P30
- [ ] 2.8 Implement tooltip (`_on_motion`, `_show_tooltip`) — shows AFT, ATS, Trade Density, z-score, classification on hover
- [ ] 2.9 Handle edge cases: std=0 (fallback to nominal thresholds), <3 dates (no classification), no Trade Density data (omit qualifier), empty state when no ticker selected

## 3. Wire Panel into GUI

- [ ] 3.1 Import `ParticipationPanel` in `app.py`
- [ ] 3.2 Add entry in `_TICKER` dict mapping `"Participação nas Negociações"` → `self._participation_panel`
- [ ] 3.3 Add key names `("average_trade_size", "average_financial_ticket", "trade_density")` to tab config for `"Participação nas Negociações"`
- [ ] 3.4 Add orientation/help content to `_tab_content` for the new tab
- [ ] 3.5 Add `self._participation_panel` to `_all_charts` list

## 4. Verify

- [ ] 4.1 Run existing test suite: `python -m pytest` — no regressions
- [ ] 4.2 Manual verification: load data, navigate to tab, confirm gauge/card/timeline render correctly for multiple tickers
