# mcp-server Specification

## Purpose

Servidor MCP embutido do FlowScope que expõe as operações de navegação do cache local como tools canônicas para chats e modelos externos, em transporte stdio, sem iniciar serviços de rede.

## Requirements

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

### Requirement: Revisão de protocolo e negociação por requisição

O servidor DEVE implementar a revisão moderna **`2026-07-28`** do MCP, na qual cada requisição declara sua versão e capacidades em `_meta`, sem handshake `initialize`. O servidor DEVE implementar a RPC obrigatória `server/discover`, devolvendo as versões de protocolo suportadas, as capacidades e a identidade do servidor. Quando a versão solicitada não for suportada, o servidor DEVE responder com `UnsupportedProtocolVersionError` listando as versões suportadas. Ao receber um `initialize` legado, o servidor DEVE responder com erro que nomeie as versões suportadas.

#### Scenario: `server/discover` responde

- **WHEN** o cliente envia `server/discover`
- **THEN** o servidor DEVE devolver as versões de protocolo suportadas, as capacidades e a identidade, incluindo `2026-07-28` entre as versões

#### Scenario: Versão não suportada

- **WHEN** o cliente requisita uma versão de protocolo que o servidor não implementa
- **THEN** o servidor DEVE responder com `UnsupportedProtocolVersionError` listando as versões suportadas

#### Scenario: Cliente legado recebe diagnóstico

- **WHEN** o cliente envia um `initialize` legado
- **THEN** o servidor DEVE responder com erro que nomeie `2026-07-28` como versão suportada

### Requirement: Catálogo de tools `nav_*`

O servidor DEVE expor as operações de navegação como tools MCP independentes — `nav_listar`, `nav_obter`, `nav_contar`, `nav_existe`, `nav_buscar`, `nav_buscar_semantico`, `nav_data_referencia` e `nav_manifesto` — descobertas por `tools/list` e invocadas por `tools/call`. `tools/list` DEVE devolver todas as tools em ordem alfabética estável. Cada tool DEVE trazer `title` e as anotações `readOnlyHint`, `destructiveHint`, `idempotentHint` e `openWorldHint`, conforme a tabela:

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

O servidor NÃO DEVE expor tools de reset de navegação nem de execução em lote. As tools do grupo `calendario_*` são definidas em requisito próprio e NÃO DEVEM alterar o conjunto das oito tools `nav_*`.

#### Scenario: Listagem determinística
- **WHEN** o cliente envia `tools/list`
- **THEN** o servidor DEVE devolver as oito tools `nav_*` e as tools `calendario_*` em ordem alfabética, cada uma com `title` e anotações completas

#### Scenario: Tool desconhecida
- **WHEN** o cliente invoca `tools/call` com um nome de tool inexistente
- **THEN** o servidor DEVE devolver erro JSON-RPC de tool não encontrada, sem encerrar

### Requirement: Schemas de entrada das tools

As tools DEVEM declarar schemas de entrada estritos e validados. `nav_listar`, `nav_contar` e `nav_existe` DEVEM exigir `caminho`. `nav_obter` DEVE exigir `caminho` e aceitar `offset` (inteiro, mínimo 0, padrão 0) e `limite` (inteiro, mínimo 1, máximo 12.000, padrão 12.000). `nav_buscar` DEVE exigir `caminho` e `regex` e aceitar `em` (lista de nomes de campos) e `max` (inteiro, mínimo 1, máximo 50, padrão 50). `nav_buscar_semantico` DEVE exigir `caminho` e `consulta` e aceitar `max` (inteiro, mínimo 1, máximo 20, padrão 10). As tools com paginação (`nav_listar`, `nav_buscar`, `nav_buscar_semantico`) DEVEM aceitar um `cursor` opcional (texto). `nav_manifesto` NÃO DEVE exigir argumentos.

#### Scenario: Schema inválido é recusado

- **WHEN** o cliente envia argumentos que violam o schema de uma tool (ex.: `max` acima de 50 ou `caminho` ausente)
- **THEN** o servidor DEVE devolver erro estruturado de validação, sem executar a operação

#### Scenario: Cursor aceito nas tools de listagem

- **WHEN** o cliente envia `cursor` para `nav_listar`, `nav_buscar` ou `nav_buscar_semantico`
- **THEN** o servidor DEVE continuar a paginação a partir do cursor informado

### Requirement: Execução de `tools/call` e envelopes de resultado

`tools/call` DEVE executar a operação no núcleo de navegação e devolver o resultado em JSON estruturado. As tools de listagem DEVEM devolver os itens junto de `nextCursor` quando houver continuação. Erros de domínio recuperáveis DEVEM ser devolvidos como conteúdo estruturado com `motivo`, `detalhe` e `dica`, sem `isError`. Falhas internas não tratadas DEVEM ser devolvidas com `isError`, mantendo o servidor apto a atender novas chamadas.

#### Scenario: Resultado determinístico

- **WHEN** `tools/call` é executado com argumentos válidos
- **THEN** o resultado DEVE ser o mesmo produzido pelo núcleo de navegação para aquela operação

#### Scenario: Erro recuperável não é falha interna

