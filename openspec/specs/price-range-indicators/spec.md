## Purpose

Define price range indicators that characterize the daily price interval and central tendency of each ticker, serving as building blocks for higher-level indicators.

## Requirements

### Requirement: Cálculo do Range (FS002)

O sistema DEVE calcular o Range diário como a diferença entre Preço Máximo e Preço Mínimo de cada ticker em cada dia.

#### Scenario: Range positivo

- **WHEN** um ticker tem MaxPric = 78.88 e MinPric = 77.91 em um dia
- **THEN** o Range DEVE ser 0.97

#### Scenario: Range zero (preço não variou)

- **WHEN** MaxPric = MinPric em um dia
- **THEN** o Range DEVE ser 0

### Requirement: Cálculo do Range Percentual (FS003)

O sistema DEVE calcular o Range Percentual como Range dividido pelo Preço Referência (avg_price), expressando a amplitude como proporção do preço médio.

#### Scenario: Range Percentual típico

- **WHEN** Range = 0.97 e avg_price = 78.15
- **THEN** o Range Percentual DEVE ser 0.97 / 78.15 = 0.0124

#### Scenario: Range Percentual com avg_price zero

- **WHEN** avg_price = 0
- **THEN** o Range Percentual DEVE retornar None

### Requirement: Cálculo do Typical Price (FS004)

O sistema DEVE calcular o Typical Price como (Máxima + Mínima + Fechamento) / 3 para cada ticker em cada dia.

#### Scenario: Typical Price típico

- **WHEN** MaxPric = 78.88, MinPric = 77.91, LastPric = 78.15
- **THEN** Typical Price DEVE ser (78.88 + 77.91 + 78.15) / 3 = 78.3133

### Requirement: Cálculo do Median Price (FS005)

O sistema DEVE calcular o Median Price como (Máxima + Mínima) / 2 para cada ticker em cada dia.

#### Scenario: Median Price típico

- **WHEN** MaxPric = 78.88, MinPric = 77.91
- **THEN** Median Price DEVE ser (78.88 + 77.91) / 2 = 78.395

### Requirement: Cálculo do Weighted Close (FS006)

O sistema DEVE calcular o Weighted Close como (Máxima + Mínima + 2 × Fechamento) / 4 para cada ticker em cada dia.

#### Scenario: Weighted Close típico

- **WHEN** MaxPric = 78.88, MinPric = 77.91, LastPric = 78.15
- **THEN** Weighted Close DEVE ser (78.88 + 77.91 + 2 × 78.15) / 4 = 78.2725

#### Scenario: Fechamento igual à máxima

- **WHEN** LastPric = MaxPric = 78.88, MinPric = 77.91
- **THEN** Weighted Close DEVE ser (78.88 + 77.91 + 2 × 78.88) / 4 = 78.6375
