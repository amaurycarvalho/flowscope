## 1. Domain — New Strategies

- [x] 1.1 Create `domain/strategies/daily_money_flow.py` with `DailyMoneyFlowStrategy` (id: `daily_money_flow`, depends: `["clv"]`, output: `dict[str, dict[date, Decimal]]`)
- [x] 1.2 Create `domain/strategies/dominance_score.py` with `DominanceScoreStrategy` (id: `dominance_score`, depends: `["clv", "daily_efficiency"]`, output: `dict[str, dict[date, Decimal | None]]`)
- [x] 1.3 Export new strategies in `domain/strategies/__init__.py`
- [x] 1.4 Register new strategies in `domain/indicators.py` (`default_engine()`)

## 2. Domain — Classifiers Module

- [x] 2.1 Create `domain/strategies/classifiers/__init__.py` with exports
- [x] 2.2 Create `domain/strategies/classifiers/dominance.py` with `classify_dominance()`, `DominanceClassification` dataclass, and thresholds for 7 levels
- [x] 2.3 Create `domain/strategies/classifiers/conviction.py` with `classify_conviction()`, `ConvictionClassification` dataclass, and thresholds for 5 levels

## 3. Chart — DominanceRankingChart (Análise Geral)

- [x] 3.1 Create `presentation/gui/charts/dominance_ranking.py` with `DominanceRankingChart` class following existing chart pattern (FigureCanvasTkAgg + ToolbarBR)
- [x] 3.2 Implement `update(data)` extracting CLV (last date), MFV (accumulated), and ticker names from `_current_data`
- [x] 3.3 Implement diverging horizontal bar chart using `ax.barh` with proper direction (left/right from center)
- [x] 3.4 Implement color mapping per dominance classification (7-level diverging colormap)
- [x] 3.5 Implement circle markers at bar endpoints with diameter proportional to MFV
- [x] 3.6 Add axis labels, center line at CLV=0, "Compradores"/"Vendedores" annotations
- [x] 3.7 Add hover tooltip showing ticker, CLV, classification, MFV
- [x] 3.8 Add ticker labels on each bar (right-aligned for positive, left-aligned for negative)

## 4. Chart — DominanceTimelineChart (Análise do Ticker)

- [x] 4.1 Create `presentation/gui/charts/dominance_timeline.py` with `DominanceTimelineChart` class following existing chart pattern
- [x] 4.2 Implement `update(data)` extracting CLV series, daily_efficiency series, daily_money_flow series for the selected ticker
- [x] 4.3 Implement diverging horizontal bar chart with one bar per date, ordered chronologically
- [x] 4.4 Implement daily efficiency line overlay on secondary y-axis (0 to 1)
- [x] 4.5 Implement circle markers with diameter proportional to daily MFV
- [x] 4.6 Implement summary KPI panel: dominance/conviction classification, MFV total, "% Pregões Compradores"
- [x] 4.7 Add date labels per bar, axis labels, center line
- [x] 4.8 Add hover tooltip per bar showing data, CLV, classification, efficiency, conviction, daily MFV

## 5. GUI Integration — app.py

- [x] 5.1 Rename existing "Dominância do Pregão" sub-tab to "Amplitude de Preço" in `tab_configs` and `_tab_content`
- [x] 5.2 Add new "Dominância do Pregão" sub-tab entry to `tab_configs` (text-based summary of CLV, efficiency, classification, MFV) OR wire the new chart
- [x] 5.3 Add "Evolução da Dominância" sub-tab with `DominanceTimelineChart` embedded in `_build_main_area`
- [x] 5.4 Add `DominanceRankingChart` as new sub-tab in Análise Geral notebook (after Quadrantes)
- [x] 5.5 Update `_tab_content` dictionary with orientation texts for all new/renamed panels
- [x] 5.6 Update `_update_charts()` to call `update()` on both new charts
- [x] 5.7 Update `_format_all_indicators()` to include `dominance_score`
- [x] 5.8 Wire ticker selection sync for the timeline chart (same pattern as quadrant chart)

## 6. Tests

- [x] 6.1 Test `DailyMoneyFlowStrategy` with known CLV and FinVol values
- [x] 6.2 Test `DominanceScoreStrategy` with known CLV and Efficiency values
- [x] 6.3 Test `classify_dominance()` boundary values for all 7 levels
- [x] 6.4 Test `classify_conviction()` boundary values for all 5 levels
- [x] 6.5 Test that new indicators appear in `all_indicators` output from `AnalyzeTickersUseCase`
