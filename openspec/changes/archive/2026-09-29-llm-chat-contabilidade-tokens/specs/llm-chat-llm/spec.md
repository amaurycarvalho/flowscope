## ADDED Requirements

### Requirement: Estimativa determinística de cache de prompt

Quando o provedor não reportar tokens de cache-hit em uma completion, o sistema DEVE estimar de forma determinística os tokens servidos por cache e preencher `LLMUsage.entrada_cache` antes de contabilizar o uso. A estimativa DEVE ocorrer somente quando (a) o provedor suportar cache de prompt e (b) o prefixo estável enviado for idêntico byte-a-byte ao de uma completion anterior. O valor estimado DEVE ser a contagem de tokens do prefixo estável (prompt de sistema, instrução de formato e bloco estável) e DEVE ser reutilizado por assinatura, sem recontagem a cada turno. A estimativa NÃO DEVE ser aplicada sobre tokens de cache-write.

#### Scenario: Prefixo inalterado estima o cache

- **WHEN** o prefixo estável é idêntico ao de uma completion anterior, o provedor suporta cache e não reporta cache-hit
- **THEN** `entrada_cache` DEVE ser preenchido com a contagem de tokens do prefixo estável

#### Scenario: Primeira completion não estima

- **WHEN** não há completion anterior com o mesmo prefixo estável na sessão
- **THEN** nenhuma estimativa de cache DEVE ser aplicada

#### Scenario: Prefixo alterado não estima

- **WHEN** o contexto estável mudou e o prefixo foi reconstruído
- **THEN** nenhuma estimativa de cache DEVE ser aplicada nessa completion

#### Scenario: Provedor sem suporte não estima

- **WHEN** o provedor não suporta cache de prompt e não reporta cache-hit
- **THEN** nenhuma estimativa DEVE ser aplicada e `entrada_cache` DEVE permanecer zero

#### Scenario: Cache reportado pelo provedor tem precedência

- **WHEN** o provedor reporta tokens de cache-hit
- **THEN** o valor reportado DEVE ser usado e nenhuma estimativa DEVE substituí-lo
