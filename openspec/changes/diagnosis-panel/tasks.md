## 1. Domain — New Classifiers

- [ ] 1.1 Create `domain/strategies/classifiers/institutional.py` with `InstitutionalClassification` dataclass and `classify_institutional(avg_trade_size, avg_financial_ticket)` using V1 heuristic thresholds
- [ ] 1.2 Create `domain/strategies/classifiers/liquidity.py` with `LiquidityClassification` dataclass and `classify_liquidity(financial_density, trade_density, volume_density)` using V1 heuristic thresholds
- [ ] 1.3 Update `domain/strategies/classifiers/__init__.py` to export the two new classifiers

## 2. Domain — Evolve DominanceClassifier

- [ ] 2.1 Add optional `vwap_distance: float | None = None` parameter to `classify_dominance()` in `domain/strategies/classifiers/dominance.py`
- [ ] 2.2 Implement enriched classification logic when vwap_distance is provided (confirmada vs recuperação labels)
- [ ] 2.3 Verify all existing callers still work without vwap_distance (backward compatibility)

## 3. Domain — Diagnosis and DiagnosisComposer

- [ ] 3.1 Create `domain/diagnosis.py` with typed diagnosis dataclasses: `DirectionDiagnosis`, `MoneyFlowDiagnosis`, `ConvictionDiagnosis`, `InstitutionalDiagnosis`, `LiquidityDiagnosis`
- [ ] 3.2 Implement `Diagnosis` dataclass with title, badge, subtitle, summary fields
- [ ] 3.3 Implement `DiagnosisComposer.compose()` that receives 5 diagnosis objects and returns a single `Diagnosis` by concatenating each classifier's narrative fragment

## 4. Presentation — Extract CLVGauge Component

- [ ] 4.1 Create `presentation/gui/charts/clv_gauge.py` extracting the CLV gauge bar logic from `price_range_panel.py`
- [ ] 4.2 Refactor `PriceRangePanel._build_clv_gauge()` to use the new `CLVGauge` component

## 5. Presentation — Extract BuySellBar Component

- [ ] 5.1 Create `presentation/gui/charts/buy_sell_bar.py` extracting the buy/sell pressure stacked bar logic from `financial_flow_panel.py`
- [ ] 5.2 Refactor `FinancialFlowPanel._build_bs_bar()` to use the new `BuySellBar` component

## 6. Presentation — Extract PriceRangeDiagram Component

- [ ] 6.1 Create `presentation/gui/charts/price_range_diagram.py` with single-day min-max range line logic (markers for M, T, V, W, Close)
- [ ] 6.2 Refactor `PriceRangePanel` to use `PriceRangeDiagram` internally for the current day rendering

## 7. Presentation — Create ClassificationBar Component

- [ ] 7.1 Create `presentation/gui/charts/classification_bar.py` with categorical bar rendering (5 discrete levels: Muito Baixo through Muito Alto)
- [ ] 7.2 Component accepts 4 classifier levels and renders labeled horizontal bars for Fluxo, Convicção, Liquidez, Institucional

## 8. Presentation — Create DiagnosisPanel

- [ ] 8.1 Create `presentation/gui/charts/diagnosis_panel.py` with `DiagnosisPanel` class following the established panel pattern (Figure, GridSpec, empty state, hover tooltip)
- [ ] 8.2 Implement `_build_card()` — text-only card rendering title, badge, and summary from the `Diagnosis` object
- [ ] 8.3 Implement `_build_classification_bars()` using `ClassificationBar` component
- [ ] 8.4 Implement `_build_price_range_diagram()` using `PriceRangeDiagram` component
- [ ] 8.5 Implement `_build_buy_sell_bar()` using `BuySellBar` component
- [ ] 8.6 Implement `_build_clv_gauge()` using `CLVGauge` component
- [ ] 8.7 Wire `update()` method to extract indicators, run all 5 classifiers, call DiagnosisComposer, and render all components
- [ ] 8.8 Add tooltip support (reusing existing hover pattern)

## 9. Integration — Register Panel in Application

- [ ] 9.1 Replace the `("Resumo Geral", None)` entry in `app.py` `tab_configs` with `DiagnosisPanel` instance
- [ ] 9.2 Position "Diagnóstico" as the first tab in Análise do Ticker notebook
- [ ] 9.3 Add orientation/help text for the "Diagnóstico" tab in the `_tab_content` structure

## 10. Verification

- [ ] 10.1 Run existing test suite to confirm no regressions from refactored components
- [ ] 10.2 Launch application and verify DiagnosisPanel renders correctly with loaded data
- [ ] 10.3 Verify all three extracted components still render correctly in their original panels
- [ ] 10.4 Verify DominanceClassifier backward compatibility (callers without vwap_distance)
