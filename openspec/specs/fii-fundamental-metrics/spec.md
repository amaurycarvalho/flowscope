# fii-fundamental-metrics Specification

## Purpose
Calcular deterministicamente as métricas fundamentalistas de FIIs elegíveis (tijolo/híbrido) — FFO Yield, Dividend Yield, P/FFO, P/VP, FFO Momentum, número de cotistas e patrimônio — com evidência por métrica, conforme as RFC-006/007.

## Requirements

### Requirement: Valor de mercado
O sistema DEVE calcular o valor de mercado como `price × shares_outstanding`, usando `decimal.Decimal` e precisão completa, sem arredondamento intermediário.

#### Scenario: Cálculo do valor de mercado
- **WHEN** price é `18,74` e shares_outstanding é `144355726`
- **THEN** o valor de mercado DEVE ser `18,74 × 144355726`

### Requirement: FFO Yield
O sistema DEVE calcular o FFO Yield como `FFO_12M / MarketValue`, armazenando o valor em decimal e apresentando como percentual com 2 casas decimais.

#### Scenario: FFO Yield calculado
- **WHEN** FFO_12M é `220777000` e MarketValue é `2705230000`
- **THEN** o FFO Yield DEVE ser aproximadamente `0,0816` (8,16%)

#### Scenario: FFO negativo
- **WHEN** FFO_12M é menor ou igual a zero
- **THEN** o FFO Yield DEVE ser `N/A`

### Requirement: P/FFO
O sistema DEVE calcular o P/FFO como `MarketValue / FFO_12M`.

#### Scenario: P/FFO calculado
- **WHEN** MarketValue é `2705230000` e FFO_12M é `220777000`
- **THEN** o P/FFO DEVE ser aproximadamente `12,25`

#### Scenario: P/FFO com FFO não positivo
- **WHEN** FFO_12M é menor ou igual a zero
- **THEN** o P/FFO DEVE ser `N/A`

### Requirement: P/VP
O sistema DEVE calcular o P/VP como `MarketValue / NetAssetValue`, onde NetAssetValue é o patrimônio líquido.

#### Scenario: P/VP calculado
- **WHEN** MarketValue é `2705230000` e NetAssetValue é `2942000000`
- **THEN** o P/VP DEVE ser aproximadamente `0,92`

#### Scenario: Patrimônio líquido não positivo
- **WHEN** NetAssetValue é menor ou igual a zero
- **THEN** o P/VP DEVE ser `N/A`

### Requirement: Dividend Yield (12 meses)
O sistema DEVE calcular o Dividend Yield como `Dividends_12M / MarketValue`, usando rendimentos efetivamente distribuídos nos últimos 12 meses.

#### Scenario: Dividend Yield calculado
- **WHEN** Dividends_12M é `213080000` e MarketValue é `2705230000`
- **THEN** o Dividend Yield DEVE ser aproximadamente `0,084` (8,4%)

### Requirement: Consistência entre P/FFO e FFO Yield
O sistema DEVE verificar que `P/FFO × FFO Yield ≈ 1` dentro de uma tolerância configurada; em caso de violação, DEVE gerar uma indicação de `DATA_INCONSISTENCY`.

#### Scenario: Consistência mantida
- **WHEN** P/FFO é `12,25` e FFO Yield é `0,0816`
- **THEN** o produto DEVE estar dentro da tolerância de 1

### Requirement: FFO Momentum
O sistema DEVE calcular o FFO Momentum como `(FFO_3M × 4) / FFO_12M − 1`.

#### Scenario: FFO Momentum calculado
- **WHEN** FFO_3M é `63802000` e FFO_12M é `220777000`
- **THEN** o FFO Momentum DEVE ser aproximadamente `0,156` (+15,6%)

#### Scenario: FFO Momentum com FFO não positivo
- **WHEN** FFO_12M é menor ou igual a zero
- **THEN** o FFO Momentum DEVE ser `N/A`

### Requirement: Classificação da tendência do FFO
O sistema DEVE classificar o FFO Momentum em faixas determinísticas e configuráveis: `FORTE_ALTA` (≥ +20%), `ALTA` (≥ +5%), `ESTAVEL` (> −5%), `QUEDA` (≥ −20%) e `FORTE_QUEDA` (< −20%).

#### Scenario: Tendência alta
- **WHEN** o FFO Momentum é `0,156`
- **THEN** a classificação DEVE ser `ALTA`

#### Scenario: Tendência em forte queda
- **WHEN** o FFO Momentum é menor que `−0,20`
- **THEN** a classificação DEVE ser `FORTE_QUEDA`

### Requirement: Classificação por número de cotistas
O sistema DEVE classificar o número de cotistas em faixas determinísticas (`MICRO`, `MUITO_PEQUENO`, `PEQUENO`, `MEDIO`, `GRANDE`, `MUITO_GRANDE`, `GIGANTE`) conforme os limiares fixos da RFC-006.

#### Scenario: Cotistas em faixa média
- **WHEN** o número de cotistas está entre 5.001 e 35.000
- **THEN** a classificação DEVE ser `MEDIO`

### Requirement: Classificação por tamanho patrimonial
O sistema DEVE classificar o patrimônio líquido em faixas determinísticas (`MICRO`, `PEQUENO`, `MEDIO`, `GRANDE`, `MUITO_GRANDE`, `GIGANTE`) conforme os limiares fixos da RFC-006.

#### Scenario: Patrimônio em faixa grande
- **WHEN** o patrimônio líquido está entre R$ 250 milhões e R$ 500 milhões
- **THEN** a classificação DEVE ser `GRANDE`

### Requirement: Evidência por métrica
O sistema DEVE produzir, para cada métrica calculada, uma evidência contendo métrica, valor, fórmula, valores de entrada, fontes, data de referência e versão de cálculo.

#### Scenario: Evidência do FFO Yield
- **WHEN** o FFO Yield é calculado
- **THEN** DEVE existir evidência registrando a fórmula `ffo_12m / market_value`, os valores de entrada e as fontes utilizadas

### Requirement: Não elegível gera N/A
O sistema DEVE retornar `N/A` para todas as métricas FFO quando o ativo não é um FII elegível (tijolo/híbrido).

#### Scenario: Ação gera N/A nas métricas FFO
- **WHEN** um ativo do tipo `ACAO` é analisado
- **THEN** FFO Yield, Dividend Yield, P/FFO, P/VP e FFO Momentum DEVEM ser `N/A`
