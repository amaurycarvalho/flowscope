## Purpose

Define volume-based indicators that measure trading activity, including volume-weighted average price, volume profile distribution, and money flow analysis.

## Requirements

### Requirement: Cálculo do Money Flow Volume

O sistema DEVE calcular o Money Flow Volume para cada ticker como CLV × Volume Financeiro, acumulado ao longo dos dias da janela Fibonacci, substituindo o CVD.

#### Scenario: MFV acumulado no período

- **WHEN** um ticker possui dados em 3 dias com MFV diário de 200.000, 150.000 e −50.000
- **THEN** o MFV acumulado DEVE ser 300.000

#### Scenario: MFV com CLV = 0

- **WHEN** CLV = 0 em um dia (fechamento no centro do range)
- **THEN** o MFV daquele dia DEVE ser 0

### Requirement: Cálculo do Volume Weighted Average Price (VWAP)

O sistema DEVE calcular o Volume Weighted Average Price para cada ticker usando a fórmula VWAP = Σ(TradAvrgPric × FinInstrmQty) / Σ(FinInstrmQty) por ticker, agregando todos os dias da janela Fibonacci. O VWAP de cada ticker representa o preço médio ponderado pela quantidade de instrumentos negociados no período.

#### Scenario: Cálculo de VWAP para um ticker com múltiplos dias

- **WHEN** um ticker possui dados em 5 dias da janela, com diferentes valores de TradAvrgPric e FinInstrmQty
- **THEN** o sistema DEVE calcular o VWAP do período como Σ(TradAvrgPric × FinInstrmQty) / Σ(FinInstrmQty), utilizando FinInstrmQty como peso

#### Scenario: Ticker com apenas um dia de dados

- **WHEN** um ticker aparece em apenas 1 dia da janela
- **THEN** o VWAP do período DEVE ser igual ao TradAvrgPric daquele único dia

#### Scenario: Ticker com FinInstrmQty zero

- **WHEN** um ticker possui FinInstrmQty = 0 em um dia da janela
- **THEN** aquele dia DEVE ser ignorado no cálculo (peso zero), mas os demais dias DEVEM ser considerados

### Requirement: Cálculo do Volume Profile

O sistema DEVE calcular o Volume Profile para cada ticker distribuindo o volume financeiro (NtlFinVol) em buckets de preço definidos pelo tick size do ativo, entre MinPric e MaxPric de cada dia.

#### Scenario: Volume Profile para um ticker

- **WHEN** um ticker possui dados com faixa de preço [MinPric, MaxPric] e volume NtlFinVol em um dia
- **THEN** o sistema DEVE distribuir o volume em buckets de tamanho igual ao tick size do ativo (ex: R$0.01) e acumular por bucket ao longo de todos os dias da janela

### Requirement: Seleção automática dos 15 tickers com maior volume

O sistema DEVE selecionar os 15 tickers com maior volume financeiro (NtlFinVol) agregado no período como padrão quando nenhum arquivo de tickers é fornecido.

#### Scenario: Mais de 15 tickers disponíveis

- **WHEN** o período contém dados de 50 tickers
- **THEN** o sistema DEVE selecionar os 15 com maior NtlFinVol somado e apresentá-los como padrão

#### Scenario: Menos de 15 tickers disponíveis

- **WHEN** o período contém dados de apenas 7 tickers
- **THEN** o sistema DEVE selecionar todos os 7 tickers disponíveis

### Requirement: Cálculo do VWAP Distance como indicador derivado

O sistema DEVE calcular o VWAP Distance para cada ticker em cada dia como `(LastPric - TradAvrgPric) / TradAvrgPric`. O indicador depende do `vwap` existente, utilizando o `daily_vwap` de cada data como denominador.

#### Scenario: VWAP Distance positivo

- **WHEN** LastPric = 52.50 e TradAvrgPric = 50.00
- **THEN** VWAP Distance DEVE ser (52.50 - 50.00) / 50.00 = 0.05

#### Scenario: VWAP Distance negativo

- **WHEN** LastPric = 48.00 e TradAvrgPric = 50.00
- **THEN** VWAP Distance DEVE ser (48.00 - 50.00) / 50.00 = -0.04

### Requirement: Tratamento de dados ausentes ou inválidos

O sistema DEVE ignorar linhas do CSV onde campos essenciais (TckrSymb, NtlFinVol, TradAvrgPric) estão vazios ou inválidos, sem interromper o processamento.

#### Scenario: Linha com volume vazio

- **WHEN** uma linha do CSV tem o campo NtlFinVol vazio
- **THEN** essa linha DEVE ser ignorada e o processamento DEVE continuar com as demais linhas
