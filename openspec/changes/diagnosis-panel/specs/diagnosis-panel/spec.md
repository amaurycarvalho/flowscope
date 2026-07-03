## ADDED Requirements

### Requirement: DiagnosisPanel replaces Resumo Geral placeholder (DP101)

The system SHALL replace the disabled "Resumo Geral" tab in the Análise do Ticker notebook with a functioning DiagnosisPanel as the first tab, answering "What kind of session did this asset have?".

#### Scenario: Tab is enabled and first in order

- **WHEN** the application starts
- **THEN** the "Diagnóstico" tab SHALL be enabled, selectable, and positioned as the first tab in the Análise do Ticker notebook

### Requirement: Panel layout uses GridSpec with five rows (DP102)

The DiagnosisPanel SHALL use a matplotlib GridSpec with 5 rows and 1 column, with height_ratios=[2.0, 1.4, 2.2, 1.2, 0.9], containing: DiagnosisCard, ClassificationBars, PriceRangeDiagram, BuySellBar, CLVGauge.

#### Scenario: All five components render

- **WHEN** a ticker has data available
- **THEN** the panel SHALL display five stacked components: a text-only card at top, four classification bars, a price range diagram, a buying pressure bar, and a CLV gauge

#### Scenario: Empty state when no data

- **WHEN** no ticker is selected or data is unavailable
- **THEN** the panel SHALL display the standard empty state placeholder

### Requirement: DiagnosisCard shows synthesized conclusion (DP103)

The top component SHALL display a text-only card (no axes) containing: title (direction), badge (institutional profile), and summary (concatenated narrative from all classifiers).

#### Scenario: Card shows direction as title

- **WHEN** DirectionDiagnosis.title is "Pregão Comprador"
- **THEN** the card SHALL display "Pregão Comprador" as the title text

#### Scenario: Card shows institutional badge

- **WHEN** InstitutionalDiagnosis.badge is "Institucional"
- **THEN** the card SHALL display the badge text below the title

#### Scenario: Card shows concatenated summary

- **WHEN** all five classifiers produce narratives
- **THEN** the card SHALL display a summary paragraph that concatenates the conviction, money flow, and liquidity phrases

### Requirement: ClassificationBars show four categorical levels (DP104)

The ClassificationBars component SHALL display four horizontal bars for Fluxo, Convicção, Liquidez, and Institucional, each showing one of five discrete width levels derived from the classifier output.

#### Scenario: Four bars rendered with correct level widths

- **WHEN** all classifiers return a level classification
- **THEN** the component SHALL display four labeled bars: Fluxo, Convicção, Liquidez, Institucional, each with width proportional to its level (Muito Baixo through Muito Alto)

### Requirement: PriceRangeDiagram shows single-day range (DP105)

The PriceRangeDiagram component SHALL display a single horizontal line representing the current day's [Min, Max] range normalized to [0%, 100%], with markers for VWAP, Median Price, Typical Price, Weighted Close, and Close.

#### Scenario: All markers positioned correctly

- **WHEN** daily data is available for the selected ticker
- **THEN** the diagram SHALL display markers for Median (M), Typical (T), VWAP (V), Weighted Close (W), and Close (●) positioned according to their normalized values within the range

### Requirement: BuySellBar shows buying vs selling pressure (DP106)

The BuySellBar component SHALL display a stacked horizontal bar showing the proportion of Buying Pressure vs Selling Pressure for the current day.

#### Scenario: Stacked bar with labels

- **WHEN** buying_pressure and selling_pressure are available
- **THEN** the component SHALL display a stacked bar with green (buy) and red (sell) segments, each labeled with its percentage

### Requirement: CLVGauge shows close location value (DP107)

The CLVGauge component SHALL display a horizontal gauge on a scale from -1 to +1 showing the Close Location Value for the current day.

#### Scenario: Gauge filled from center to CLV

- **WHEN** CLV is available
- **THEN** the gauge SHALL display a filled segment from 0 to the CLV value, colored green for positive and red for negative
