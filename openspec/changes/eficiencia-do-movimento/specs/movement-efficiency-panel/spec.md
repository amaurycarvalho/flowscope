## ADDED Requirements

### Requirement: Panel layout and structure
The system SHALL provide an "Eficiência do Movimento" sub-aba under "Análise do Ticker" containing a panel with three vertically stacked components: a classification card, a horizontal gauge, and a history chart. The panel SHALL render using a matplotlib GridSpec with `height_ratios=[2, 1, 3]`.

#### Scenario: Panel renders with correct layout
- **WHEN** user selects a ticker and navigates to "Eficiência do Movimento" sub-aba
- **THEN** the panel SHALL display three components: card (top), gauge (middle), history (bottom)

#### Scenario: Panel shows empty state when no data
- **WHEN** no ticker is selected or no data is available
- **THEN** the panel SHALL display a centered "Sem dados" message

### Requirement: Classification card
The system SHALL display a classification card at the top of the panel. The card SHALL show the classification title, the efficiency value as a percentage, and an automatically generated explanatory text based on the efficiency level. The card SHALL have a colored border matching the classification level.

#### Scenario: Card displays Muito Baixa classification
- **WHEN** daily efficiency is 0.12 (between 0.00 and 0.20)
- **THEN** the card SHALL display "Muito Baixa" as classification, "12%" as value, and the text "O preço percorreu uma grande faixa, mas terminou próximo do ponto de partida. A volatilidade pouco contribuiu para um avanço efetivo."

#### Scenario: Card displays Baixa classification
- **WHEN** daily efficiency is 0.30 (between 0.20 and 0.40)
- **THEN** the card SHALL display "Baixa" as classification, "30%" as value, and the text "Houve bastante oscilação durante o pregão, porém apenas uma pequena parcela resultou em deslocamento líquido."

#### Scenario: Card displays Moderada classification
- **WHEN** daily efficiency is 0.50 (between 0.40 and 0.60)
- **THEN** the card SHALL display "Moderada" as classification, "50%" as value, and the text "Parte relevante da volatilidade foi convertida em movimento efetivo, mas ainda houve bastante disputa ao longo do dia."

#### Scenario: Card displays Alta classification
- **WHEN** daily efficiency is 0.70 (between 0.60 and 0.80)
- **THEN** the card SHALL display "Alta" as classification, "70%" as value, and the text "A maior parte da amplitude diária resultou em deslocamento consistente do preço, indicando um movimento convincente."

#### Scenario: Card displays Muito Alta classification
- **WHEN** daily efficiency is 0.90 (above 0.80)
- **THEN** the card SHALL display "Muito Alta" as classification, "90%" as value, and the text "O pregão utilizou quase toda a volatilidade para avançar em uma única direção, sinalizando forte convicção dos participantes."

### Requirement: Horizontal gauge
The system SHALL display a horizontal gauge below the card. The gauge SHALL span from 0 to 1 on the x-axis. The gauge SHALL have three colored zones: red (#CC4444) from 0 to 0.30 labeled "Ruído", yellow (#CCAA44) from 0.30 to 0.60 labeled "Intermediário", and green (#44AA66) from 0.60 to 1.00 labeled "Progresso". A triangular marker SHALL indicate the current efficiency value.

#### Scenario: Gauge displays marker at correct position
- **WHEN** daily efficiency is 0.75
- **THEN** the gauge SHALL show a triangular marker at position 0.75 on the x-axis, within the green zone

#### Scenario: Gauge shows correct labels
- **WHEN** the gauge is rendered
- **THEN** the gauge SHALL display "Ruído" on the left end and "Progresso" on the right end

### Requirement: History chart
The system SHALL display a horizontal bar chart below the gauge. Each bar SHALL represent one pregão, ordered from most recent (top) to oldest (bottom). The system SHALL show the last 15 pregões. The bar length SHALL represent the efficiency value (0 to 1). Each bar SHALL be colored according to its efficiency value: red for ≤0.30, yellow for 0.30–0.60, green for >0.60. The current day's bar SHALL be visually highlighted (darker shade or outline).

#### Scenario: History shows correct number of bars
- **WHEN** the ticker has 20 pregões of data
- **THEN** the history chart SHALL display exactly 15 bars, most recent at top

#### Scenario: Bars display correct colors
- **WHEN** efficiency values are 0.15, 0.45, and 0.85
- **THEN** the 0.15 bar SHALL be red, the 0.45 bar SHALL be yellow, and the 0.85 bar SHALL be green

#### Scenario: Current day bar is highlighted
- **WHEN** the history chart is rendered
- **THEN** the most recent bar SHALL have a visually distinct style (darker shade) compared to older bars

### Requirement: Tooltip on hover
The system SHALL display a tooltip when the user hovers over any bar in the history chart. The tooltip SHALL show the date, efficiency value, range, range percentual, CLV, closing price, and average price for that pregão.

#### Scenario: Tooltip appears on hover
- **WHEN** user hovers mouse over a history bar
- **THEN** a tooltip SHALL appear showing that day's date, efficiency, range, range%, CLV, close price, and average price

### Requirement: Indicator data
The system SHALL use `daily_efficiency` as the primary indicator. The system SHALL also load `range`, `range_percentual`, and `clv` from `all_indicators` for tooltip display.

#### Scenario: Panel loads required indicators
- **WHEN** the panel updates for a ticker
- **THEN** the panel SHALL read `daily_efficiency`, `range`, `range_percentual`, and `clv` from the ticker's `all_indicators`

### Requirement: Tab registration
The system SHALL register the "Eficiência do Movimento" sub-aba as enabled (not disabled) in the "Análise do Ticker" notebook.

#### Scenario: Tab is selectable
- **WHEN** user navigates to "Análise do Ticker"
- **THEN** the "Eficiência do Movimento" tab SHALL be enabled and selectable

### Requirement: Orientation text
The system SHALL display orientation text when the "Eficiência do Movimento" tab is selected. The orientation SHALL explain the objective, the question answered, the indicators involved, and how to interpret the panel.

#### Scenario: Orientation updates on tab select
- **WHEN** user selects "Eficiência do Movimento" sub-aba
- **THEN** the orientation panel SHALL show content matching this capability

### Requirement: Efficiency classifier
The system SHALL provide a `classify_efficiency()` function that maps a numeric efficiency value to one of five classification levels with associated label, short label, color, and explanatory text.

#### Scenario: Classifier returns correct level for each threshold
- **WHEN** efficiency is 0.10, 0.30, 0.50, 0.70, and 0.90
- **THEN** the classifier SHALL return "Muito Baixa", "Baixa", "Moderada", "Alta", and "Muito Alta" respectively
