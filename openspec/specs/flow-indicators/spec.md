## Purpose

Define flow indicators that capture the directional bias of trading activity — buying vs selling pressure, money flow, and close location within the day's range.

## Requirements

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

### Requirement: Cálculo do Daily Money Flow (FS206)

O sistema DEVE calcular o Daily Money Flow como CLV × Volume Financeiro (FinVol) para cada ticker em cada dia, retornando um valor diário (não acumulado).

#### Scenario: Daily Money Flow positivo

- **WHEN** CLV = 0.3 e fin_vol = 1.000.000 para um ticker em um dia
- **THEN** Daily Money Flow DEVE ser 300.000

#### Scenario: Daily Money Flow negativo

- **WHEN** CLV = −0.3 e fin_vol = 1.000.000
- **THEN** Daily Money Flow DEVE ser −300.000

#### Scenario: CLV é None

- **WHEN** Range = 0 (CLV é None)
- **THEN** Daily Money Flow DEVE ser None

### Requirement: Cálculo do Dominance Score (FS207)

O sistema DEVE calcular o Dominance Score como CLV × Daily Efficiency para cada ticker em cada dia, variando de −1 a +1.

#### Scenario: Compra convincente

- **WHEN** CLV = +0.80 e Daily Efficiency = 0.90
- **THEN** Dominance Score DEVE ser +0.72

#### Scenario: Compra não convincente

- **WHEN** CLV = +0.80 e Daily Efficiency = 0.20
- **THEN** Dominance Score DEVE ser +0.16

#### Scenario: Range zero

- **WHEN** Range = 0 (CLV é None ou Efficiency é None)
- **THEN** Dominance Score DEVE ser None

### Requirement: Dependências no DAG (FS208)

O sistema DEVE registrar as novas strategies no DAG do IndicatorEngine com as dependências corretas.

#### Scenario: DailyMoneyFlowStrategy depende de clv

- **WHEN** o engine executa
- **THEN** `daily_money_flow` DEVE ser executado após `clv`

#### Scenario: DominanceScoreStrategy depende de clv e daily_efficiency

- **WHEN** o engine executa
- **THEN** `dominance_score` DEVE ser executado após `clv` e `daily_efficiency`

### Requirement: Integração na saída do use case (FS209)

As novas strategies DEVEM estar disponíveis em `all_indicators` no resultado do `AnalyzeTickersUseCase`, seguindo o mesmo padrão dos demais indicadores (excluídas apenas vwap, volume_profile, top_tickers).

#### Scenario: Acesso pelo painel

- **WHEN** um painel acessa `data["all_indicators"]["dominance_score"]`
- **THEN** DEVE receber o dicionário {ticker: {date: value}} para o ticker selecionado
