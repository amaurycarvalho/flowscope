## MODIFIED Requirements

### Requirement: Operações canônicas do núcleo

O núcleo DEVE suportar exatamente as operações `listar`, `obter`, `contar`, `existe`, `buscar`, `buscar_semantico`, `data_referencia` e o manifesto de navegação. A operação `data_referencia` NÃO DEVE exigir campos e DEVE devolver a data de referência resolvida da última carga de fundamentos. O núcleo NÃO DEVE expor operações de reset de navegação nem de execução em lote. Operações DEVEM ser executadas na ordem em que são submetidas, com resultado por operação e sem timestamps.

#### Scenario: Operação desconhecida é recusada

- **WHEN** uma operação fora do conjunto canônico é submetida
- **THEN** o núcleo DEVE devolver erro estruturado com motivo de operação desconhecida e a lista de operações válidas

#### Scenario: Reset e lote não existem no núcleo

- **WHEN** o catálogo de operações do núcleo é enumerado
- **THEN** ele NÃO DEVE conter operações de reset de navegação nem de execução em lote

#### Scenario: Data de referência resolvida

- **WHEN** a operação `data_referencia` é executada sem campos
- **THEN** o núcleo DEVE devolver a data de referência resolvida (marcador `last_fundamentals` ou fallback `last_date`), sem consultar a rede
