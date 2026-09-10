## ADDED Requirements

### Requirement: Revalidação condicional do snapshot do Fundamentus

O sistema DEVE revalidar o snapshot em cache usando a `Data últ cot` como validador primário e validadores HTTP (`ETag`/`Last-Modified`) como secundários, servindo o cache sem reprocessar quando o snapshot não avançou.

#### Scenario: Data de cotação inalterada

- **WHEN** a `Data últ cot` obtida da fonte não é posterior à armazenada
- **THEN** o sistema DEVE servir o cache e atualizar apenas os metadados de revalidação

#### Scenario: Data de cotação nova

- **WHEN** a `Data últ cot` obtida da fonte é posterior à armazenada
- **THEN** o sistema DEVE substituir o snapshot em cache

#### Scenario: Resposta 304 Not Modified

- **WHEN** o servidor responde `304 Not Modified` a uma requisição condicional
- **THEN** o sistema DEVE servir o cache sem reprocessar o HTML

#### Scenario: Ausência de validadores HTTP

- **WHEN** a fonte não fornece `ETag` nem `Last-Modified`
- **THEN** o sistema DEVE realizar a aquisição completa e comparar a `Data últ cot`

### Requirement: Coalescência de requisições e TTL de segurança

O sistema DEVE limitar a frequência de checagens remotas por ticker e DEVE forçar uma atualização completa após um intervalo máximo de segurança, mesmo quando a data de cotação não muda.

#### Scenario: Chamadas repetidas dentro do intervalo

- **WHEN** o mesmo ticker é consultado novamente antes de vencer o intervalo mínimo de revalidação
- **THEN** o sistema DEVE servir o cache sem nova requisição

#### Scenario: TTL de segurança vencido

- **WHEN** o tempo desde a última atualização excede o intervalo máximo de segurança
- **THEN** o sistema DEVE refazer a aquisição completa mesmo com a data inalterada

### Requirement: Cache versionado por parser

O sistema DEVE vincular o cache do Fundamentus à versão do parser, de modo que uma mudança de versão invalide os snapshots anteriores.

#### Scenario: Versão do parser alterada

- **WHEN** a versão do parser difere da versão registrada no cache
- **THEN** o snapshot anterior DEVE ser ignorado e a fonte consultada novamente

### Requirement: Invalidação explícita por ticker

O sistema DEVE permitir forçar a atualização de um ticker, ignorando o cache.

#### Scenario: Atualização forçada

- **WHEN** a atualização é solicitada com `force_refresh`
- **THEN** o sistema DEVE consultar a fonte e substituir o cache, independentemente da validade do snapshot armazenado

### Requirement: Resultado do cache reportado ao consumidor

O sistema DEVE reportar, para cada consulta, se o snapshot foi servido do cache, revalidado ou atualizado, permitindo que a apresentação informe a atualização de dados.

#### Scenario: Atualização de dados sinalizada

- **WHEN** o snapshot de um ticker é atualizado a partir da fonte
- **THEN** o resultado DEVE indicar atualização para que a interface possa exibir "Dados atualizados"
