## ADDED Requirements

### Requirement: Cálculo do CLV — Close Location Value (FS201)

O sistema DEVE calcular o CLV como ((Fechamento − Mínima) − (Máxima − Fechamento)) / (Máxima − Mínima) para cada ticker em cada dia.

#### Scenario: Fechamento no centro do range

- **WHEN** MaxPric = 80, MinPric = 70, LastPric = 75
- **THEN** CLV DEVE ser ((75 − 70) − (80 − 75)) / (80 − 70) = 0

#### Scenario: Fechamento na máxima

- **WHEN** LastPric = MaxPric = 80, MinPric = 70
- **THEN** CLV DEVE ser ((80 − 70) − (80 − 80)) / (80 − 70) = 1

#### Scenario: Fechamento na mínima

- **WHEN** LastPric = MinPric = 70, MaxPric = 80
- **THEN** CLV DEVE ser ((70 − 70) − (80 − 70)) / (80 − 70) = −1

#### Scenario: Range zero (preço não variou)

- **WHEN** MaxPric = MinPric = 75
- **THEN** CLV DEVE retornar None

### Requirement: Cálculo do Money Flow Multiplier (FS204)

O sistema DEVE calcular o Money Flow Multiplier como exatamente o mesmo valor do CLV para o mesmo ticker no mesmo dia.

#### Scenario: MFM igual ao CLV

- **WHEN** CLV = 0.3 para um ticker em um dia
- **THEN** Money Flow Multiplier DEVE ser 0.3

### Requirement: Cálculo do Money Flow Volume (FS205)

O sistema DEVE calcular o Money Flow Volume como Money Flow Multiplier × Volume Financeiro para cada ticker.

#### Scenario: MFV positivo (viés comprador)

- **WHEN** MFM = 0.3 e fin_vol = 1.000.000
- **THEN** MFV DEVE ser 300.000

#### Scenario: MFV negativo (viés vendedor)

- **WHEN** MFM = −0.3 e fin_vol = 1.000.000
- **THEN** MFV DEVE ser −300.000

#### Scenario: MFV acumulado no período

- **WHEN** um ticker tem dados em 3 dias com MFV diário 100.000, 50.000 e −30.000
- **THEN** o MFV acumulado DEVE ser 120.000

### Requirement: Cálculo do Buying Pressure Index (FS202)

O sistema DEVE calcular o Buying Pressure Index como (Fechamento − Mínima) / (Máxima − Mínima) para cada ticker em cada dia.

#### Scenario: Buying Pressure na máxima

- **WHEN** LastPric = MaxPric = 80, MinPric = 70
- **THEN** Buying Pressure DEVE ser (80 − 70) / (80 − 70) = 1

#### Scenario: Buying Pressure na mínima

- **WHEN** LastPric = MinPric = 70, MaxPric = 80
- **THEN** Buying Pressure DEVE ser (70 − 70) / (80 − 70) = 0

### Requirement: Cálculo do Selling Pressure Index (FS203)

O sistema DEVE calcular o Selling Pressure Index como (Máxima − Fechamento) / (Máxima − Mínima) para cada ticker em cada dia.

#### Scenario: Relação Buying + Selling Pressure = 1

- **WHEN** Buying Pressure = 0.3 para um dia
- **THEN** Selling Pressure DEVE ser 0.7

#### Scenario: Selling Pressure na máxima

- **WHEN** LastPric = MaxPric = 80, MinPric = 70
- **THEN** Selling Pressure DEVE ser (80 − 80) / (80 − 70) = 0
