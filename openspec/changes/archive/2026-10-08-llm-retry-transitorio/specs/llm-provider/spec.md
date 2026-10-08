## ADDED Requirements

### Requirement: Retry de erros transitórios no adaptador liteLLM

O adaptador de LLM DEVE repetir automaticamente as chamadas que falham por erro **transitório** — indisponibilidade do provedor, cota excedida e falha de comunicação (`LLMServiceUnavailableError`, `LLMRateLimitError` e `LLMCommunicationError`) — até um número máximo de tentativas configurável. Erros **permanentes** (`LLMProviderError`, `LLMConfigurationError` e `LLMUnavailableError`) NÃO DEVEM ser repetidos e DEVEM propagar imediatamente. Entre tentativas, o adaptador DEVE aguardar um backoff crescente com variação aleatória (jitter). Ao esgotar as tentativas, o adaptador DEVE propagar a última exceção de domínio, preservando o comportamento atual do chamador.

#### Scenario: Erro transitório seguido de sucesso

- **WHEN** a primeira tentativa falha com `LLMServiceUnavailableError` e uma tentativa seguinte tem sucesso
- **THEN** a resposta DEVE ser retornada normalmente, sem propagar o erro

#### Scenario: Tentativas esgotadas

- **WHEN** todas as tentativas falham com erro transitório
- **THEN** o adaptador DEVE propagar a exceção de domínio correspondente ao último erro

#### Scenario: Erro permanente não é repetido

- **WHEN** a chamada falha com `LLMProviderError`, `LLMConfigurationError` ou `LLMUnavailableError`
- **THEN** o erro DEVE propagar imediatamente, sem novas tentativas

#### Scenario: Espera entre tentativas

- **WHEN** uma tentativa falha com erro transitório e ainda restam tentativas
- **THEN** o adaptador DEVE aguardar um intervalo de backoff crescente com jitter antes da próxima tentativa

### Requirement: Tentativas contam no rate limiting

Cada tentativa física de chamada ao provedor, incluindo as repetições por erro transitório, DEVE adquirir uma permissão do rate limiter configurado, de modo que os retries respeitem o limite de requisições por minuto.

#### Scenario: Retry consome cota

- **WHEN** uma chamada exige retry e obtém sucesso na segunda tentativa
- **THEN** o rate limiter DEVE registrar duas aquisições para essa chamada

#### Scenario: Chamada sem retry consome uma permissão

- **WHEN** uma chamada obtém sucesso na primeira tentativa
- **THEN** o rate limiter DEVE registrar exatamente uma aquisição
