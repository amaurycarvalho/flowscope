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
