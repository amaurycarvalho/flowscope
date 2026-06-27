## ADDED Requirements

### Requirement: Download da carteira do IDIV via API B3

O sistema DEVE baixar a composição da carteira do IDIV (Índice Dividendos) da B3 usando o endpoint `GetDownloadPortfolioDay` com token base64 representando `{"index":"IDIV","language":"pt-br"}`. O retorno DEVE ser parseado para extrair a lista de tickers (coluna `Código`), ignorando cabeçalho, rodapé e linhas de totalização.

#### Scenario: Download bem-sucedido da carteira IDIV
- **WHEN** o sistema solicita a carteira IDIV
- **THEN** uma lista de strings com os tickers DEVE ser retornada (ex: `["ABCB4", "ALOS3", ...]`)

#### Scenario: Falha no download da carteira
- **WHEN** o endpoint do IDIV retorna erro ou timeout
- **THEN** o sistema DEVE retornar uma lista vazia sem interromper o fluxo principal

### Requirement: Cache da carteira IDIV com TTL

O sistema DEVE manter um cache local da carteira IDIV com TTL de 7 dias. O cache DEVE armazenar os tickers e o timestamp de quando foi obtido. Ao expirar, o sistema DEVE buscar novamente da API.

#### Scenario: Cache válido (dentro do TTL)
- **WHEN** a carteira IDIV foi baixada há menos de 7 dias
- **THEN** o sistema DEVE retornar os tickers do cache sem fazer nova requisição HTTP

#### Scenario: Cache expirado
- **WHEN** a carteira IDIV foi baixada há mais de 7 dias
- **THEN** o sistema DEVE buscar novamente da API e atualizar o cache

### Requirement: Filtro por segmento CASH no parser

O sistema DEVE filtrar as linhas do CSV TradeInformationConsolidado para manter apenas aquelas onde `SgmtNm == "CASH"`, descartando linhas de outros segmentos (BMF, FUTURE, etc.). Este filtro DEVE ser aplicado durante o parsing.

#### Scenario: Parsing com filtro CASH
- **WHEN** um CSV contém linhas com `SgmtNm` igual a "CASH", "BMF" e "FUTURE"
- **THEN** apenas as linhas com `SgmtNm == "CASH"` DEVEM ser incluídas no resultado
