## Context

FlowScope currently uses a single-panel visualization model: three chart types (VWAP, CVD, Scatter) behind RadioButton selectors inside a "Visualização" LabelFrame. The AnalysisText widget is a stub. The proposed change replaces this with a two-level ttk.Notebook system, removing CVD/Scatter charts entirely, and introducing per-ticker analysis tabs as placeholders for future indicators.

The challenge is fitting a multi-tab interface into the existing PanedWindow layout without breaking the working data loading, filtering, ticker management, and export functionality.

## Goals / Non-Goals

**Goals:**
- Replace RadioButton + pack/forget chart switching with ttk.Notebook tab navigation
- Two main tabs: "Análise Geral" (VWAP + future Quadrantes) and "Análise do Ticker" (5 placeholder sub-tabs + combobox)
- Evolve AnalysisText into OrientationPanel — a read-only text panel that shows curated explanatory content keyed to the active sub-tab
- Remove CVDHistChart, ScatterChart, and all associated GUI code
- Remove CLI `--cvd` flag, `export_cvd_csv()`, and `ExportCVDUseCase`
- Persist `(main_tab, sub_tab)` in config.json instead of `last_chart`
- Keep data loading, ticker list, export (data + VWAP chart image), status bar, keyboard shortcuts, and sidebar layout intact

**Non-Goals:**
- Implement any logic for the placeholder tabs (Quadrantes, Dominância, Fluxo, etc.) — they remain empty placeholders
- Change the VWAP chart rendering logic
- Change the domain/application/infrastructure layers (except removing ExportCVDUseCase)
- Add new indicators or calculations

## Decisions

### Decision 1: Notebooks inside left_pw (PanedWindow), not replacing it

The main horizontal PanedWindow (`_main_pw`) and the right sidebar (TickerList + OrientationPanel) remain unchanged. The left vertical PanedWindow (`left_pw`) previously held `selector_frame` (fixed height) + `chart_container` (stretching). Now it holds only the `main_notebook` (stretching entirely).

```
BEFORE:
left_pw ──┬── selector_frame (RadioButtons)   [stretch=never]
          └── chart_container (active chart)   [stretch=always]

AFTER:
left_pw ── main_notebook                       [stretch=always]
```

The `selector_frame` is removed. The `_chart_container` Frame and `_chart_title` Label are removed — the Notebook tab labels serve as the title.

**Rationale**: Preserves the existing window layout and sash positions. No need to restructure the PanedWindow hierarchy. The Notebook replaces both the selector and the chart area in a single widget.

### Decision 2: Two-level Notebook — main Notebook contains sub-Notebooks

```
main_notebook (ttk.Notebook)
├── Tab "Análise Geral"
│   └── general_notebook (ttk.Notebook)
│       ├── Tab "VWAP"
│       │   └── vwap_chart.frame (existing)
│       └── Tab "Quadrantes"
│           └── ttk.Label("Em desenvolvimento...")
│
└── Tab "Análise do Ticker"
    └── ticker_frame (ttk.Frame)
        ├── ttk.Combobox (ticker selector, top)
        └── ticker_notebook (ttk.Notebook)
            ├── Tab "Dominância do Pregão"    → placeholder
            ├── Tab "Fluxo Financeiro"         → placeholder
            ├── Tab "Participação Institucional" → placeholder
            ├── Tab "Eficiência do Movimento"  → placeholder
            └── Tab "Resumo Geral"             → placeholder
```

**Rationale**: ttk.Notebook inside ttk.Notebook works cleanly in Tkinter. The sub-notebooks each own their content frames. The main notebook is the single child of `left_pw`.

### Decision 3: Combobox bound to TickerList data, not a separate list

