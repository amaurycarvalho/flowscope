## MODIFIED Requirements

### Requirement: Cálculo do Cumulative Volume Delta (CVD)

A funcionalidade de CVD é substituída pelo Money Flow Volume (FS205), que utiliza CLV contínuo no lugar de sinal binário.

#### Scenario: Cálculo de CVD para um ticker

- **WHEN** existem dados de múltiplos dias para um ticker
- **THEN** o sistema DEVE calcular o Money Flow Volume acumulado no período, não mais o CVD

## REMOVED Requirements

### Requirement: Cálculo do Cumulative Volume Delta (CVD)

**Reason**: CVD usava sinal binário (±fin_vol baseado em last_price > avg_price). Money Flow Volume (FS205) substitui com CLV contínuo (range [-1, +1]) × fin_vol, capturando nuances que o CVD ignora.

**Migration**: Substituir chamadas a `calculate_cvd()` por `money_flow_volume` do novo engine DAG. O campo `cvd` no resultado do use case será substituído por `money_flow_volume`.

## ADDED Requirements

### Requirement: Cálculo do Money Flow Volume

O sistema DEVE calcular o Money Flow Volume para cada ticker como CLV × Volume Financeiro, acumulado ao longo dos dias da janela Fibonacci, substituindo o CVD.

#### Scenario: MFV acumulado no período

- **WHEN** um ticker possui dados em 3 dias com MFV diário de 200.000, 150.000 e −50.000
- **THEN** o MFV acumulado DEVE ser 300.000

#### Scenario: MFV com CLV = 0

- **WHEN** CLV = 0 em um dia (fechamento no centro do range)
- **THEN** o MFV daquele dia DEVE ser 0
