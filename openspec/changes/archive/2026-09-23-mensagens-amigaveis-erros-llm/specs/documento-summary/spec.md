## MODIFIED Requirements

### Requirement: Propagação das exceções tipadas

O serviço DEVE propagar as exceções tipadas da `llm-core` (`LLMUnavailableError`, `LLMConfigurationError`, `LLMCommunicationError`, `LLMProviderError`, `LLMServiceUnavailableError`, `LLMRateLimitError`) para que o consumidor decida como exibir a falha.

#### Scenario: LLM indisponível
- **WHEN** a porta lança `LLMUnavailableError`
- **THEN** a exceção DEVE propagar para o consumidor sem ser convertida

#### Scenario: Falha de comunicação
- **WHEN** a porta lança `LLMCommunicationError`
- **THEN** a exceção DEVE propagar para o consumidor sem ser convertida

#### Scenario: Provedor temporariamente indisponível
- **WHEN** a porta lança `LLMServiceUnavailableError`
- **THEN** a exceção DEVE propagar para o consumidor sem ser convertida
