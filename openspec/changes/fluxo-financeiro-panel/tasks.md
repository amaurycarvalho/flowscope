## 1. MoneyFlow Classifier

- [ ] 1.1 Create `src/flowscope/domain/strategies/classifiers/money_flow.py` with `MoneyFlowClassification` dataclass (label, short_label, color, score) and `classify_money_flow(score: float)` function implementing the 9-level threshold table
- [ ] 1.2 Write tests for `classify_money_flow` covering all 9 levels and boundary conditions

## 2. FinancialFlowPanel Core

- [ ] 2.1 Create `src/flowscope/presentation/gui/charts/financial_flow_panel.py` with `__init__`: tk.Frame, Figure(figsize=(5,4), dpi=100), GridSpec(2, 1, height_ratios=[3, 2]), FigureCanvasTkAgg, ToolbarBR, hover infrastructure (_annot, _canvas.mpl_connect)
- [ ] 2.2 Implement gauge principal (row 0): divergent horizontal bar centered at 0 using `daily_money_flow` value, with green/red coloring, scale labels ("Vendedor ◄" / "► Comprador"), classification text annotation, DMF value text
- [ ] 2.3 Add CLV marker to the gauge: triangle or vertical line at CLV position on -1 to +1 scale, with CLV value label
- [ ] 2.4 Add accumulated MFV text overlay: "Acum. {N}d: R$ {valor}" using `money_flow_volume` from data, positioned at bottom-right of gauge
- [ ] 2.5 Add Range% text overlay: "Range: {value}%" positioned at bottom-left of gauge
- [ ] 2.6 Implement barra empilhada (row 1): stacked horizontal bar with Buying Pressure (green) and Selling Pressure (red), labels "Compra {bp}%" and "Venda {sp}%"
- [ ] 2.7 Implement hover tooltip on gauge: show DMF, MFV acumulado, CLV, Score, Classification, Volume Financeiro, Range% on mouse motion
- [ ] 2.8 Implement `update(self, data: dict, ticker: str | None)`: extract daily_money_flow, money_flow_volume, clv, buying_pressure, selling_pressure, range_percentual from data; compute score; classify; render all elements; invoke summary_callback
- [ ] 2.9 Implement `get_figure(self) -> Figure` for clipboard copy support

## 3. app.py Integration

- [ ] 3.1 Import `FinancialFlowPanel` in `app.py` and add instance creation in `_build_main_area()` within the tab_configs loop (similar to PriceRangePanel and DominanceTimelineChart)
- [ ] 3.2 Remove "Fluxo Financeiro" from `enabled_tabs` set to activate the sub-aba
- [ ] 3.3 Add update dispatch for "Fluxo Financeiro" in `_update_ticker_indicator_tabs()` calling `_financial_flow_panel.update(self._current_data, ticker=ticker)`
- [ ] 3.4 Create `_on_flow_summary(self, summary: str)` method following `_on_quadrant_summary` pattern to update OrientationPanel dynamically
- [ ] 3.5 Update `_tab_content` for ("Análise do Ticker", "Fluxo Financeiro") with new title "Fluxo Financeiro — Daily Money Flow" and updated body text reflecting the new question "O movimento de hoje foi sustentado por fluxo financeiro?" and indicators (Daily Money Flow, Money Flow Volume acumulado, Buying Pressure, Selling Pressure, CLV)

## 4. Verification

- [ ] 4.1 Run existing tests: `python -m pytest tests/ -x -q` to ensure no regressions
- [ ] 4.2 Run the application and verify Fluxo Financeiro tab renders correctly with loaded data
