# Spec Delta

## MODIFIED Requirements

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

### Requirement: Escopo restrito de leitura

Durante o atendimento, o servidor MCP DEVE apenas ler o cache local por meio do núcleo de navegação e do cache do calendário. Ele NÃO DEVE expor, e as tools NÃO DEVEM permitir, consultas à B3/CVM, download, extração, resumo ou escrita de estado. A preparação opcional executada antes de o servidor começar a atender (ver o requisito de preparação na inicialização) não é uma tool e NÃO DEVE ser acessível pelo protocolo.

#### Scenario: Somente leitura
- **WHEN** qualquer tool `nav_*` ou `calendario_*` é invocada
- **THEN** nenhuma escrita de estado, download ou consulta externa DEVE ocorrer

#### Scenario: Preparação não é exposta como tool
- **WHEN** o cliente envia `tools/list`
- **THEN** o catálogo NÃO DEVE conter tool de carregar watchlist nem de atualizar fundamentos

## ADDED Requirements

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
