# Spec Delta

## MODIFIED Requirements

### Requirement: Subcomandos de leitura `exportar` e `consultar`

O sistema DEVE organizar as operações de leitura da CLI em dois subcomandos de verbo. O subcomando `exportar` DEVE agrupar as operações que materializam dados calculados localmente em arquivo. O subcomando `consultar` DEVE agrupar as consultas a dados remotos da B3 e ao calendário local de feriados que imprimem JSON estruturado. A seleção do subcomando DEVE ser exaustiva, sem resolução por precedência entre flags conflitantes. Cada subcomando DEVE aceitar apenas os parâmetros aplicáveis às suas operações. A opção `--saida <ARQUIVO>` DEVE estar disponível nos subcomandos de leitura; quando omitida, a saída DEVE ir para `stdout`, exceto em `exportar vwap`, que DEVE gravar por padrão o arquivo `vwap_<AAAA-MM-DD>.csv`.

#### Scenario: Estrutura dos verbos de leitura
- **WHEN** o usuário executa `flowscope exportar --help` ou `flowscope consultar --help`
- **THEN** o sistema DEVE listar apenas os subcomandos e os parâmetros aplicáveis àquele verbo

#### Scenario: Saída direcionada para arquivo
- **WHEN** o usuário adiciona `--saida arquivo.json` a um subcomando de `consultar`
- **THEN** o sistema DEVE gravar o JSON em `arquivo.json` em vez de imprimi-lo em `stdout`

#### Scenario: Parâmetro fora de escopo é rejeitado
- **WHEN** o usuário informa um parâmetro que não pertence ao subcomando, como `--categoria` em `flowscope consultar noticias`
- **THEN** o sistema DEVE rejeitar a invocação com erro de argumentos, sem executar consulta

#### Scenario: Consulta local de feriados
- **WHEN** o usuário executa `flowscope consultar feriados --ano 2026`
- **THEN** o sistema lê o calendário do cache local
- **THEN** imprime o JSON estruturado em `stdout` sem iniciar requisição de rede

## ADDED Requirements

### Requirement: Consulta de feriados via `consultar feriados`

O sistema DEVE aceitar `flowscope consultar feriados --ano <AAAA> [--saida <ARQUIVO>]`. O comando DEVE ler somente o cache do calendário e devolver, em JSON, o ano, a origem, o instante de extração, o estado do calendário e a lista de feriados com data ISO, dia da semana, nome e origem. Sem cache para o ano, DEVE devolver conteúdo estruturado com estado `calendario_indisponivel`, sem erro fatal e sem consultar a rede.

#### Scenario: Listagem de um ano
- **WHEN** o usuário executa `flowscope consultar feriados --ano 2026` e o ano está no cache
- **THEN** o JSON contém os feriados de 2026 com data, dia da semana, nome e origem
- **THEN** nenhuma requisição de rede é iniciada

#### Scenario: Ano sem cache
- **WHEN** o usuário consulta um ano sem cache
- **THEN** o comando devolve `calendario_indisponivel` em JSON
- **THEN** o processo não falha nem consulta a ANBIMA

#### Scenario: Saída em arquivo
- **WHEN** o usuário adiciona `--saida feriados.json`
- **THEN** o JSON é gravado no caminho indicado

### Requirement: Exportação de feriados via `exportar feriados`

O sistema DEVE aceitar `flowscope exportar feriados --ano <AAAA> --formato <csv|json> [--saida <ARQUIVO>]`. O comando DEVE ler somente o cache do calendário. O CSV DEVE usar `;` como separador, datas ISO e colunas de data, dia da semana, nome e origem. O JSON DEVE conter os metadados do ano e a lista de feriados. Sem `--saida`, o conteúdo DEVE ser impresso em `stdout`, sem gravar arquivo.

#### Scenario: Exportação CSV
- **WHEN** o usuário executa `flowscope exportar feriados --ano 2026 --formato csv`
- **THEN** o conteúdo CSV é impresso em `stdout`
- **THEN** usa `;`, datas ISO e as colunas de data, dia da semana, nome e origem

#### Scenario: Exportação JSON
- **WHEN** o usuário executa `flowscope exportar feriados --ano 2026 --formato json`
- **THEN** o conteúdo JSON é impresso em `stdout`
- **THEN** nenhum arquivo é gravado sem `--saida`

#### Scenario: Formato inválido
- **WHEN** o usuário informa um formato diferente de `csv` ou `json`
- **THEN** o comando é rejeitado com erro de argumentos
- **THEN** nenhuma leitura ou gravação é executada
