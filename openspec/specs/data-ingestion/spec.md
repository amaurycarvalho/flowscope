## ADDED Requirements

### Requirement: Download de arquivos consolidados via API B3 two-step
O sistema DEVE baixar arquivos TradeInformationConsolidated da B3 usando o fluxo two-step: (1) GET para `api/download/requestname?fileName=...&date=...` obtendo token, (2) GET para `api/download/?token=` para download efetivo do CSV.

#### Scenario: Download bem-sucedido de um arquivo
- **WHEN** o sistema solicita o arquivo da data `2026-06-25` com nome `TradeInformationConsolidated`
- **THEN** o CSV correspondente DEVE ser baixado e salvo no diretório de cache local

#### Scenario: Data sem arquivo disponível
- **WHEN** a API B3 retorna erro para uma data solicitada (ex: feriado, fim de semana)
- **THEN** o sistema DEVE registrar o erro e continuar com as demais datas da janela, não interrompendo o processamento

### Requirement: Janela temporal com offsets de Fibonacci
O sistema DEVE calcular as datas de download usando offsets de Fibonacci a partir da data de referência: d-1, d-2, d-3, d-5, d-8, d-13, d-21.

#### Scenario: Cálculo da janela a partir de uma data de referência
- **WHEN** a data de referência é `2026-06-26` (sexta-feira)
- **THEN** as datas calculadas DEVEM ser: 2026-06-25, 2026-06-24, 2026-06-23, 2026-06-22, 2026-06-18, 2026-06-15, 2026-06-05 (considerando apenas dias úteis)

#### Scenario: Data calculada cai em fim de semana
- **WHEN** um offset produz uma data que é sábado ou domingo
- **THEN** o sistema DEVE avançar para a próxima data até encontrar um dia útil (segunda a sexta), sem recalcular os demais offsets

### Requirement: Cache local de CSVs
O sistema DEVE manter cache local dos arquivos CSV baixados no diretório apropriado da plataforma: `~/.cache/flowscope/` (Linux), `%LOCALAPPDATA%/flowscope/cache/` (Windows), `~/Library/Caches/flowscope/` (macOS). Os arquivos DEVEM ser nomeados como `YYYY-MM-DD.csv`.

#### Scenario: Cache hit — arquivo já existe
- **WHEN** o sistema precisa do CSV da data `2026-06-25` e ele já existe no cache
- **THEN** o sistema DEVE usar o arquivo cacheado sem fazer nova requisição HTTP

#### Scenario: Cache miss — data de referência mudou
- **WHEN** a data de referência é alterada e arquivos de novas datas são necessários
- **THEN** o sistema DEVE baixar apenas os arquivos faltantes, mantendo os já existentes no cache

### Requirement: Parsing de CSV TradeInformationConsolidated
O sistema DEVE fazer parsing dos arquivos CSV da B3 utilizando o delimitador `;`, extraindo as colunas: RptDt, TckrSymb, SgmtNm, MinPric, MaxPric, TradAvrgPric, LastPric, TradQty, NtlFinVol, FinInstrmQty.

#### Scenario: Parsing de arquivo CSV válido
- **WHEN** um CSV consolidado é lido
- **THEN** cada linha DEVE produzir uma entidade de domínio com os campos mapeados para tipos Python apropriados (data como `date`, preços como `Decimal` ou `float`, volumes como `int`)

#### Scenario: CSV com linha de cabeçalho inválida ou ausente
- **WHEN** o parser encontra um CSV sem o cabeçalho esperado ou com formato inválido
- **THEN** o sistema DEVE lançar uma exceção específica de parsing com mensagem descritiva em português

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
