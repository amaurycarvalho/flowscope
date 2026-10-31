## Purpose

Define the command-line interface for FlowScope, including argument parsing, data export (VWAP CSV), ticker filtering, and desktop shortcut creation.

## Requirements

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

### Requirement: Exportação CSV de VWAP via `exportar vwap`

O sistema DEVE exportar os valores de VWAP dos tickers selecionados em formato CSV quando o subcomando `flowscope exportar vwap` é utilizado. O CSV DEVE incluir colunas para cada data da janela Fibonacci, com os VWAPs diários de cada ticker. Quando a opção `--tickers <ARQUIVO>` é fornecida, o sistema DEVE filtrar a exportação para conter apenas os tickers listados no arquivo. O sistema DEVE gravar o arquivo `vwap_<AAAA-MM-DD>.csv` por padrão; quando `--saida <ARQUIVO>` é fornecida, o sistema DEVE gravar no caminho indicado.

#### Scenario: Exportação VWAP com colunas diárias

- **WHEN** o usuário executa `flowscope exportar vwap`
- **THEN** o CSV gerado DEVE conter colunas: Ticker, VWAP_Periodo, e uma coluna por data da janela Fibonacci (ex: 2026-06-25, 2026-06-24, ...) com o VWAP diário de cada ticker

#### Scenario: Exportação VWAP com tickers específicos

- **WHEN** o usuário executa `flowscope exportar vwap --tickers meus_tickers.txt`
- **THEN** o CSV gerado DEVE conter apenas os tickers listados no arquivo, e apenas as datas com dados disponíveis para esses tickers

#### Scenario: Nome de arquivo customizado

- **WHEN** o usuário executa `flowscope exportar vwap --saida relatorio.csv`
- **THEN** o sistema DEVE gravar o CSV em `relatorio.csv` em vez do nome padrão com data

### Requirement: Subcomandos de consulta via `consultar`

O sistema DEVE expor as consultas a dados remotos da B3 sob o subcomando `flowscope consultar`:

- `flowscope consultar proventos <TICKER> --data-inicio <AAAA-MM-DD> --data-fim <AAAA-MM-DD> [--saida <ARQUIVO>]`: extrai rendimentos e amortizações estruturados.
- `flowscope consultar fatos <TICKER> [--categoria <CODIGO>] [--data-inicio <AAAA-MM-DD>] [--data-fim <AAAA-MM-DD>] [--saida <ARQUIVO>]`: extrai fatos relevantes, assembleias e avisos do ticker via `GetMaterialFacts`; `--categoria` filtra a categoria de documento (1=Assembleias, 3=Aviso Acionistas, 4=Fatos Relevantes, 48=Aviso Debenturistas, 107=Relatório Proventos).
- `flowscope consultar noticias [--palavra <TERMO>] [--data-inicio <AAAA-MM-DD>] [--data-fim <AAAA-MM-DD>] [--saida <ARQUIVO>]`: lista notícias do Plantão B3; `--palavra` filtra por palavra-chave no título.
- `flowscope consultar regulacao [--saida <ARQUIVO>]`: extrai Censuras Públicas e Condições Excepcionais da B3.

Sem `--saida`, o resultado DEVE ser impresso como JSON em `stdout`. Os parâmetros contextuais DEVEM existir apenas nos subcomandos a que se aplicam.

#### Scenario: Extração de fatos relevantes de um ticker

- **WHEN** o usuário executa `flowscope consultar fatos PETR4 --data-inicio 2026-01-01 --data-fim 2026-06-30`
- **THEN** o sistema DEVE resolver o codeCVM de PETR4, consultar `GetMaterialFacts` para todas as categorias e exibir os resultados em JSON no `stdout`

#### Scenario: Extração de fatos relevantes com categoria específica

- **WHEN** o usuário executa `flowscope consultar fatos PETR4 --categoria 4`
- **THEN** o sistema DEVE consultar apenas a categoria Fatos Relevantes (4)

#### Scenario: Listagem de notícias com filtro de data

- **WHEN** o usuário executa `flowscope consultar noticias --data-inicio 2026-07-01 --data-fim 2026-07-29`
- **THEN** o sistema DEVE listar notícias do Plantão B3 no período e exibir em JSON no `stdout`

#### Scenario: Listagem de notícias com palavra-chave

