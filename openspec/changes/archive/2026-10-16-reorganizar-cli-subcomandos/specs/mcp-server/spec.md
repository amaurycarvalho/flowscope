## MODIFIED Requirements

### Requirement: Servidor MCP iniciado por `flowscope mcp`

O sistema DEVE oferecer um servidor MCP iniciado explicitamente pelo subcomando `flowscope mcp`, usando o transporte **stdio**: o cliente lança o processo, as mensagens JSON-RPC são delimitadas por newline em `stdin`/`stdout` e o servidor DEVE encerrar ao receber EOF. Sem os parâmetros de preparação, o servidor DEVE ler a árvore do cache local padrão do FlowScope e NÃO DEVE exigir parâmetros de raiz ou de compactação de saída. O subcomando DEVE aceitar os parâmetros opcionais `--watchlist <arquivo>` e `--data <AAAA-MM-DD>`, tratados pela preparação na inicialização. O servidor NÃO DEVE expor transporte de rede nesta mudança. O servidor NÃO DEVE ser iniciado por flag de nível raiz; o alias legado `flowscope --mcp` NÃO DEVE mais existir.

#### Scenario: Início e encerramento por stdio

- **WHEN** `flowscope mcp` é iniciado e o `stdin` é fechado
- **THEN** o servidor DEVE processar as mensagens recebidas e encerrar sem erro ao receber EOF

#### Scenario: Alias legado

- **WHEN** `flowscope --mcp` é iniciado
- **THEN** o sistema DEVE rejeitar a invocação com erro de argumento, sem iniciar o servidor

#### Scenario: Sem transporte de rede

- **WHEN** o servidor MCP é iniciado
- **THEN** nenhuma porta de rede DEVE ser aberta
