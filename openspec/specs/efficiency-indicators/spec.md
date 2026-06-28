## Purpose

Define efficiency indicators that measure how effectively price moves relative to its range, indicating the directional conviction of a trading session.

## Requirements

### Requirement: Cálculo do Daily Efficiency (FS301)

O sistema DEVE calcular o Daily Efficiency como o valor absoluto de (Fechamento − Preço Referência) dividido pelo Range, onde Preço Referência = avg_price.

#### Scenario: Movimento unidirecional

- **WHEN** LastPric = 78.15, avg_price = 78.40, Range = 0.97
- **THEN** Daily Efficiency DEVE ser |78.15 − 78.40| / 0.97 = 0.2577

#### Scenario: Pregão lateral (fechamento próximo ao preço médio)

- **WHEN** LastPric ≈ avg_price, Range = 1.00
- **THEN** Daily Efficiency DEVE ser próximo de 0

#### Scenario: Range zero

- **WHEN** Range = 0
- **THEN** Daily Efficiency DEVE retornar None

#### Scenario: Fechamento igual ao preço de referência

- **WHEN** LastPric = avg_price
- **THEN** Daily Efficiency DEVE ser 0
