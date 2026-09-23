# short-interest Specification

## Purpose

Calcular deterministicamente as métricas de *short interest* — Shorts% e Short Interest Ratio — e classificá-las em escalas qualitativas de sentimento e de risco de fechamento, normalizando o estoque de empréstimos pelo *free float* e pelo volume de negociação.

## Requirements

### Requirement: Shorts% (Short Interest sobre o free float)

O sistema DEVE calcular `Shorts% = (Ações Alugadas ÷ Free Float) × 100` como fração em `Decimal`, sem arredondamento intermediário, apresentada em notação percentual com uma casa decimal. O *free float* DEVE vir do CVM FRE (`Quantidade_Total_Acoes_Circulacao`). Quando o *free float* não estiver disponível para o ticker, o denominador DEVE ser o total emitido de ações/cotas. Insumo ausente ou denominador zero DEVEM resultar em `N/A`.

#### Scenario: Shorts% calculado com free float

- **WHEN** um ativo possui `10.000.000` ações alugadas e *free float* de `100.000.000`
- **THEN** o `Shorts%` DEVE ser `10,0%`

#### Scenario: Fallback para o total emitido

- **WHEN** o *free float* do ticker não está disponível e o total emitido é `200.000.000` com `10.000.000` ações alugadas
- **THEN** o `Shorts%` DEVE ser `5,0%`

#### Scenario: Insumo ausente

- **WHEN** as ações alugadas ou o denominador não estão disponíveis
- **THEN** o `Shorts%` DEVE ser `N/A`

#### Scenario: Denominador zero

- **WHEN** o denominador (*free float* ou total emitido) é zero
- **THEN** o `Shorts%` DEVE ser `N/A`

### Requirement: Classificação do volume de shorts

O sistema DEVE classificar o `Shorts%` em cinco rótulos determinísticos: `Inexistente` (igual a 0% ou `N/A`), `Muito Baixo` (maior que 0% e menor que 1%), `Baixo` (maior ou igual a 1% e menor que 3%), `Alto` (maior ou igual a 3% e menor ou igual a 10%) e `Muito Alto` (maior que 10%). Quando o `Shorts%` for `N/A`, a classificação DEVE ser `Inexistente`.

#### Scenario: Classificação muito alta

- **WHEN** o `Shorts%` é `25%`
- **THEN** o volume de shorts DEVE ser `Muito Alto`

#### Scenario: Classificação alta no limite

- **WHEN** o `Shorts%` é `10%`
- **THEN** o volume de shorts DEVE ser `Alto`

#### Scenario: Classificação inexistente

- **WHEN** o `Shorts%` é `0%`
- **THEN** o volume de shorts DEVE ser `Inexistente`

#### Scenario: Shorts% indisponível

- **WHEN** o `Shorts%` é `N/A`
- **THEN** a classificação DEVE ser `Inexistente`

### Requirement: Short Interest Ratio (Fechamento Shorts)

O sistema DEVE calcular `SIR = Ações Alugadas ÷ Volume Médio Diário de Negociação`, usando como volume médio a média diária da quantidade negociada dos dias disponíveis em memória para o ticker. O valor DEVE ser armazenado em `Decimal` e apresentado em dias, como razão com uma casa decimal e sufixo `d`. Quando não houver nenhum dia de negociação disponível, o volume médio for zero, ou as ações alugadas estiverem ausentes, o `SIR` DEVE ser `N/A`.

#### Scenario: SIR calculado

- **WHEN** um ativo possui `10.000.000` ações alugadas e volume médio diário de `2.000.000`
- **THEN** o `Fechamento Shorts` DEVE ser `5,0d`

#### Scenario: Sem volume em memória

- **WHEN** não há nenhum dia de negociação disponível para o ticker
- **THEN** o `Fechamento Shorts` DEVE ser `N/A`

#### Scenario: Volume médio zero

- **WHEN** o volume médio diário é zero
- **THEN** o `Fechamento Shorts` DEVE ser `N/A`

### Requirement: Classificação do risco de fechamento

O sistema DEVE classificar o `SIR` em cinco rótulos determinísticos: `Inexistente` (igual a 0 ou `N/A`), `Muito Baixo` (maior que 0 e menor que 2), `Baixo` (maior ou igual a 2 e menor que 4), `Alto` (maior ou igual a 4 e menor ou igual a 5) e `Muito Alto` (maior que 5). Quando o `SIR` for `N/A`, a classificação DEVE ser `Inexistente`.

#### Scenario: Risco muito alto

- **WHEN** o `SIR` é `6`
- **THEN** o risco de fechamento DEVE ser `Muito Alto`

#### Scenario: Risco alto no limite

- **WHEN** o `SIR` é `5`
- **THEN** o risco de fechamento DEVE ser `Alto`

#### Scenario: Risco inexistente

- **WHEN** o `SIR` é `0`
- **THEN** o risco de fechamento DEVE ser `Inexistente`

#### Scenario: SIR indisponível

- **WHEN** o `SIR` é `N/A`
- **THEN** a classificação DEVE ser `Inexistente`

### Requirement: Escopo por tipo de ativo e independência das colunas

O sistema DEVE calcular as métricas de *short interest* para ativos do tipo `Papel` (ação), usando o *free float* real, e para ativos do tipo `FII`, usando o total de cotas como denominador do `Shorts%`. Ativos sem estoque de empréstimos ou sem denominador aplicável DEVEM exibir `N/A` nas colunas numéricas (`Shorts%` e `Fechamento Shorts`) e `Inexistente` nas colunas de classificação (`Volume de Shorts` e `Risco Fechamento`). A ausência de um insumo DEVE afetar apenas a coluna que depende dele, sem impedir as demais métricas da linha.

#### Scenario: FII usa o total de cotas

- **WHEN** um FII possui `1.000.000` cotas alugadas e `50.000.000` cotas emitidas
- **THEN** o `Shorts%` DEVE ser `2,0%`

#### Scenario: Ativo sem dados de short interest

- **WHEN** um ativo não possui estoque de empréstimos disponível
- **THEN** `Shorts%` e `Fechamento Shorts` DEVEM exibir `N/A` e `Volume de Shorts` e `Risco Fechamento` DEVEM exibir `Inexistente`, sem afetar as demais colunas da linha

#### Scenario: Ações alugadas ausentes

- **WHEN** as ações alugadas estão ausentes, mas o denominador e o volume estão disponíveis
- **THEN** `Shorts%` e `Fechamento Shorts` DEVEM ser `N/A` e `Volume de Shorts` e `Risco Fechamento` DEVEM ser `Inexistente`