- **WHEN** o usuário executa `flowscope consultar noticias --palavra PETROBRAS --data-inicio 2026-01-01 --data-fim 2026-12-31`
- **THEN** o sistema DEVE filtrar notícias que contenham "PETROBRAS" no título

#### Scenario: Extração de dados regulatórios da B3

- **WHEN** o usuário executa `flowscope consultar regulacao`
- **THEN** o sistema DEVE extrair Censuras Públicas e Condições Excepcionais e exibir em JSON no `stdout`

#### Scenario: Consulta com saída em arquivo

- **WHEN** o usuário executa `flowscope consultar regulacao --saida regulacao.json`
- **THEN** o sistema DEVE gravar o JSON em `regulacao.json`

#### Scenario: Reutilização de argumentos de data existentes

- **WHEN** `--data-inicio` e `--data-fim` são usados com `flowscope consultar fatos` ou `flowscope consultar noticias`
- **THEN** os argumentos DEVEM filtrar o período de consulta, assim como o comportamento já definido para `flowscope consultar proventos`

### Requirement: Subcomandos de navegação via CLI

O sistema DEVE aceitar o subcomando `flowscope nav <operacao> ...` para executar as operações de navegação diretamente pelo terminal, reusando o mesmo núcleo de navegação do chat e do servidor MCP. As operações DEVEM incluir `listar`, `obter`, `contar`, `existe`, `buscar`, `buscar-semantico` e `manifesto`. A saída padrão DEVE ser JSON estruturado em `stdout`; a flag opcional `--pretty` DEVE formatar a saída para leitura humana. `flowscope nav obter <caminho>` DEVE aceitar `--offset` e `--limite`, `flowscope nav buscar <caminho>` DEVE aceitar `--regex`, `--em` e `--max`, e `flowscope nav buscar-semantico <caminho>` DEVE aceitar `--consulta` e `--max`. As operações de listagem DEVEM aceitar `--cursor` para continuar a paginação. Erros de navegação DEVEM ser impressos como JSON estruturado em `stdout`; mensagens de diagnóstico DEVEM ir para `stderr`.

#### Scenario: Listagem por CLI

- **WHEN** o usuário executa `flowscope nav listar /noticias/grupos`
- **THEN** o sistema DEVE imprimir o JSON com os filhos imediatos e, quando houver continuação, o `nextCursor`

#### Scenario: Continuação por cursor

- **WHEN** o usuário executa `flowscope nav listar <caminho> --cursor <token>`
- **THEN** o sistema DEVE imprimir a página seguinte do resultado

#### Scenario: Leitura de conteúdo pesado

- **WHEN** o usuário executa `flowscope nav obter /documentos/PETR4/<chave>/texto --offset 0 --limite 12000`
- **THEN** o sistema DEVE imprimir o trecho correspondente com total, offset, limite e indicador de continuação

#### Scenario: Busca determinística por CLI

- **WHEN** o usuário executa `flowscope nav buscar /documentos/PETR4 --regex "..." --em titulo,texto --max 50`
- **THEN** o sistema DEVE imprimir os nós que casam, respeitando o limite de resultados

#### Scenario: Saída legível opcional

- **WHEN** o usuário adiciona `--pretty` a um subcomando `nav`
- **THEN** o sistema DEVE formatar o JSON para leitura humana

#### Scenario: Erro de navegação na CLI

- **WHEN** uma operação `nav` falha de forma recuperável
- **THEN** o sistema DEVE imprimir o erro estruturado com motivo, detalhe e dica, e o diagnóstico DEVE ir para `stderr`

### Requirement: Leitura da data de referência via CLI

O sistema DEVE aceitar o subcomando `flowscope nav data-referencia` para imprimir, como JSON estruturado em `stdout`, a data de referência resolvida da última carga de fundamentos. O subcomando NÃO DEVE exigir caminho nem argumentos e DEVE reusar o mesmo núcleo de navegação das demais operações `nav`.

#### Scenario: Leitura da data de referência

- **WHEN** o usuário executa `flowscope nav data-referencia`
- **THEN** a data de referência resolvida DEVE ser impressa como JSON em `stdout`

#### Scenario: Sem data disponível

- **WHEN** não há marcador de última carga nem `last_date` no `config.json`
- **THEN** o comando DEVE indicar a ausência de data em JSON, sem erro fatal

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
