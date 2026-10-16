## RENAMED Requirements

- FROM: `### Requirement: Servidor MCP iniciado por `flowscope --mcp``
- TO: `### Requirement: Servidor MCP iniciado por `flowscope mcp``

## MODIFIED Requirements

### Requirement: Catálogo de tools `nav_*`

O servidor DEVE expor as operações de navegação como tools MCP independentes — `nav_listar`, `nav_obter`, `nav_contar`, `nav_existe`, `nav_buscar`, `nav_buscar_semantico`, `nav_data_referencia` e `nav_manifesto` — descobertas por `tools/list` e invocadas por `tools/call`. `tools/list` DEVE devolver as tools em ordem alfabética estável. Cada tool DEVE trazer `title` e as anotações `readOnlyHint`, `destructiveHint`, `idempotentHint` e `openWorldHint`, conforme a tabela:

| Tool                   | `readOnlyHint` | `destructiveHint` | `idempotentHint` | `openWorldHint` |
| ---------------------- | -------------- | ----------------- | ---------------- | --------------- |
| `nav_listar`           | true           | false             | true             | false           |
| `nav_obter`            | true           | false             | true             | false           |
| `nav_contar`           | true           | false             | true             | false           |
| `nav_existe`           | true           | false             | true             | false           |
| `nav_buscar`           | true           | false             | true             | false           |
| `nav_buscar_semantico` | true           | false             | true             | false           |
| `nav_data_referencia`  | true           | false             | true             | false           |
| `nav_manifesto`        | true           | false             | true             | false           |

O servidor NÃO DEVE expor tools de reset de navegação nem de execução em lote.

#### Scenario: Listagem determinística

- **WHEN** o cliente envia `tools/list`
- **THEN** o servidor DEVE devolver as oito tools `nav_*` em ordem alfabética, cada uma com `title` e anotações completas

#### Scenario: Tool desconhecida

- **WHEN** o cliente invoca `tools/call` com um nome de tool inexistente
- **THEN** o servidor DEVE devolver erro JSON-RPC de tool não encontrada, sem encerrar

### Requirement: Servidor MCP iniciado por `flowscope mcp`

O sistema DEVE oferecer um servidor MCP iniciado explicitamente pelo subcomando `flowscope mcp`, usando o transporte **stdio**: o cliente lança o processo, as mensagens JSON-RPC são delimitadas por newline em `stdin`/`stdout` e o servidor DEVE encerrar ao receber EOF. O sistema DEVE manter o alias `flowscope --mcp` para compatibilidade. Sem os parâmetros de preparação, o servidor DEVE ler a árvore do cache local padrão do FlowScope e NÃO DEVE exigir parâmetros de raiz ou de compactação de saída. O subcomando DEVE aceitar os parâmetros opcionais `--watchlist <arquivo>` e `--data <AAAA-MM-DD>`, tratados pela preparação na inicialização. O servidor NÃO DEVE expor transporte de rede nesta mudança.

#### Scenario: Início e encerramento por stdio

- **WHEN** `flowscope mcp` é iniciado e o `stdin` é fechado
- **THEN** o servidor DEVE processar as mensagens recebidas e encerrar sem erro ao receber EOF

#### Scenario: Alias legado

- **WHEN** `flowscope --mcp` é iniciado
- **THEN** o servidor DEVE se comportar como `flowscope mcp`

#### Scenario: Sem transporte de rede

- **WHEN** o servidor MCP é iniciado
- **THEN** nenhuma porta de rede DEVE ser aberta

### Requirement: Escopo restrito de leitura

Durante o atendimento, o servidor MCP DEVE apenas ler o cache local por meio do núcleo de navegação. Ele NÃO DEVE expor, e as tools NÃO DEVEM permitir, consultas à B3/CVM, download, extração, resumo ou escrita de estado. A preparação opcional executada antes de o servidor começar a atender (ver o requisito de preparação na inicialização) não é uma tool e NÃO DEVE ser acessível pelo protocolo.

