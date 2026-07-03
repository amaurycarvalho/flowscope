## 1. Classifier

- [ ] 1.1 Create `src/flowscope/domain/strategies/classifiers/efficiency.py` with `EfficiencyClassification` dataclass and `classify_efficiency()` function with 5 levels (Muito Baixa to Muito Alta), each with label, short_label, color, score, and explanatory text
- [ ] 1.2 Export `classify_efficiency` and `EfficiencyClassification` from `src/flowscope/domain/strategies/classifiers/__init__.py`

## 2. Efficiency Panel

- [ ] 2.1 Create `src/flowscope/presentation/gui/charts/efficiency_panel.py` with `EfficiencyPanel` class following `FinancialFlowPanel` pattern (GridSpec `height_ratios=[2, 1, 3]`, FigureCanvasTkAgg, ToolbarBR, empty state)
- [ ] 2.2 Implement `_build_card()`: classification title, efficiency percentage, colored border, auto-generated explanatory text based on `classify_efficiency()` result
- [ ] 2.3 Implement `_build_gauge()`: horizontal gauge 0–1 with three colored zones (red 0–0.30 "Ruído", yellow 0.30–0.60 "Intermediário", green 0.60–1.00 "Progresso") and triangular marker for current efficiency
- [ ] 2.4 Implement `_build_history()`: horizontal bar chart with last 15 pregões, bars colored by efficiency zone, current day highlighted
- [ ] 2.5 Implement `_on_motion()` hover tooltip showing date, efficiency, range, range%, CLV, close price, and average price for all bars
- [ ] 2.6 Implement `update()` method consuming `all_indicators["daily_efficiency"]`, `["range"]`, `["range_percentual"]`, `["clv"]`

## 3. App Integration

- [ ] 3.1 Import `EfficiencyPanel` in `src/flowscope/presentation/gui/app.py`
- [ ] 3.2 Instantiate `EfficiencyPanel` in `_build_main_area()` for "Eficiência do Movimento" tab, replacing the `Text` placeholder
- [ ] 3.3 Remove "Eficiência do Movimento" from `enabled_tabs` exclusion set (or remove it — it's already listed in tab_configs but disabled)
- [ ] 3.4 Add `self._efficiency_panel` to `self._TICKER` dict and `self._ticker_charts` set
- [ ] 3.5 Update orientation text in `_tab_content` for ("Análise do Ticker", "Eficiência do Movimento") with new objective, question, indicators, and interpretation

## 4. Documentation

- [ ] 4.1 Update `panels.md` to document the new "Eficiência do Movimento" sub-aba with layout, components, question answered, indicators, and interpretation
