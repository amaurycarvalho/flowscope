## Purpose

Calcular, por ticker, as métricas de dividendo exibidas na tabela fundamentalista: a última data-com, o último dividendo pago e a tendência do dividendo em relação ao pagamento anterior.

## ADDED Requirements

### Requirement: Última data-com
O sistema DEVE determinar, para um ticker, a data-com (`data_base`) do provento de tipo `Rendimento` mais recente disponível até a data de referência.

#### Scenario: Data-com do provento mais recente
- **WHEN** o ticker possui proventos de tipo `Rendimento`
- **THEN** a última data-com DEVE ser a `data_base` do provento mais recente

#### Scenario: Sem proventos
- **WHEN** o ticker não possui proventos de tipo `Rendimento`
- **THEN** a última data-com DEVE ser `N/A`

### Requirement: Último dividendo
O sistema DEVE determinar, para um ticker, o valor do último dividendo (provento de tipo `Rendimento`) pago, excluindo proventos de tipo `Amortização`.

#### Scenario: Último dividendo de rendimento
- **WHEN** o ticker possui proventos de tipo `Rendimento` e `Amortização`
- **THEN** o último dividendo DEVE ser o valor do provento de tipo `Rendimento` mais recente, ignorando `Amortização`

#### Scenario: Apenas amortização
- **WHEN** o ticker possui somente proventos de tipo `Amortização`
- **THEN** o último dividendo DEVE ser `N/A`

### Requirement: Tendência do dividendo
O sistema DEVE classificar a tendência do dividendo comparando o último dividendo (Rendimento) com o dividendo imediatamente anterior, usando uma banda de tolerância configurável (padrão ±5%). A classificação DEVE ser `SUBINDO` quando `último ≥ anterior × 1,05`, `CAINDO` quando `último ≤ anterior × 0,95`, e `MANTEVE` nos demais casos.

#### Scenario: Dividendo subiu
- **WHEN** o último dividendo é maior ou igual a 1,05 vezes o anterior
- **THEN** a tendência DEVE ser `SUBINDO`

#### Scenario: Dividendo caiu
- **WHEN** o último dividendo é menor ou igual a 0,95 vezes o anterior
- **THEN** a tendência DEVE ser `CAINDO`

#### Scenario: Dividendo manteve
- **WHEN** o último dividendo está dentro da banda de ±5% em relação ao anterior
- **THEN** a tendência DEVE ser `MANTEVE`

#### Scenario: Sem dividendo anterior
- **WHEN** o ticker possui apenas um dividendo (ou nenhum)
- **THEN** a tendência DEVE ser `N/A`

### Requirement: Banda de tendência configurável
A banda de tolerância da tendência do dividendo DEVE ser configurável e versionada, sem alteração silenciosa do comportamento.

#### Scenario: Banda configurada
- **WHEN** a configuração define a banda de tendência como 0,05
- **THEN** a classificação DEVE usar 0,05 como limiar de `SUBINDO`/`CAINDO`
