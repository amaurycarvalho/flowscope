## Purpose

Define the VWAP Distance indicator that measures the percentage deviation of the last price from the daily VWAP (TradAvrgPric), used as the Y-axis metric in the quadrant chart and for standalone analysis of price fairness at closing.

## Requirements

### Requirement: Cálculo do VWAP Distance

O sistema DEVE calcular o VWAP Distance para cada ticker em cada dia como `(LastPric - DailyVWAP) / DailyVWAP`, onde DailyVWAP é o TradAvrgPric (preço médio ponderado do dia).

#### Scenario: Fechamento acima do VWAP diário

- **WHEN** LastPric = 52.50 e TradAvrgPric = 50.00
- **THEN** VWAP Distance DEVE ser (52.50 - 50.00) / 50.00 = 0.05 (5%)

#### Scenario: Fechamento abaixo do VWAP diário

- **WHEN** LastPric = 48.00 e TradAvrgPric = 50.00
- **THEN** VWAP Distance DEVE ser (48.00 - 50.00) / 50.00 = -0.04 (-4%)

#### Scenario: Fechamento exatamente no VWAP

- **WHEN** LastPric = 50.00 e TradAvrgPric = 50.00
- **THEN** VWAP Distance DEVE ser 0.0 (0%)

### Requirement: Dependência do VWAP

O sistema DEVE calcular o VWAP Distance como indicador derivado, dependendo do indicador `vwap` para obter o `daily_vwap` de cada ticker em cada data.

#### Scenario: Registro da dependência

- **WHEN** o indicador é registrado no DAG engine
- **THEN** sua lista de dependências DEVE conter `["vwap"]`
