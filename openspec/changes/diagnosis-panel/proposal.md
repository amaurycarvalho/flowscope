## Why

The "Resumo Geral" placeholder tab in Análise do Ticker is disabled and shows only raw indicator text — it has no panel implementation and no clear design. Meanwhile, the existing panels (Amplitude de Preço, Fluxo Financeiro, Evolução da Dominância) each answer one specific question, but there is no consolidated view that answers "What kind of session did this asset have?". This change replaces the placeholder with a Diagnosis Panel that synthesizes all indicators into an interpretative diagnosis, respecting the FlowScope philosophy of one panel = one question.

## What Changes

- Replace the disabled "Resumo Geral" tab with a functioning "Diagnóstico" panel as the first tab in Análise do Ticker
- Create two new domain classifiers: InstitutionalClassifier and LiquidityClassifier
- Evolve the existing DominanceClassifier to optionally accept VWAP Distance for richer classification
- Create a Diagnosis domain object and DiagnosisComposer that assembles five independent classifier outputs into a structured narrative (title, badge, summary)
- Extract three reusable visual components from existing panels: CLVGauge, BuySellBar, PriceRangeDiagram
- Create a new ClassificationBar component for categorical display of classifier levels
- Build the DiagnosisPanel using GridSpec with height_ratios=[2.0, 1.4, 2.2, 1.2, 0.9] containing: DiagnosisCard, ClassificationBars, PriceRangeDiagram, BuySellBar, CLVGauge
- Add orientation/help text for the new panel
- No existing panels are removed or broken — components are extracted and reused

## Capabilities

### New Capabilities
- `diagnosis-panel`: New panel that synthesizes indicators into a single diagnostic conclusion, answering "What kind of session did this asset have?"
- `institutional-classifier`: Classifier that estimates participant profile (institutional vs. retail) from average trade size and average financial ticket
- `liquidity-classifier`: Classifier that assesses liquidity quality from financial, trade, and volume density

### Modified Capabilities
- `dominance-classifiers`: Evolve the DominanceClassifier to accept optional VWAP Distance parameter for richer quadrant-aware classification (e.g., "Compra Confirmada" vs "Compra em Recuperação"), fully backward-compatible

## Impact

- Domain: New files `domain/strategies/classifiers/institutional.py`, `domain/strategies/classifiers/liquidity.py`, `domain/diagnosis.py`; evolution of `domain/strategies/classifiers/dominance.py`
- Presentation: New files `charts/diagnosis_panel.py`, `charts/classification_bar.py`, `charts/clv_gauge.py`, `charts/buy_sell_bar.py`, `charts/price_range_diagram.py`
- Modified presentation: `charts/price_range_panel.py`, `charts/financial_flow_panel.py`, `app.py` (tab registration and help text)
- No new dependencies, no API changes, no infrastructure changes
