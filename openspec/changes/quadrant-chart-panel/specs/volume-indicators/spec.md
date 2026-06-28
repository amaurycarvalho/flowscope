## ADDED Requirements

### Requirement: Cálculo do VWAP Distance como indicador derivado

O sistema DEVE calcular o VWAP Distance para cada ticker em cada dia como `(LastPric - TradAvrgPric) / TradAvrgPric`. O indicador depende do `vwap` existente, utilizando o `daily_vwap` de cada data como denominador.

#### Scenario: VWAP Distance positivo

- **WHEN** LastPric = 52.50 e TradAvrgPric = 50.00
- **THEN** VWAP Distance DEVE ser (52.50 - 50.00) / 50.00 = 0.05

#### Scenario: VWAP Distance negativo

- **WHEN** LastPric = 48.00 e TradAvrgPric = 50.00
- **THEN** VWAP Distance DEVE ser (48.00 - 50.00) / 50.00 = -0.04
