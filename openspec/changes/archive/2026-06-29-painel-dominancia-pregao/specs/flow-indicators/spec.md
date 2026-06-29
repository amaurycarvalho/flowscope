## ADDED Requirements

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
