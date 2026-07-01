## Purpose

The Price Range Panel provides visual analysis of a ticker's daily price amplitude, helping traders assess whether the price merely oscillated or exhibited a convincing directional movement during the trading session.

## Requirements

### Requirement: Price Range Timeline Chart (FS601)

The system SHALL display a Price Range Timeline chart as the main component of the Amplitude de Preço panel.

#### Scenario: Chart shows today's range with markers

- **WHEN** a ticker has daily_data with min_price, max_price, last_price for the current session
- **THEN** the chart SHALL display a horizontal band representing [Min, Max] normalized to [0%, 100%], with markers for Median Price, Typical Price, VWAP, Weighted Close, and Close (●) positioned according to their normalized values

#### Scenario: Only current day shows full markers

- **WHEN** multiple days of data are available
- **THEN** the current (latest) day SHALL display all markers (Median, Typical, VWAP, Weighted Close, Close) with labels, and previous days SHALL display only the Close marker (●)

#### Scenario: Y-axis lists dates chronologically

- **WHEN** multiple days are displayed
- **THEN** each day SHALL occupy one row on the Y-axis, ordered chronologically with the most recent date at the top

#### Scenario: Close positions connected by arrows

- **WHEN** consecutive days have valid close data
- **THEN** arrows SHALL connect the Close marker of each day to the Close marker of the following day, showing the trajectory

#### Scenario: Minimum data period

- **WHEN** fewer than 2 days of data are available
- **THEN** the chart SHALL display the available data without arrows

### Requirement: Range % Histórico (FS602)

The system SHALL display a line chart of Range % over the available period.

#### Scenario: Line chart shows range percentual over time

- **WHEN** daily Range% data is available for the ticker
- **THEN** a line chart SHALL plot Range% on the Y-axis against dates on the X-axis, covering the available period (up to 30 sessions)

#### Scenario: Current day highlighted

- **WHEN** the line chart is displayed
- **THEN** the current day's point SHALL be highlighted with a distinct marker

### Requirement: Gauge de Eficiência (FS603)

The system SHALL display a horizontal gauge of Daily Efficiency.

#### Scenario: Gauge shows efficiency value

- **WHEN** Daily Efficiency is available for the current day
- **THEN** a horizontal gauge SHALL display the value on a scale from 0 to 1, with a filled bar proportional to the value

#### Scenario: Efficiency gauge color

- **WHEN** Daily Efficiency ≤ 0.30
- **THEN** the filled bar SHALL use a muted/neutral color
- **WHEN** Daily Efficiency > 0.30 AND ≤ 0.60
- **THEN** the filled bar SHALL use a moderate color
- **WHEN** Daily Efficiency > 0.60
- **THEN** the filled bar SHALL use a strong/conviction color

### Requirement: Gauge de CLV (FS604)

The system SHALL display a horizontal gauge of Close Location Value.

#### Scenario: Gauge shows CLV value

- **WHEN** CLV is available for the current day
- **THEN** a horizontal gauge SHALL display the value on a scale from -1 to +1, with a filled bar from the center (0) to the CLV value

#### Scenario: CLV gauge color

- **WHEN** CLV > 0
- **THEN** the filled bar SHALL use a buying-pressure color (green)
- **WHEN** CLV < 0
- **THEN** the filled bar SHALL use a selling-pressure color (red)
- **WHEN** CLV = 0
- **THEN** the gauge SHALL show no fill

### Requirement: Classificação Qualitativa (FS605)

The system SHALL display a qualitative classification of the trading session based on Range% and Daily Efficiency.

#### Scenario: Classification displayed as annotation

- **WHEN** both Range% and Daily Efficiency are available
- **THEN** the classification text SHALL be displayed as an annotation in the Price Range Timeline chart area

#### Scenario: Classification categories

- **WHEN** Range% ≤ historical median AND Daily Efficiency ≤ 0.30
- **THEN** the classification SHALL be "Pregão Lateral"
- **WHEN** Range% > historical median AND Daily Efficiency ≤ 0.30
- **THEN** the classification SHALL be "Volatilidade sem Direção"
- **WHEN** Range% ≤ historical median AND Daily Efficiency > 0.30
- **THEN** the classification SHALL be "Movimento Consistente"
- **WHEN** Range% > historical median AND Daily Efficiency > 0.30
- **THEN** the classification SHALL be "Movimento Direcional Forte"

### Requirement: Integration with GUI (FS606)

The system SHALL integrate the Price Range Panel into the "Análise do Ticker" notebook under the "Amplitude de Preço" tab.

#### Scenario: Tab is enabled

- **WHEN** the application starts
- **THEN** the "Amplitude de Preço" tab SHALL be enabled and selectable

#### Scenario: Panel updates on ticker selection

- **WHEN** a ticker is selected AND data is available
- **THEN** the Price Range Panel SHALL update to display data for the selected ticker

#### Scenario: Panel updates on data load

- **WHEN** new data is loaded
- **THEN** the Price Range Panel SHALL refresh to display the updated data

### Requirement: Orientation Text (FS607)

The system SHALL display updated orientation text for the Amplitude de Preço panel.

#### Scenario: Orientation explains the question answered

- **WHEN** the "Amplitude de Preço" tab is selected
- **THEN** the orientation panel SHALL display text explaining that the panel answers "O preço apenas oscilou ou houve um movimento direcional convincente durante o pregão?"

#### Scenario: Orientation explains indicators

- **WHEN** the "Amplitude de Preço" tab is selected
- **THEN** the orientation panel SHALL explain Range, Range%, CLV, Daily Efficiency, Median Price, Typical Price, Weighted Close, and VWAP in the context of the visual panel
