## Purpose

Define density indicators that measure the concentration of volume, trades, and financial value relative to price range, providing insights into the intensity of trading activity per unit of price movement.

## Requirements

### Requirement: Cálculo do Financial Density (FS401)

O sistema DEVE calcular o Financial Density como Volume Financeiro dividido pelo Range para cada ticker em cada dia.

#### Scenario: Financial Density típico

- **WHEN** fin_vol = 1.979.684.547 e Range = 0.97
- **THEN** Financial Density DEVE ser 1.979.684.547 / 0.97 = 2.040.911.904

#### Scenario: Range zero

- **WHEN** Range = 0
- **THEN** Financial Density DEVE retornar None

### Requirement: Cálculo do Trade Density (FS402)

O sistema DEVE calcular o Trade Density como Número de Negócios dividido pelo Range para cada ticker em cada dia.

#### Scenario: Trade Density típico

- **WHEN** trades_qty = 20.509 e Range = 0.97
- **THEN** Trade Density DEVE ser 20.509 / 0.97 = 21.143

#### Scenario: Range zero

- **WHEN** Range = 0
- **THEN** Trade Density DEVE retornar None

### Requirement: Cálculo do Volume Density (FS403)

O sistema DEVE calcular o Volume Density como Quantidade Negociada dividida pelo Range para cada ticker em cada dia.

#### Scenario: Volume Density típico

- **WHEN** fin_instr_qty = 25.251.100 e Range = 0.97
- **THEN** Volume Density DEVE ser 25.251.100 / 0.97 = 26.032.062

#### Scenario: Range zero

- **WHEN** Range = 0
- **THEN** Volume Density DEVE retornar None
