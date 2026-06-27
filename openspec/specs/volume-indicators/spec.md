## ADDED Requirements

### Requirement: Cálculo do Cumulative Volume Delta (CVD)
O sistema DEVE calcular o Cumulative Volume Delta para cada ticker a partir dos dados consolidados de negociação no período da janela Fibonacci.

#### Scenario: Cálculo de CVD para um ticker
- **WHEN** existem dados de múltiplos dias para um ticker
- **THEN** o sistema DEVE produzir um valor de CVD acumulado representando o delta de volume no período

### Requirement: Cálculo do Volume Weighted Average Price (VWAP)
O sistema DEVE calcular o Volume Weighted Average Price para cada ticker usando a fórmula VWAP = Σ(PreçoMédio × VolumeFinanceiro) / Σ(VolumeFinanceiro) por dia, e VWAP do período como média ponderada dos VWAPs diários.

#### Scenario: Cálculo de VWAP para um ticker com múltiplos dias
- **WHEN** um ticker possui dados em 5 dias da janela
- **THEN** o sistema DEVE calcular o VWAP diário para cada dia e o VWAP consolidado do período como média ponderada pelo NtlFinVol

#### Scenario: Ticker com apenas um dia de dados
- **WHEN** um ticker aparece em apenas 1 dia da janela
- **THEN** o VWAP do período DEVE ser igual ao VWAP daquele único dia (TradAvrgPric)

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

### Requirement: Tratamento de dados ausentes ou inválidos
O sistema DEVE ignorar linhas do CSV onde campos essenciais (TckrSymb, NtlFinVol, TradAvrgPric) estão vazios ou inválidos, sem interromper o processamento.

#### Scenario: Linha com volume vazio
- **WHEN** uma linha do CSV tem o campo NtlFinVol vazio
- **THEN** essa linha DEVE ser ignorada e o processamento DEVE continuar com as demais linhas
