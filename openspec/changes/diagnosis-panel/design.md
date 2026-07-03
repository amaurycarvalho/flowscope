## Context

The "Resumo Geral" tab is a disabled placeholder in the Análise do Ticker notebook — it falls through to a generic `tk.Text` widget with no chart class, no GridSpec, no visualization. Meanwhile, three panels exist (PriceRangePanel, FinancialFlowPanel, DominanceTimelineChart), each answering one question. There is no consolidated view.

Three other disabled tabs (Participação Institucional, Eficiência do Movimento, Resumo Geral) draw from the same indicators. This design replaces only Resumo Geral with a DiagnosisPanel that synthesizes all classifiers. The other two disabled tabs remain unchanged (they may be removed or subsumed in a future change).

## Goals / Non-Goals

**Goals:**
- Replace the disabled "Resumo Geral" tab with a functional DiagnosisPanel as the first tab in Análise do Ticker
- Create two new domain classifiers: Institutional and Liquidity
- Evolve DominanceClassifier to accept optional VWAP Distance parameter (backward-compatible)
- Create a Diagnosis domain object and DiagnosisComposer that concatenates 5 independent classifier narratives
- Extract CLVGauge, BuySellBar, PriceRangeDiagram as reusable visual components
- Create ClassificationBar component for categorical display of 4 classifier levels
- Register the panel, add orientation text
- Refactor PriceRangePanel and FinancialFlowPanel to use the extracted components

**Non-Goals:**
- No changes to other tabs (Análise Geral, existing Ticker Analysis panels)
- No removal of the two other disabled tabs (Participação Institucional, Eficiência do Movimento)
- No HistoricalContext infrastructure (V2 enhancement, post-change)
- No changes to data ingestion, indicator calculation, or infrastructure layer
- No score composition or numerical ranking in the diagnosis

## Decisions

### Architecture: Three-layer separation

```
Indicators (existing)
    ↓
Classifiers (domain) → *Diagnosis objects
    ↓
DiagnosisComposer (domain) → Diagnosis {title, badge, subtitle, summary}
    ↓
Visual components (presentation) → DiagnosisPanel
```

Each classifier is independent, returns a typed diagnosis object, and owns its narrative fragment. The Composer does not decide — it concatenates.

### Classifier protocol: No shared interface, five concrete types

Each classifier returns its own dataclass with only the fields it needs:

- `DirectionDiagnosis { classification, title, summary }` — from DominanceClassifier (evolved)
- `MoneyFlowDiagnosis { classification, phrase }` — from existing MoneyFlowClassifier
- `ConvictionDiagnosis { classification, phrase }` — from existing ConvictionClassifier
- `InstitutionalDiagnosis { classification, badge }` — new classifier
- `LiquidityDiagnosis { classification, phrase }` — new classifier

Alternative considered: a common `ClassifierResult` protocol. Rejected because the five dimensions are not interchangeable — forcing a uniform interface would either lose semantics or require awkward optional fields.

### DominanceClassifier evolution: Optional VWAP Distance

The existing `classify_dominance(clv)` gains an optional `vwap_distance` parameter. When absent, behavior is identical to today. When present, the classifier produces richer labels (e.g., "Compra Confirmada" when CLV > 0 AND VWAP Distance > 0). The function signature:

```python
def classify_dominance(clv: float, *, vwap_distance: float | None = None) -> DominanceClassification
```

Alternative considered: creating a separate DirectionClassifier. Rejected because "dominance" and "direction" describe the same phenomenon at different granularities — keeping one concept avoids confusion.

### DiagnosisComposer: Concatenator, not decider

The composer receives five typed diagnosis objects and produces a single `Diagnosis`:

```python
@dataclass(frozen=True)
class Diagnosis:
    title: str      # from DirectionDiagnosis.title, e.g. "Pregão Comprador"
    badge: str      # from InstitutionalDiagnosis.badge, e.g. "🏦 Institucional"
    subtitle: str   # from conviction or money_flow, e.g. "Direcional"
    summary: str    # concatenation: "Movimento direcional sustentado por forte fluxo financeiro em ambiente de alta liquidez."
```