#### Scenario: Somente leitura

- **WHEN** qualquer tool `nav_*` é invocada
- **THEN** nenhuma escrita de estado, download ou consulta externa DEVE ocorrer

#### Scenario: Preparação não é exposta como tool

- **WHEN** o cliente envia `tools/list`
- **THEN** o catálogo NÃO DEVE conter tool de carregar watchlist nem de atualizar fundamentos

## ADDED Requirements

### Requirement: Tool somente-leitura `nav_data_referencia`

O servidor DEVE expor a tool `nav_data_referencia`, sem argumentos de entrada, que devolve a data de referência resolvida da última carga de fundamentos (marcador `last_fundamentals` com fallback para `last_date`). A tool DEVE ser somente-leitura e NÃO DEVE consultar a B3/CVM, baixar, extrair, resumir nem escrever estado.

#### Scenario: Data de referência disponível

- **WHEN** o cliente invoca `nav_data_referencia` e há data de referência registrada
- **THEN** o servidor DEVE devolver a data resolvida como conteúdo estruturado, sem `isError`

#### Scenario: Sem data registrada

- **WHEN** o cliente invoca `nav_data_referencia` e não há marcador nem `last_date`
- **THEN** o servidor DEVE devolver conteúdo estruturado indicando a ausência de data, sem erro fatal

#### Scenario: Confinamento de leitura

- **WHEN** `nav_data_referencia` é invocada
- **THEN** nenhuma chamada de rede, resumo, extração, download ou escrita DEVE ocorrer

### Requirement: Preparação opcional na inicialização do servidor MCP

O subcomando `flowscope mcp` DEVE aceitar os parâmetros opcionais `--watchlist <arquivo>` e `--data <AAAA-MM-DD>`. Quando `--watchlist` for informado, o sistema DEVE executar, antes de iniciar o servidor, a mesma etapa de `flowscope carregar watchlist <arquivo>`. Quando `--data` for informado, o sistema DEVE executar, antes de iniciar o servidor, a mesma etapa de `flowscope atualizar fundamentos --data <AAAA-MM-DD>`, usando a watchlist resultante e, sem `--data`, a data de referência resolvida. A preparação DEVE reusar os mesmos núcleos das ações, DEVE ocorrer sob o lock global de ação — liberado antes de o servidor começar a atender —, DEVE registrar progresso em `stderr` e NÃO DEVE escrever em `stdout`. Uma falha na preparação DEVE abortar a inicialização com código de saída diferente de zero, sem iniciar o servidor. A árvore DEVE ser montada após a preparação, refletindo a data de referência.

#### Scenario: Watchlist preparada na inicialização

- **WHEN** `flowscope mcp --watchlist carteira.txt` é executado
- **THEN** a watchlist do arquivo DEVE ser persistida como em `flowscope carregar watchlist` antes de o servidor iniciar

#### Scenario: Fundamentos preparados na inicialização

- **WHEN** `flowscope mcp --data 2026-10-14` é executado
- **THEN** os fundamentos DEVEM ser atualizados como em `flowscope atualizar fundamentos --data 2026-10-14` antes de o servidor iniciar
- **AND** a árvore DEVE refletir a data de referência resolvida

#### Scenario: Sem parâmetros não há preparação

- **WHEN** `flowscope mcp` é executado sem `--watchlist` e sem `--data`
- **THEN** nenhuma escrita, download ou consulta externa DEVE ocorrer na inicialização

#### Scenario: Falha na preparação aborta a inicialização

- **WHEN** a preparação falha (por exemplo, arquivo de watchlist inexistente)
- **THEN** o processo DEVE encerrar com código diferente de zero, sem iniciar o servidor

#### Scenario: Preparação não polui o `stdout`

- **WHEN** a preparação executa antes de o servidor atender
- **THEN** a saída das etapas de preparação DEVE ir para `stderr` e o `stdout` DEVE conter apenas mensagens JSON-RPC do servidor
