## Purpose

Define trade size indicators that measure the average volume and financial value per trade, providing insights into institutional participation vs retail activity.

## Requirements

### Requirement: Cálculo do Average Trade Size (FS101)

O sistema DEVE calcular o Average Trade Size como Quantidade Negociada dividida pelo Número de Negócios para cada ticker em cada dia.

#### Scenario: Average Trade Size típico

- **WHEN** fin_instr_qty = 25.251.100 e trades_qty = 20.509
- **THEN** Average Trade Size DEVE ser 25.251.100 / 20.509 = 1.231

#### Scenario: Número de Negócios zero

- **WHEN** trades_qty = 0
- **THEN** Average Trade Size DEVE retornar None

### Requirement: Cálculo do Average Financial Ticket (FS102)

O sistema DEVE calcular o Average Financial Ticket como Volume Financeiro dividido pelo Número de Negócios para cada ticker em cada dia.

#### Scenario: Average Financial Ticket típico

- **WHEN** fin_vol = 1.979.684.547 e trades_qty = 20.509
- **THEN** Average Financial Ticket DEVE ser 1.979.684.547 / 20.509 = 96.527

#### Scenario: Número de Negócios zero

- **WHEN** trades_qty = 0
- **THEN** Average Financial Ticket DEVE retornar None
