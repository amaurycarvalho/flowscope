## ADDED Requirements

### Requirement: Cache do HTML do documento FundosNet

O sistema DEVE persistir o HTML bruto de cada documento do FundosNet obtido por `buscar_html_documento`, indexado pelo identificador do documento, de modo que solicitações subsequentes do mesmo documento sejam servidas do cache sem nova requisição HTTP. O cache DEVE ser compartilhado entre os documentos de proventos (`type=41`) e os do informe mensal (`type=40`), que usam o mesmo endpoint. Quando o download falhar e existir HTML armazenado, o sistema DEVE servir o conteúdo em cache; sem conteúdo armazenado, DEVE sinalizar a indisponibilidade.

#### Scenario: Documento servido do cache
- **WHEN** o HTML de um documento já foi baixado e é solicitado novamente dentro do período de retenção
- **THEN** o sistema DEVE devolver o HTML armazenado sem realizar nova requisição HTTP

#### Scenario: Documento novo é armazenado
- **WHEN** um documento ainda não está em cache
- **THEN** o sistema DEVE baixar o HTML e armazená-lo indexado pelo identificador do documento

#### Scenario: Proventos e informe mensal compartilham o cache
- **WHEN** o mesmo identificador de documento é lido pela extração de proventos e pela extração do informe mensal
- **THEN** o HTML DEVE ser baixado uma única vez e reutilizado pelas duas leituras

#### Scenario: Falha de rede com cache disponível
- **WHEN** o download do documento falha por indisponibilidade e existe HTML armazenado para o identificador
- **THEN** o sistema DEVE servir o conteúdo em cache

#### Scenario: Falha de rede sem cache
- **WHEN** o download do documento falha e não existe HTML armazenado para o identificador
- **THEN** o sistema DEVE sinalizar a indisponibilidade, sem retornar conteúdo vazio como se fosse válido

### Requirement: Cache da identidade do fundo

O sistema DEVE persistir a resposta de `GetListClassFund` usada na resolução de identidade, indexada pelo `id` primário do fundo, de modo que `find_by_ticker` não consulte a B3 novamente dentro do período de validade. A ausência de correspondência NÃO DEVE ser armazenada, para não congelar falhas transitórias.

#### Scenario: Identidade servida do cache
- **WHEN** a identidade de um fundo já foi resolvida e é solicitada novamente dentro do período de validade
- **THEN** o sistema DEVE devolver os registros de classe armazenados sem nova requisição HTTP

#### Scenario: Validade vencida reconsulta a fonte
- **WHEN** o período de validade da identidade armazenada vence
- **THEN** o sistema DEVE consultar a B3 novamente e substituir o cache

#### Scenario: Ticker sem correspondência não é cacheado
- **WHEN** a resolução de um ticker não encontra correspondência na B3
- **THEN** o resultado vazio NÃO DEVE ser armazenado, permitindo nova tentativa em execução futura

### Requirement: Chaves de cache versionadas e políticas centralizadas

O sistema DEVE versionar as chaves de cache de documentos e de identidade com a versão do parser/aquisição da B3 e DEVE centralizar os prazos de validade e os nomes de chave em constantes do cliente, para que uma mudança de parser invalide os registros anteriores e as políticas de cache evoluam em um único ponto.

#### Scenario: Mudança de versão do parser invalida registros
- **WHEN** a versão do parser/aquisição difere da versão registrada no cache
- **THEN** os registros de documento e de identidade anteriores DEVEM ser tratados como ausentes e a fonte DEVE ser consultada novamente

#### Scenario: Política de cache em um único ponto
- **WHEN** um prazo de validade ou nome de chave da aquisição B3 precisa mudar
- **THEN** a alteração DEVE ocorrer nas constantes do cliente, sem duplicar valores literais nos métodos de aquisição
