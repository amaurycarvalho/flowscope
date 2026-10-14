# mcp-server Specification

## Purpose

Servidor MCP embutido do FlowScope que expõe as operações de navegação do cache local como tools canônicas para chats e modelos externos, em transporte stdio, sem iniciar serviços de rede.

## Requirements

### Requirement: Servidor MCP iniciado por `flowscope --mcp`

O sistema DEVE oferecer um servidor MCP iniciado explicitamente por `flowscope --mcp`, usando o transporte **stdio**: o cliente lança o processo, as mensagens JSON-RPC são delimitadas por newline em `stdin`/`stdout` e o servidor DEVE encerrar ao receber EOF. O servidor NÃO DEVE expor transporte de rede nesta mudança. O servidor NÃO DEVE exigir nem aceitar parâmetros de raiz ou de compactação de saída: a árvore é sempre lida do cache local padrão do FlowScope.

#### Scenario: Início e encerramento por stdio

- **WHEN** `flowscope --mcp` é iniciado e o `stdin` é fechado
- **THEN** o servidor DEVE processar as mensagens recebidas e encerrar sem erro ao receber EOF

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

O servidor DEVE expor as operações de navegação como tools MCP independentes — `nav_listar`, `nav_obter`, `nav_contar`, `nav_existe`, `nav_buscar`, `nav_buscar_semantico` e `nav_manifesto` — descobertas por `tools/list` e invocadas por `tools/call`. `tools/list` DEVE devolver as tools em ordem alfabética estável. Cada tool DEVE trazer `title` e as anotações `readOnlyHint`, `destructiveHint`, `idempotentHint` e `openWorldHint`, conforme a tabela:

| Tool                   | `readOnlyHint` | `destructiveHint` | `idempotentHint` | `openWorldHint` |
| ---------------------- | -------------- | ----------------- | ---------------- | --------------- |
| `nav_listar`           | true           | false             | true             | false           |
| `nav_obter`            | true           | false             | true             | false           |
| `nav_contar`           | true           | false             | true             | false           |
| `nav_existe`           | true           | false             | true             | false           |
| `nav_buscar`           | true           | false             | true             | false           |
| `nav_buscar_semantico` | true           | false             | true             | false           |
| `nav_manifesto`        | true           | false             | true             | false           |

O servidor NÃO DEVE expor tools de reset de navegação nem de execução em lote.

#### Scenario: Listagem determinística

- **WHEN** o cliente envia `tools/list`
- **THEN** o servidor DEVE devolver as sete tools `nav_*` em ordem alfabética, cada uma com `title` e anotações completas

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

O servidor MCP DEVE apenas ler o cache local por meio do núcleo de navegação. Ele NÃO DEVE expor, e as tools NÃO DEVEM permitir, consultas à B3/CVM, download, extração, resumo ou escrita de estado.

#### Scenario: Somente leitura

- **WHEN** qualquer tool `nav_*` é invocada
- **THEN** nenhuma escrita de estado, download ou consulta externa DEVE ocorrer
