# Spec Delta — b3-fii-extraction

## ADDED Requirements

### Requirement: Listagem de fundos completa e resiliente a páginas vazias

O sistema DEVE obter a listagem completa de fundos de um tipo usando o maior `pageSize` aceito pela API (120), repetir com backoff páginas vazias retornadas antes de `totalPages` e só considerar a listagem válida quando a quantidade coletada corresponder a `totalRecords`.

#### Scenario: Página vazia intermitente é repetida
- **WHEN** a página 2 retorna `results: []` e `totalPages: 5`, embora `totalPages` anterior indicasse 5 páginas
- **THEN** o sistema DEVE repetir a página 2 após espera e continuar a coleta até a página 5

#### Scenario: Lista completa é cacheada
- **WHEN** a coleta atinge `len(results) == totalRecords`
- **THEN** o sistema DEVE gravar a listagem no cache por tipo de fundo

#### Scenario: Lista parcial não substitui cache completo
- **WHEN** a coleta termina com menos registros que `totalRecords` após esgotar as repetições
- **THEN** o sistema NÃO DEVE gravar a lista parcial no cache e DEVE preservar a última listagem completa válida

#### Scenario: Chave de cache versionada descarta lista parcial antiga
- **WHEN** existir uma listagem gravada por versão anterior da aquisição
- **THEN** o sistema DEVE ignorá-la e recoletar a listagem com a versão atual

### Requirement: Repetição de resposta vazia do GetListClassFund

O sistema DEVE tratar corpo de resposta vazio do `GetListClassFund` como conteúdo inválido transitório, repetindo a requisição conforme a política central de retry, sem interpretá-lo como ausência de fundo.

#### Scenario: Corpo vazio seguido de resposta válida
- **WHEN** a primeira tentativa do `GetListClassFund` retorna HTTP 200 com corpo vazio e a tentativa seguinte retorna os registros de classe
- **THEN** o sistema DEVE usar a resposta válida sem propagar falha

#### Scenario: Corpo vazio persistente após as tentativas
- **WHEN** todas as tentativas do `GetListClassFund` retornam corpo vazio
- **THEN** o sistema DEVE registrar a falha e tratar o resultado como indisponível, sem cachear ausência de identidade

### Requirement: Persistência da identidade do fundo por ticker

O sistema DEVE persistir, a cada resolução bem-sucedida, um registro por ticker contendo `idFNET`, CNPJ do fundo, nome e tipo de fundo, com versão de schema, escrita atômica e tolerância a arquivo ausente, corrompido ou de versão antiga.

#### Scenario: Identidade gravada após resolução
- **WHEN** um ticker é resolvido com sucesso na B3 e possui CNPJ
- **THEN** o sistema DEVE gravar `idFNET`, CNPJ, nome e tipo de fundo no registro persistente do ticker

#### Scenario: Registro corrompido ou de versão antiga é ignorado
- **WHEN** o registro persistente de um ticker não puder ser lido ou estiver em versão de schema anterior
- **THEN** o sistema DEVE tratá-lo como ausente e consultar a B3 novamente

#### Scenario: Resultado negativo não é persistido
- **WHEN** um ticker não é encontrado em uma listagem completa da B3
- **THEN** o sistema NÃO DEVE gravar nem manter um registro negativo de identidade para esse ticker
