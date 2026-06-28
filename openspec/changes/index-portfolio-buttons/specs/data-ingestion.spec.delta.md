## Purpose

Delta spec for `data-ingestion`: generalizar download de carteira de IDIV-only para qualquer índice B3.

## Modified Requirements

### Requirement: Download da carteira de qualquer índice via API B3 (substitui "Download da carteira do IDIV via API B3")

O sistema DEVE baixar a composição da carteira teórica de **qualquer índice da B3** usando o endpoint `GetDownloadPortfolioDay` com token base64 construído a partir de `{"index":"<INDEX>","language":"pt-br"}`. O retorno DEVE ser parseado para extrair a lista de tickers (coluna `Código`), ignorando cabeçalho, rodapé e linhas de totalização, independentemente do nome do índice.

#### Scenario: Download bem-sucedido de IBOV
- **WHEN** o sistema solicita a carteira IBOV
- **THEN** uma lista de strings com os tickers DEVE ser retornada (ex: `["VALE3", "PETR4", "ITUB4", ...]`)

#### Scenario: Download bem-sucedido de IFIX
- **WHEN** o sistema solicita a carteira IFIX
- **THEN** uma lista de strings com os tickers DEVE ser retornada (ex: `["KINP11", "HGLG11", "KNRI11", ...]`)

#### Scenario: Falha no download de índice inexistente
- **WHEN** o sistema solicita um índice que não existe na B3
- **THEN** o sistema DEVE retornar uma lista vazia sem interromper o fluxo principal

### Requirement: Cache da carteira por índice com TTL (substitui "Cache da carteira IDIV com TTL")

O sistema DEVE manter um cache local independente para **cada índice** (IBOV, IDIV, IFIX, etc.) com TTL de 7 dias. A chave de cache DEVE ser `portfolio_{index}`. Cada índice DEVE ter seu próprio timestamp de expiração.

#### Scenario: Cache válido para IBOV
- **WHEN** a carteira IBOV foi baixada há menos de 7 dias
- **THEN** o sistema DEVE retornar os tickers do cache sem fazer nova requisição HTTP

#### Scenario: Cache expirado para IFIX (mas IDIV ainda válido)
- **WHEN** a carteira IFIX foi baixada há mais de 7 dias, mas IDIV foi baixada há 2 dias
- **THEN** o sistema DEVE buscar IFIX novamente da API e usar o cache para IDIV
