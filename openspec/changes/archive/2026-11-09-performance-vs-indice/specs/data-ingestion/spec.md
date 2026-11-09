## ADDED Requirements

### Requirement: Série diária de fechamento dos índices via API B3

O sistema DEVE baixar a série diária de fechamento dos índices IBOV, IDIV e IFIX no endpoint B3 `indexStatisticsProxy/IndexCall/GetPortfolioDay`, com token base64 de `{"index":"<INDEX>","language":"pt-br","year":"<YYYY>"}`.

#### Scenario: Download da evolução diária do IBOV
- **WHEN** o sistema solicita a evolução do IBOV para 2026
- **THEN** DEVE receber os fechamentos diários do ano e convertê-los em pares `(data, fechamento)`

#### Scenario: Download da evolução diária do IFIX e do IDIV
- **WHEN** o sistema solicita a evolução do IFIX ou do IDIV para um ano
- **THEN** DEVE receber os fechamentos diários do índice correspondente

#### Scenario: Índice inexistente
- **WHEN** o endpoint retorna resultado vazio para um índice
- **THEN** o sistema DEVE tratar como ausência de série, sem interromper a carga

### Requirement: Cache da série diária por índice e ano

O sistema DEVE manter cache da série diária por `(índice, ano)`. O ano corrente DEVE ter validade de 1 dia; anos anteriores DEVEM ser tratados como imutáveis. Uma mudança de versão de schema DEVE invalidar séries geradas por versões anteriores.

#### Scenario: Ano corrente expira em um dia
- **WHEN** a série do ano corrente foi obtida há menos de 1 dia
- **THEN** o sistema DEVE usar o cache sem nova requisição

#### Scenario: Ano anterior imutável
- **WHEN** a série de um ano anterior já está em cache
- **THEN** o sistema DEVE reutilizá-la sem nova requisição

#### Scenario: Mudança de schema invalida
- **WHEN** a versão do parser ou schema muda
- **THEN** as séries geradas pela versão anterior NÃO DEVEM ser reutilizadas