- **WHEN** a operação devolve um erro de domínio recuperável (ex.: `caminho_invalido`)
- **THEN** a resposta DEVE conter o erro estruturado sem `isError`, e o servidor DEVE continuar atendendo

#### Scenario: Falha interna preserva o servidor

- **WHEN** ocorre uma falha interna não tratada durante uma tool
- **THEN** a resposta DEVE marcar `isError` e o servidor DEVE continuar atendendo novas mensagens

### Requirement: Observabilidade e integridade do canal stdio

No modo MCP, o servidor NÃO DEVE escrever nada em `stdout` que não seja uma mensagem JSON-RPC válida. Logs e diagnósticos DEVEM ser escritos em `stderr`. O servidor DEVE suportar notificação de cancelamento.

#### Scenario: stdout limpo

- **WHEN** o servidor registra logs durante o atendimento
- **THEN** os logs DEVEM ir para `stderr` e nenhuma saída não-JSON-RPC DEVE aparecer em `stdout`

#### Scenario: Cancelamento de requisição

- **WHEN** o cliente envia uma notificação de cancelamento para uma requisição em andamento
- **THEN** o servidor DEVE abandonar a requisição sem corromper o canal

### Requirement: Escopo restrito de leitura

Durante o atendimento, o servidor MCP DEVE apenas ler o cache local por meio do núcleo de navegação e do cache do calendário. Ele NÃO DEVE expor, e as tools NÃO DEVEM permitir, consultas à B3/CVM, download, extração, resumo ou escrita de estado. A preparação opcional executada antes de o servidor começar a atender (ver o requisito de preparação na inicialização) não é uma tool e NÃO DEVE ser acessível pelo protocolo.

#### Scenario: Somente leitura
- **WHEN** qualquer tool `nav_*` ou `calendario_*` é invocada
- **THEN** nenhuma escrita de estado, download ou consulta externa DEVE ocorrer

#### Scenario: Preparação não é exposta como tool
- **WHEN** o cliente envia `tools/list`
- **THEN** o catálogo NÃO DEVE conter tool de carregar watchlist nem de atualizar fundamentos

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

### Requirement: Tools `calendario_*`

O servidor DEVE expor `calendario_listar`, `calendario_classificar` e `calendario_exportar` como tools independentes, somente-leitura e restritas ao cache local. As três DEVEM trazer `title` e as anotações `readOnlyHint=true`, `destructiveHint=false`, `idempotentHint=true` e `openWorldHint=false`. Nenhuma delas DEVE consultar a ANBIMA, gravar arquivos ou modificar o cache.

#### Scenario: Listagem de feriados
- **WHEN** o cliente invoca `calendario_listar` com `ano`
- **THEN** o servidor devolve os feriados do ano com data ISO, dia da semana, nome e origem
- **THEN** somente o cache local é lido

#### Scenario: Classificação de data
- **WHEN** o cliente invoca `calendario_classificar` com `data` no formato `AAAA-MM-DD`
- **THEN** o servidor devolve se é dia útil e, quando não for, o motivo e o nome do feriado
- **THEN** nenhuma requisição de rede é iniciada

#### Scenario: Exportação sem gravar arquivo
- **WHEN** o cliente invoca `calendario_exportar` com `ano` e `formato` `csv` ou `json`
- **THEN** o servidor devolve o conteúdo no resultado estruturado
- **THEN** nenhum arquivo é criado, alterado ou removido

#### Scenario: Ano sem cache
- **WHEN** o cliente consulta um ano sem cache
- **THEN** o servidor devolve conteúdo estruturado com estado `calendario_indisponivel`
- **THEN** não consulta a ANBIMA nem falha internamente

#### Scenario: Schemas estritos
- **WHEN** o cliente envia argumentos inválidos, como `ano` não inteiro, `data` fora do formato ISO ou `formato` desconhecido
- **THEN** o servidor devolve erro estruturado de validação
- **THEN** nenhuma leitura é executada

### Requirement: Schemas de entrada das tools `calendario_*`

As tools do grupo `calendario_*` DEVEM declarar schemas de entrada estritos. `calendario_listar` DEVE exigir `ano` (inteiro). `calendario_classificar` DEVE exigir `data` (texto no formato `AAAA-MM-DD`). `calendario_exportar` DEVE exigir `ano` (inteiro) e `formato` (enum `csv` ou `json`). Argumentos ausentes, de tipo incorreto ou fora do enum DEVEM ser recusados com erro estruturado de validação, sem executar a leitura.

#### Scenario: Schema de listagem
- **WHEN** o cliente invoca `calendario_listar` sem `ano` ou com `ano` não inteiro
- **THEN** o servidor recusa a chamada com erro de validação
- **THEN** nenhuma leitura do cache é executada

#### Scenario: Schema de classificação
- **WHEN** o cliente invoca `calendario_classificar` com `data` fora do formato `AAAA-MM-DD`
- **THEN** o servidor recusa a chamada com erro de validação

#### Scenario: Schema de exportação
- **WHEN** o cliente invoca `calendario_exportar` com `formato` diferente de `csv` ou `json`
- **THEN** o servidor recusa a chamada com erro de validação
- **THEN** nenhum conteúdo é exportado
