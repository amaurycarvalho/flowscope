## Purpose

Define the command-line interface for FlowScope, including argument parsing, data export (VWAP CSV), ticker filtering, and desktop shortcut creation.

## Requirements

### Requirement: Exportação CSV de VWAP via --vwap
O sistema DEVE exportar os valores de VWAP dos tickers selecionados em formato CSV quando a flag `--vwap` é utilizada. O CSV DEVE incluir colunas para cada data da janela Fibonacci, com os VWAPs diários de cada ticker. Quando a flag `--tickers` é fornecida, o sistema DEVE filtrar a exportação para conter apenas os tickers listados no arquivo.

#### Scenario: Exportação VWAP com colunas diárias
- **WHEN** o usuário executa `flowscope --vwap`
- **THEN** o CSV gerado DEVE conter colunas: Ticker, VWAP_Periodo, e uma coluna por data da janela Fibonacci (ex: 2026-06-25, 2026-06-24, ...) com o VWAP diário de cada ticker

#### Scenario: Exportação VWAP com tickers específicos
- **WHEN** o usuário executa `flowscope --vwap --tickers meus_tickers.txt`
- **THEN** o CSV gerado DEVE conter apenas os tickers listados no arquivo, e apenas as datas com dados disponíveis para esses tickers

### Requirement: Extração de earnings estruturados via CLI
O sistema DEVE aceitar o argumento `--structured-earnings <TICKER>` para disparar a extração de rendimentos e amortizações estruturados. O argumento DEVE exigir obrigatoriamente `--data-inicio <AAAA-MM-DD>` e `--data-fim <AAAA-MM-DD>`. O argumento opcional `--output <ARQUIVO>` DEVE definir o caminho do JSON de saída; quando omitido, o JSON DEVE ser impresso em stdout.

#### Scenario: Extração completa com output em arquivo
- **WHEN** o usuário executa `flowscope --structured-earnings ALZR11 --data-inicio 2026-01-01 --data-fim 2026-07-29 --output proventos.json`
- **THEN** o sistema DEVE extrair os proventos, salvar em `proventos.json` e imprimir mensagem de sucesso

#### Scenario: Extração com ticker sem dados
- **WHEN** o usuário executa `flowscope --structured-earnings PETR4 --data-inicio 2026-01-01 --data-fim 2026-07-29`
- **THEN** o sistema DEVE exibir "Nenhum dado disponível para PETR4" sem erro

### Requirement: Argumentos CLI para dados regulatórios
O sistema DEVE aceitar novos argumentos de linha de comando para extração de dados regulatórios e de mercado:

- `--fatos-relevantes <TICKER>`: Extrai fatos relevantes, assembleias e avisos do ticker especificado via `GetMaterialFacts`
- `--noticias`: Lista notícias do Plantão B3
- `--regulacao`: Extrai Censuras Públicas e Condições Excepcionais da B3
- `--categoria <CODIGO>`: Filtra categoria de documento para `--fatos-relevantes` (1=Assembleias, 3=Aviso Acionistas, 4=Fatos Relevantes, 48=Aviso Debenturistas, 107=Relatório Proventos)
- `--palavra <TERMO>`: Filtra notícias por palavra-chave (usado com `--noticias`)

#### Scenario: Extração de fatos relevantes de um ticker
- **WHEN** o usuário executa `flowscope --fatos-relevantes PETR4 --data-inicio 2026-01-01 --data-fim 2026-06-30`
- **THEN** o sistema DEVE resolver o codeCVM de PETR4, consultar `GetMaterialFacts` para todas as categorias e exibir os resultados em JSON no stdout

#### Scenario: Extração de fatos relevantes com categoria específica
- **WHEN** o usuário executa `flowscope --fatos-relevantes PETR4 --categoria 4`
- **THEN** o sistema DEVE consultar apenas a categoria Fatos Relevantes (4)

#### Scenario: Listagem de notícias com filtro de data
- **WHEN** o usuário executa `flowscope --noticias --data-inicio 2026-07-01 --data-fim 2026-07-29`
- **THEN** o sistema DEVE listar notícias do Plantão B3 no período e exibir em JSON no stdout

#### Scenario: Listagem de notícias com palavra-chave
- **WHEN** o usuário executa `flowscope --noticias --palavra PETROBRAS --data-inicio 2026-01-01 --data-fim 2026-12-31`
- **THEN** o sistema DEVE filtrar notícias que contenham "PETROBRAS" no título

#### Scenario: Extração de dados regulatórios da B3
- **WHEN** o usuário executa `flowscope --regulacao`
- **THEN** o sistema DEVE extrair Censuras Públicas e Condições Excepcionais e exibir em JSON no stdout

#### Scenario: Reutilização de argumentos de data existentes
- **WHEN** `--data-inicio` e `--data-fim` são usados com `--fatos-relevantes` ou `--noticias`
- **THEN** os argumentos DEVEM filtrar o período de consulta, mesmo comportamento já definido para `--structured-earnings`

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


