## ADDED Requirements

### Requirement: Charts show empty state on app start

Upon application startup, before any data is loaded, every chart panel SHALL display a centered "Sem dados" label with all axes turned off.

#### Scenario: App starts with no data
- **WHEN** the application window is fully initialized and no data has been loaded
- **THEN** each chart panel shows a clean state with `ax.axis("off")` and a centered "Sem dados" label in light gray

#### Scenario: Empty state survives tab navigation
- **WHEN** the user switches between tabs and sub-tabs before loading data
- **THEN** every chart panel continues to show the empty state

### Requirement: Charts show empty state when no data is available

When `update()` is called but no valid data is provided, the chart SHALL render the empty state instead of a blank axes with a title.

#### Scenario: Update with empty dict
- **WHEN** a chart's `update()` method receives an empty dict or `None`
- **THEN** the chart displays the "Sem dados" empty state

#### Scenario: Update with missing ticker
- **WHEN** a ticker-specific chart's `update()` receives data but the ticker is not present
- **THEN** the chart displays the "Sem dados" empty state

#### Scenario: Update with empty daily data
- **WHEN** all data fields exist but daily_data is empty
- **THEN** the chart displays the "Sem dados" empty state

### Requirement: Multi-axes charts show single empty state

Charts with multiple subplots (PriceRangePanel, FinancialFlowPanel) SHALL display a single "Sem dados" label centered on the entire figure, not separate labels per subplot.

#### Scenario: Multi-axes chart in empty state
- **WHEN** a chart with multiple axes (e.g., 2 or 3 subplots) is in empty state
- **THEN** a single `fig.text()` label is shown centered on the figure, and all subplot axes have `axis("off")`

### Requirement: Lazy rendering by sub-tab

When data is loaded, only the chart of the currently visible sub-tab SHALL be rendered. Charts of non-visible sub-tabs SHALL remain in "Sem dados" state.

#### Scenario: Data load while on VWAP sub-tab
- **WHEN** data is loaded while the user is on "Análise Geral > VWAP"
- **THEN** only the VWAP chart is updated with data; Quadrantes and Dominância charts remain in empty state

#### Scenario: Data load while on Dominância Timeline sub-tab
- **WHEN** data is loaded while the user is on "Análise do Ticker > Evolução da Dominância"
- **THEN** only the Dominância Timeline chart is updated; PriceRange and FinancialFlow remain in empty state

#### Scenario: Switching to a non-visible sub-tab after data load
- **WHEN** data has been loaded and the user switches to a sub-tab that was previously in empty state
- **THEN** that sub-tab's chart is now updated with the available data

### Requirement: Data reload resets non-visible charts to empty

When data is reloaded, charts of non-visible sub-tabs SHALL be reset to "Sem dados" state (Opção A — pure). Only the currently visible sub-tab's chart SHALL be updated with the new data.

#### Scenario: Reload while on VWAP, then switch to Quadrantes
- **WHEN** data is reloaded while viewing VWAP, and then the user switches to Quadrantes
- **THEN** VWAP shows new data immediately; Quadrantes was reset to "Sem dados" on reload and now renders with new data on switch

#### Scenario: Reload while on Dominância Timeline, then switch to PriceRange
- **WHEN** data is reloaded while viewing Dominância Timeline, and then the user switches to PriceRange
- **THEN** Dominância Timeline shows new data; PriceRange was reset to empty on reload and now renders with new data on switch

### Requirement: Utility function for empty state

The project SHALL provide shared utility functions to create, show, and hide the empty state consistently across all chart types.

#### Scenario: create_empty called on chart init
- **WHEN** a chart is initialized
- **THEN** `create_empty(figure, axes_list)` is called, returning a `Text` object, with all axes set to `axis("off")` and a centered "Sem dados" label on the figure

#### Scenario: show_empty called on empty data
- **WHEN** a chart's `update()` guard detects no data
- **THEN** `show_empty(figure, axes_list, label)` is called, clearing all axes, setting them to `axis("off")`, and making the label visible

#### Scenario: hide_empty called before plotting
- **WHEN** a chart's `update()` has data to plot
- **THEN** `hide_empty(label)` is called, making the label invisible so the chart can render normally

### Requirement: Registry mapping coordinates lazy rendering

The application SHALL maintain a mapping from (main_tab, sub_tab) tuples to chart instances, used to coordinate which chart to update on tab switches and data loads.

#### Scenario: Registry resolves chart for current sub-tab
- **WHEN** data is loaded or a tab changes
- **THEN** the registry mapping is queried with the current (main_tab, sub_tab) to find the chart instance
- **THEN** only that chart's `update()` is called

#### Scenario: Quadrant chart receives show_arrows parameter
- **WHEN** the Quadrant chart is resolved from the registry
- **THEN** the update call passes `show_arrows=(len(filtered) == 1)` alongside the data mapping
