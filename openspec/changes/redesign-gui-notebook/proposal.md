## Why

The current visualization selector (RadioButtons) limits the interface to cycling between three unrelated charts. This prevents FlowScope from evolving into a multi-perspective analysis tool where the user navigates between general market overview and per-ticker deep dives. The AnalysisText placeholder is unused and the CVD/Dispersion charts overlap with the core VWAP analysis without adding distinct value.

## What Changes

### Additions
- Main `ttk.Notebook` replacing the "Visualização" RadioButton frame with two tabs: "Análise Geral" and "Análise do Ticker"
- Sub-notebook in "Análise Geral" with "VWAP" (existing chart) and "Quadrantes" (placeholder for future development)
- Sub-notebook in "Análise do Ticker" with 5 tabs: "Dominância do Pregão", "Fluxo Financeiro", "Participação Institucional", "Eficiência do Movimento", "Resumo Geral" (all placeholders)
- `ttk.Combobox` in "Análise do Ticker" for selecting a single ticker from the current ticker list
- `OrientationPanel` widget replacing `AnalysisText`, displaying a fixed explanatory text per sub-tab (purpose, indicators involved, how to interpret)

### Removals **BREAKING**
- RadioButton group and "Visualização" frame
- `CVDHistChart` (GUI chart) — **BREAKING**
- `ScatterChart` (GUI scatter plot) — **BREAKING**
- `--cvd` CLI flag and `export_cvd_csv()` — **BREAKING**
- `ExportCVDUseCase` from application layer — **BREAKING**
- `AnalysisText` widget (replaced by `OrientationPanel`)

### Modifications
- `_show_current_chart()` adapted to control notebook tabs instead of pack/forget
- `_update_charts()` simplified to update only VWAP chart
- `_copy_chart()` simplified to copy only VWAP chart
- `config.json` persistence: `last_chart` field replaced by `last_tab` + `last_subtab`
- `TickerList` changes propagate to the combobox in "Análise do Ticker"

## Capabilities

### New Capabilities
- `ticker-analysis`: Per-ticker deep analysis with sub-views for price dominance, financial flow, institutional participation, movement efficiency, and a general summary. All tabs are placeholders for future development.

### Modified Capabilities
- `gui-interface`: Requirements for CVD histogram chart, scatter plot chart, and RadioButton selector are removed. Requirements for notebook-based navigation and per-ticker analysis combobox are added. AnalysisText requirement evolves to OrientationPanel.
- `cli-interface`: Requirement for `--cvd` export flag is removed.

## Impact

- `src/flowscope/presentation/gui/app.py` — major restructuring of `_build_main_area()`, `_show_current_chart()`, `_update_charts()`, `_copy_chart()`, `_on_close()`, preference load/save
- `src/flowscope/presentation/gui/charts/cvd_hist.py` — removed
- `src/flowscope/presentation/gui/charts/scatter.py` — removed
- `src/flowscope/presentation/gui/widgets/analysis_text.py` — replaced by `orientation_panel.py`
- `src/flowscope/presentation/cli.py` — remove `--cvd` argument and `export_cvd_csv()`
- `src/flowscope/application/use_cases.py` — remove `ExportCVDUseCase`
- `src/flowscope/presentation/main.py` — remove CVD export dispatch
- No changes to domain layer or infrastructure layer (CVD calculation preserved for future use)
