## ADDED Requirements

### Requirement: Resolução de Ticker para idFNET
O sistema DEVE, a partir de um ticker (ex: `ALZR11`), tentar obter o identificador interno `idFNET` na B3, utilizando o endpoint `GetListClassFund` com token Base64. Para tickers que não são fundos listados, a resolução DEVE retornar `None` sem lançar exceção.

#### Scenario: Resolução bem-sucedida de ticker de fundo
- **WHEN** o sistema resolve o ticker `ALZR11`
- **THEN** o sistema DEVE extrair a raiz removendo o sufixo `11`, construir o token Base64 com `{"linguagem": "pt-br", "idCEM": "ALZR", "typeFund": "FII"}`, e retornar o `id` do objeto da resposta onde `tradingName` NÃO contém `"Fundo:"`

#### Scenario: Ticker de ação — resolução retorna None
- **WHEN** o sistema tenta resolver `PETR4` (ação, não fundo)
- **THEN** o sistema DEVE retornar `None` sem lançar exceção, permitindo que o pipeline continue sem dados desta fonte

#### Scenario: Ticker não encontrado na B3
- **WHEN** o ticker informado não retorna resultados ou retorna apenas objetos com `tradingName` contendo `"Fundo:"`
- **THEN** o sistema DEVE retornar `None`

### Requirement: Cache de resolução de ticker
O sistema DEVE cachear o resultado da resolução ticker → idFNET utilizando `CacheManager.get_or_fetch` com TTL de 30 dias, chave no formato `fund_resolution_{ticker}`. `None` também DEVE ser cacheado para evitar requisições repetidas a tickers não-fundos.

#### Scenario: Cache hit para ticker já resolvido
- **WHEN** o ticker `ALZR11` foi resolvido há menos de 30 dias
- **THEN** o sistema DEVE retornar o idFNET do cache sem realizar requisição HTTP

#### Scenario: Cache hit para ticker não-fundo
- **WHEN** `PETR4` foi consultado há menos de 30 dias e retornou `None`
- **THEN** o sistema DEVE retornar `None` do cache sem realizar nova requisição HTTP

### Requirement: Construção de token Base64 para API B3 Fundos
O sistema DEVE construir tokens Base64 para os endpoints da API `fundsListedProxy` serializando objetos JSON com `separators=(",",":")` e codificando em Base64, seguindo o mesmo padrão usado no `B3Client` para portfolios.

#### Scenario: Token para GetListClassFund
- **WHEN** o payload é `{"linguagem":"pt-br","idCEM":"ALZR","typeFund":"FII"}`
- **THEN** o token gerado DEVE ser `eyJsYW5ndWFnZSI6InB0LWJyIiwiaWRDRU0iOiJBTFpSIiwidHlwZUZ1bmQiOiJGSUkifQ==`

#### Scenario: Token para GetStructuredReports
- **WHEN** o payload inclui `dataInicial`, `dataFinal`, `pageNumber`, `pageSize`, `idFNET`, `typeFund` e `type`
- **THEN** o token gerado DEVE codificar corretamente todos os campos, inclusive valores numéricos como inteiros sem aspas
