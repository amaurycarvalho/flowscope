## 1. Preparation — Remove CVD and Scatter dependencies

- [x] 1.1 Remove `ExportCVDUseCase` from `src/flowscope/application/use_cases.py`
- [x] 1.2 Remove `--cvd` argument and `export_cvd_csv()` from `src/flowscope/presentation/cli.py`
- [x] 1.3 Remove CVD export dispatch from `src/flowscope/presentation/main.py`
- [x] 1.4 Remove imports of `CVDHistChart` and `ScatterChart` from `src/flowscope/presentation/gui/app.py`
- [x] 1.5 Delete `src/flowscope/presentation/gui/charts/cvd_hist.py`
- [x] 1.6 Delete `src/flowscope/presentation/gui/charts/scatter.py`

## 2. OrientationPanel widget

- [x] 2.1 Create `src/flowscope/presentation/gui/widgets/orientation_panel.py` with class `OrientationPanel` — a `tk.Frame` containing a title `ttk.Label` and a read-only `tk.Text` body, with a `set_content(title, body)` method
- [x] 2.2 Delete `src/flowscope/presentation/gui/widgets/analysis_text.py`

## 3. Notebook layout in `_build_main_area()`

- [x] 3.1 Replace `selector_frame` (RadioButtons + LabelFrame "Visualização") and `chart_container` in `left_pw` with a single `main_notebook = ttk.Notebook(left_pw)` containing two tabs
- [x] 3.2 Create `general_frame` (tab "Análise Geral") containing `general_notebook` (sub-tabs "VWAP" and "Quadrantes"). Pack `VWAPHistChart.frame` inside the "VWAP" sub-tab
- [x] 3.3 Create `ticker_frame` (tab "Análise do Ticker") containing a `ttk.Combobox` at top and `ticker_notebook` (5 placeholder sub-tabs: Dominância, Fluxo, Participação, Eficiência, Resumo) below
- [x] 3.4 Bind `<<NotebookTabChanged>>` on all three notebooks to `_on_tab_changed()`
- [x] 3.5 Bind `<<ComboboxSelected>>` on the combobox to update OrientationPanel

## 4. Replace AnalysisText with OrientationPanel in sidebar

- [x] 4.1 Instantiate `OrientationPanel` instead of `AnalysisText` in `_build_main_area()` (right sidebar `analysis_frame`)
- [x] 4.2 Define a content map: `{(main_tab, sub_tab): (title, body)}` with fixed explanatory text for each sub-tab

## 5. `_on_tab_changed()` handler

- [x] 5.1 Implement `_on_tab_changed()` that reads the active main tab + sub-tab via `notebook.tab(notebook.select(), "text")`
- [x] 5.2 For "Análise Geral" / "VWAP": show VWAP chart (pack if hidden), hide for Quadrantes placeholder
- [x] 5.3 For "Análise do Ticker": update OrientationPanel based on active sub-tab
- [x] 5.4 Save `(main_tab, sub_tab)` to preferences on each change

## 6. Remove `_chart_var`, `_on_chart_select()`, and `_show_current_chart()`

- [x] 6.1 Delete `self._chart_var` and all references to it
- [x] 6.2 Delete `_on_chart_select()` method
- [x] 6.3 Delete `_show_current_chart()` method
- [x] 6.4 Remove `_chart_title_var` and `_chart_title` Label
- [x] 6.5 Remove `_empty_label` (empty state is handled by the notebook's empty tabs)

## 7. Update `_update_charts()` and `_copy_chart()`

- [x] 7.1 Simplify `_update_charts()` to update only `_vwap_chart` (remove CVD and Scatter update calls)
- [x] 7.2 Simplify `_copy_chart()` to use only `_vwap_chart` (remove CVD/Scatter dict lookup)
- [x] 7.3 Remove `matplotlib.use("TkAgg")` from `_update_charts()` if it was only needed for the removed charts

## 8. Combobox sync with TickerList

- [x] 8.1 After data load (`_on_load_data()`), populate combobox values from `self._tickers`
- [x] 8.2 In `_on_ticker_edit()`, refresh combobox values from `TickerList.get_tickers()`
- [x] 8.3 Combobox selection triggers `_on_tab_changed()` to update OrientationPanel

## 9. Preference persistence update

- [x] 9.1 Replace `"last_chart"` with `"last_tab"` and `"last_subtab"` in `DEFAULT_CONFIG`
- [x] 9.2 Update `_on_close()` to save `last_tab` and `last_subtab`
- [x] 9.3 Update `__init__()` to restore notebook selections from `last_tab`/`last_subtab` on startup

## 10. Final cleanup and verification

- [x] 10.1 Remove unused imports from `app.py` (tkinter.ttk was already imported; remove `analysis_text`, `cvd_hist`, `scatter` imports)
- [x] 10.2 Verify the VWAP chart renders correctly in the notebook tab
- [x] 10.3 Verify data loading, ticker list, export (data + chart), shortcuts still work
- [x] 10.4 Verify preferences save and restore the correct tab/sub-tab across sessions
- [x] 10.5 Run the application and test all tab navigation paths
