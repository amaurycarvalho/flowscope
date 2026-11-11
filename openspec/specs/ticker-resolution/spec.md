## Purpose

Define a resolução de tickers para o identificador interno `idFNET` na API de fundos listados da B3, com cache do resultado (inclusive `None`) e retorno gracioso quando o ticker não é um fundo listado.

## Requirements

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
O sistema DEVE cachear o resultado positivo da resolução ticker → idFNET utilizando `CacheManager.get_or_fetch` com TTL de 30 dias e chave versionada no formato `fund_resolution_{ticker}`. Resultado negativo NÃO DEVE ser cacheado, para não congelar falhas transitórias.

#### Scenario: Cache hit para ticker já resolvido
- **WHEN** o ticker `ALZR11` foi resolvido há menos de 30 dias
- **THEN** o sistema DEVE retornar o idFNET do cache sem realizar requisição HTTP

#### Scenario: Resultado negativo não é cacheado
- **WHEN** um ticker não é encontrado na B3
- **THEN** o sistema DEVE retornar ausência sem gravar a ausência no cache, permitindo nova tentativa em execução futura

#### Scenario: Cache hit para ticker não-fundo
- **WHEN** `PETR4` foi consultado há menos de 30 dias e retornou `None`
- **THEN** o sistema NÃO DEVE reutilizar a ausência do cache e DEVE consultar a B3 novamente

#### Scenario: Versão anterior da chave é ignorada
- **WHEN** existe um registro de resolução gravado por versão anterior da aquisição
- **THEN** o sistema DEVE tratá-lo como ausente e resolver o ticker novamente

### Requirement: Construção de token Base64 para API B3 Fundos
O sistema DEVE construir tokens Base64 para os endpoints da API `fundsListedProxy` serializando objetos JSON com `separators=(",",":")` e codificando em Base64, seguindo o mesmo padrão usado no `B3Client` para portfolios.

#### Scenario: Token para GetListClassFund
- **WHEN** o payload é `{"linguagem":"pt-br","idCEM":"ALZR","typeFund":"FII"}`
- **THEN** o token gerado DEVE ser `eyJsYW5ndWFnZSI6InB0LWJyIiwiaWRDRU0iOiJBTFpSIiwidHlwZUZ1bmQiOiJGSUkifQ==`

#### Scenario: Token para GetStructuredReports
- **WHEN** o payload inclui `dataInicial`, `dataFinal`, `pageNumber`, `pageSize`, `idFNET`, `typeFund` e `type`
- **THEN** o token gerado DEVE codificar corretamente todos os campos, inclusive valores numéricos como inteiros sem aspas

### Requirement: Fallback da identidade persistida quando a B3 está indisponível

O sistema DEVE consultar a identidade persistida ticker → idFNET → CNPJ quando a resolução na B3 falhar ou a listagem de fundos vier incompleta, retornando a identidade armazenada sem lançar exceção.

#### Scenario: B3 indisponível usa identidade persistida
- **WHEN** a consulta à B3 falha por indisponibilidade e existe identidade persistida para o ticker
- **THEN** o sistema DEVE retornar o `idFNET` e o CNPJ armazenados

#### Scenario: Listagem incompleta usa identidade persistida
- **WHEN** a listagem de fundos não pôde ser concluída e existe identidade persistida para o ticker
- **THEN** o sistema DEVE retornar a identidade armazenada em vez de tratar o ticker como ausente

#### Scenario: Sem identidade persistida, indisponibilidade vira ausência tolerada
- **WHEN** a B3 está indisponível e não existe identidade persistida para o ticker
- **THEN** o sistema DEVE retornar ausência sem lançar exceção, mantendo o pipeline sem dados dessa fonte

#### Scenario: Identidade persistida alimenta o CNPJ fiscal
- **WHEN** a identidade é servida do registro persistido com CNPJ
- **THEN** o CNPJ DEVE ficar disponível para a resolução fiscal, permitindo o fallback CVM Anual mesmo com a B3 indisponível

### Requirement: Listagem completa prevalece sobre identidade persistida

O sistema NÃO DEVE usar a identidade persistida quando a listagem completa da B3 for obtida com sucesso e não contiver o ticker, para não mascarar fundos removidos ou tickers inválidos.

#### Scenario: Ticker ausente em listagem completa
- **WHEN** a B3 fornece uma listagem completa e o ticker não está presente, embora exista identidade persistida antiga
- **THEN** o sistema DEVE tratar o ticker como ausente e não usar a identidade antiga
