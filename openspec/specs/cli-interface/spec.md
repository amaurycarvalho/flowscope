## Purpose

Define the command-line interface for FlowScope, including argument parsing, data export (VWAP CSV), ticker filtering, and desktop shortcut creation.

## Requirements

### Requirement: Subcomandos de leitura `exportar` e `consultar`

O sistema DEVE organizar as operações de leitura da CLI em dois subcomandos de verbo. O subcomando `exportar` DEVE agrupar as operações que materializam dados calculados localmente em arquivo. O subcomando `consultar` DEVE agrupar as consultas a dados remotos da B3 que imprimem JSON estruturado. A seleção do subcomando DEVE ser exaustiva, sem resolução por precedência entre flags conflitantes. Cada subcomando DEVE aceitar apenas os parâmetros aplicáveis às suas operações. A opção `--saida <ARQUIVO>` DEVE estar disponível nos subcomandos de leitura; quando omitida, a saída DEVE ir para `stdout`, exceto em `exportar vwap`, que DEVE gravar por padrão o arquivo `vwap_<AAAA-MM-DD>.csv`.

#### Scenario: Estrutura dos verbos de leitura

- **WHEN** o usuário executa `flowscope exportar --help` ou `flowscope consultar --help`
- **THEN** o sistema DEVE listar apenas os subcomandos e os parâmetros aplicáveis àquele verbo

#### Scenario: Saída direcionada para arquivo

- **WHEN** o usuário adiciona `--saida arquivo.json` a um subcomando de `consultar`
- **THEN** o sistema DEVE gravar o JSON em `arquivo.json` em vez de imprimi-lo em `stdout`

#### Scenario: Parâmetro fora de escopo é rejeitado

- **WHEN** o usuário informa um parâmetro que não pertence ao subcomando, como `--categoria` em `flowscope consultar noticias`
- **THEN** o sistema DEVE rejeitar a invocação com erro de argumentos, sem executar consulta

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