No priority rules, no scoring — each classifier fills its slot.

Alternative considered: a rule engine that selects the best title from all 5 dimensions. Rejected because direction is always the substantive noun; other dimensions are qualifiers. The hierarchy is semantic, not algorithmic.

### New classifiers: Heuristic V1, percentile V2 (future)

InstitutionalClassifier and LiquidityClassifier use fixed thresholds in V1, encapsulated behind their public API. When HistoricalContext infrastructure is built (future change), only the internal implementation changes — no panel code, no composer code, no other classifier code is affected.

**InstitutionalClassifier V1 heuristics:**

- Average Ticket / Avg Price → relative size metric
- Combines average_trade_size and average_financial_ticket into qualitative levels: "Varejo", "Misto", "Institucional", "Institucional Forte"

**LiquidityClassifier V1 heuristics:**

- financial_density, trade_density, volume_density combined into: "Muito Baixa", "Baixa", "Normal", "Alta", "Muito Alta"

### Visual components: Extract primitives, not panels

Three components are extracted from existing panels:

- **CLVGauge**: horizontal bar -1..+1 with fill color (from PriceRangePanel)
- **BuySellBar**: stacked horizontal bar with Buy/Sell pressure (from FinancialFlowPanel)
- **PriceRangeDiagram**: single-day min-max line with markers (V, M, T, W, ●) — extracted from PriceRangePanel's multi-day timeline

Existing panels are refactored to use these components internally.

Alternative considered: adding a "mode" parameter to PriceRangePanel for single-day display. Rejected because PriceRangePanel is oriented around temporal evolution (Y axis = time, arrows between days) while the diagnosis needs a static single-day view — fundamentally different semantics.

### ClassificationBar: Categorical, not continuous

Four bars (Fluxo, Convicção, Liquidez, Institucional) display classifier level using 5 discrete widths:

```
Muito Baixo  █
Baixo        ███
Normal       █████
Alto         ███████
Muito Alto   ██████████
```

No continuous 0-100 normalization. No percentiles visible to the panel. The level enum determines the bar length.

Alternative considered: continuous 0-100 bars normalized by historical percentile. Rejected because this requires HistoricalContext infrastructure (future) and the categorical approach is more robust without it.

### GridSpec layout

```python
GridSpec(5, 1, height_ratios=[2.0, 1.4, 2.2, 1.2, 0.9])
```

| Row | Component | Purpose |
|-----|-----------|---------|
| 0 | DiagnosisCard (text-only, no axes) | Title + badge + summary |
| 1 | ClassificationBar (4 categorical bars) | Fluxo, Convicção, Liquidez, Institucional |
| 2 | PriceRangeDiagram | Single-day min-max with markers |
| 3 | BuySellBar | Buying/Selling pressure |
| 4 | CLVGauge | Close Location Value |

Reading order follows natural interpretation: conclusion → strength → price evidence → pressure → close location.

### Tab order and naming

- File: `presentation/gui/charts/diagnosis_panel.py`
- Class: `DiagnosisPanel`
- Tab text: "Diagnóstico" (Portuguese, matches UI language)
- Position: First tab in Análise do Ticker notebook
- Existing code path: Replace the `("Resumo Geral", None)` entry in `tab_configs` and its `else` branch

## Risks / Trade-offs

- **V1 heuristic thresholds may misclassify edge cases** → Mitigation: encapsulated behind classifier interface; thresholds can be tuned without affecting other layers. Orientation text clarifies the heuristic nature.
- **Three extracted components increase file count** → Mitigation: each component is a focused 30-80 line file with a single responsibility. Total added code is comparable to inlining.
- **DominanceClassifier evolution may affect existing callers** → Mitigation: parameter is optional with default None; existing callers pass no vwap_distance and get identical behavior. Test coverage confirms backward compatibility.
- **DiagnosisPanel adds 5 subplot rows** → Mitigation: 1280×800 minimum resolution handles this comfortably; the panel uses toolbar-scrollable figure if needed.