The `ttk.Combobox` in "Análise do Ticker" reads its `values` from `TickerList.get_tickers()`. When the user edits the ticker list, `_on_ticker_edit()` (or the combobox's own refresh) updates the combobox values. The combobox has no "add ticker" capability — it only selects among already-loaded tickers.

**Rationale**: Single source of truth for available tickers. Ticker management stays in TickerList; the combobox is a selection convenience.

### Decision 4: OrientationPanel replaces AnalysisText as a content-driven widget

```
OrientationPanel
├── frame (tk.Frame)
│   ├── header: ttk.Label("Sobre esta análise")
│   └── body: tk.Text (read-only, word-wrap, height=10)
```

Content is set via `orientation_panel.set_content(title: str, body: str)`. Each sub-tab in both notebooks calls this method when selected, passing its own explanatory text.

**Rationale**: Simple key-value mapping from (main_tab, sub_tab) → (title, body). Avoids coupling OrientationPanel to specific tab names. The panel is purely presentational.

### Decision 5: `_show_current_chart()` → `_on_tab_changed()` event handler

Instead of a single method driven by `_chart_var`, tab changes are handled by binding to `<<NotebookTabChanged>>` on all three notebooks (main, general, ticker). The handler:

1. Determines which main tab is active
2. If "Análise Geral": reads the general sub-tab, shows/hides VWAP chart or placeholder
3. If "Análise do Ticker": reads the ticker sub-tab, shows the appropriate placeholder
4. Updates OrientationPanel content from the sub-tab map
5. Persists `(main_tab, sub_tab)` to preferences

**Rationale**: `<<NotebookTabChanged>>` is the standard Tkinter event for notebook selection. No need to maintain a separate `_chart_var` StringVar. Single handler for all tab changes.

### Decision 6: Preference persistence — `last_chart` replaced by compound key

```
BEFORE: "last_chart": "vwap"
AFTER:  "last_tab": "general", "last_subtab": "vwap"
```

Saved in `_on_close()` (same as before) and on every tab change (in `_on_tab_changed()`). On startup, the main notebook is `select()`-ed to `last_tab`, and the sub-notebook to `last_subtab`.

**Rationale**: Two-level navigation requires two keys. Keeping them as separate top-level keys avoids nested dictionaries in JSON.

### Decision 7: Remove ExportCVDUseCase and CLI --cvd entirely

The application layer `ExportCVDUseCase` is deleted. The CLI `--cvd` argument and `export_cvd_csv()` function are removed from `cli.py`. The dispatch in `main.py` for CVD export is removed.

**Rationale**: CVD chart is removed from the GUI; keeping a CLI export for a removed visualization creates confusion. If CVD data export is needed later, it can be reintroduced as a generic "export raw data" feature.

### Alternatives Considered

- **Single-level Notebook**: Flattening all tabs (VWAP, Quadrantes, Dominância, etc.) into one level. Rejected because it mixes general-market views with per-ticker views, creating an inconsistent navigation model.
- **Radiobutton → Combobox for chart selection**: Keeping the existing single-chart model but using a dropdown instead of radio buttons. Rejected — doesn't solve the need for per-ticker analysis and future placeholder tabs.
- **Out-of-process tab content (iframe-like)**: Creating separate toplevel windows per tab. Rejected — overengineered for Tkinter and breaks the integrated feel.
- **Custom Tab widget**: Building a custom tab bar from Canvas. Rejected — ttk.Notebook is stable, native, and works on all platforms.

## Risks / Trade-offs

[Risk: Notebook tab index fragility] → The `_on_tab_changed()` handler relies on `notebook.index(notebook.select())` to identify tabs. Tab indices change if tabs are reordered. Mitigation: Use tab text labels (via `notebook.tab(notebook.select(), "text")`) for identification instead of indices.

[Risk: Combobox out of sync with TickerList] → If TickerList is updated but the combobox values are not refreshed, the user might select a stale or missing ticker. Mitigation: Refresh combobox `values` property in `_on_ticker_edit()` and after data load.

[Risk: OrientationPanel content becomes stale] → When the user switches tabs, the panel must update immediately. Since `<<NotebookTabChanged>>` fires reliably, this is low risk. However, a fallback (empty state) must render if no match is found.

[Trade-off: Two-level Notebook nesting] → ttk.Notebook inside ttk.Notebook works but creates a slightly busy visual hierarchy. Acceptable because the tabs are conceptually distinct (market-wide vs. per-ticker).

[Trade-off: Removed CVD export] → Users who relied on `--cvd` CLI will lose that capability. Low impact as FlowScope is pre-1.0 and the primary interface is the GUI. If requested, a generic data export feature can be added separately.

## Open Questions

- Should the combobox trigger an immediate chart/panel update on selection, or require a confirm button? (Current design: immediate update via `<<ComboboxSelected>>` binding.)
- What exact explanatory text goes in OrientationPanel for each sub-tab? (Content is defined in specs, not design.)
- Should "Análise do Ticker" show the combobox + placeholder even when no data is loaded? (Yes — same empty state as the current VWAP chart: "Nenhum ticker corresponde ao filtro.")
