## MODIFIED Requirements

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
