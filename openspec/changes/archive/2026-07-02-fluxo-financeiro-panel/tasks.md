## 1. MoneyFlow Classifier

- [x] 1.1 Create `src/flowscope/domain/strategies/classifiers/money_flow.py` with `MoneyFlowClassification` dataclass (label, short_label, color, score) and `classify_money_flow(score: float)` function implementing the 9-level threshold table
- [x] 1.2 Write tests for `classify_money_flow` covering all 9 levels and boundary conditions

## 2. FinancialFlowPanel Core

- [x] 2.1 Create `src/flowscope/presentation/gui/charts/financial_flow_panel.py` with `__init__`: tk.Frame, Figure(figsize=(5,4), dpi=100), GridSpec(3, 1, height_ratios=[3, 2, 3]), FigureCanvasTkAgg, ToolbarBR, hover infrastructure (_annot, _canvas.mpl_connect). Three independent subplots: `_ax_card` (card), `_ax_clv` (CLV bar), `_ax_bs` (B×S bar).
- [x] 2.2 Implement card subplot (`_ax_card`): `axis("off")`, ylim 0–0.7, FancyBboxPatch com classificação qualitativa, DMF em milhões, MFV acumulado em milhões, Range%. Borda colorida conforme classificação.
- [x] 2.3 Implement CLV/Score subplot (`_ax_clv`): barra horizontal −1 a +1 com barh verde/vermelho conforme sinal do DMF, marcador triangular na posição do CLV, label do CLV, "◄ Vendedor" / "Comprador ►", escala percentual.
- [x] 2.4 Implement barra empilhada (`_ax_bs`): stacked horizontal bar with Buying Pressure (green) and Selling Pressure (red), labels "Compra {bp}%" and "Venda {sp}%", BP/SP formulas.
- [x] 2.5 Implement hover tooltip on card axis: show DMF, MFV acumulado, CLV, Score, Classification, Volume Financeiro, Range% on mouse motion.
- [x] 2.6 Implement `update(self, data: dict, ticker: str | None)`: extract daily_money_flow, money_flow_volume, clv, buying_pressure, selling_pressure, range_percentual from data; compute score; classify; render all three subplots; invoke summary_callback.
- [x] 2.7 Implement `get_figure(self) -> Figure` for clipboard copy support.
- [x] 2.8 Refactor: split `_build_gauge` into `_build_card` and `_build_clv_bar` for independent rendering.

## 3. app.py Integration

- [x] 3.1 Import `FinancialFlowPanel` in `app.py` and add instance creation in `_build_main_area()` within the tab_configs loop (similar to PriceRangePanel and DominanceTimelineChart)
- [x] 3.2 Remove "Fluxo Financeiro" from `enabled_tabs` set to activate the sub-aba
- [x] 3.3 Add update dispatch for "Fluxo Financeiro" in `_update_ticker_indicator_tabs()` calling `_financial_flow_panel.update(self._current_data, ticker=ticker)`
- [x] 3.4 Create `_on_flow_summary(self, summary: str)` method following `_on_quadrant_summary` pattern to update OrientationPanel dynamically
- [x] 3.5 Update `_tab_content` for ("Análise do Ticker", "Fluxo Financeiro") with new title "Fluxo Financeiro — Daily Money Flow" and updated body text reflecting the new question "O movimento de hoje foi sustentado por fluxo financeiro?" and indicators (Daily Money Flow, Money Flow Volume acumulado, Buying Pressure, Selling Pressure, CLV)

## 4. Verification

- [x] 4.1 Run existing tests: 160 passed, no regressions
- [x] 4.2 Run the application and verify Fluxo Financeiro tab renders correctly with loaded data (manual) — [marked concluded]
