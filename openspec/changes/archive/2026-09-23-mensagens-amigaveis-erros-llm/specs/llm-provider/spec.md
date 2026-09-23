## MODIFIED Requirements

### Requirement: Exceções tipadas de LLM

O sistema DEVE definir uma hierarquia de exceções com uma base `LLMError` e subclasses que permitam aos consumidores distinguir a causa da falha:

- `LLMUnavailableError`: LLM indisponível (provedor `none` ou dependências `[llm]` ausentes).
- `LLMConfigurationError`: configuração inválida (ex.: provedor `custom` sem `model` ou sem `api_url`).
- `LLMCommunicationError`: falha de comunicação com o provedor (timeout, conexão).
- `LLMProviderError`: erro retornado pelo provedor (autenticação, requisição inválida).
- `LLMServiceUnavailableError`: provedor temporariamente indisponível por sobrecarga ou erro 5xx.
- `LLMRateLimitError`: cota do provedor excedida.

#### Scenario: Provedor none
- **WHEN** o provedor configurado é `none`
- **THEN** qualquer chamada DEVE lançar `LLMUnavailableError`

#### Scenario: Dependências ausentes
- **WHEN** o liteLLM não está instalado e uma chamada é tentada
- **THEN** o sistema DEVE lançar `LLMUnavailableError`

#### Scenario: Timeout do provedor
- **WHEN** a chamada ao provedor excede o tempo limite
- **THEN** o sistema DEVE lançar `LLMCommunicationError`

#### Scenario: Cota excedida
- **WHEN** o provedor responde com erro de limite de cota (HTTP 429)
- **THEN** o sistema DEVE lançar `LLMRateLimitError`

#### Scenario: Erro de autenticação ou requisição inválida
- **WHEN** o provedor responde com erro de autenticação ou de requisição inválida
- **THEN** o sistema DEVE lançar `LLMProviderError`

#### Scenario: Erro interno do provedor
- **WHEN** o provedor responde com indisponibilidade temporária (ex.: HTTP 503 por alta demanda ou outro erro 5xx)
- **THEN** o sistema DEVE lançar `LLMServiceUnavailableError`

## ADDED Requirements

### Requirement: Ausência do banner de depuração do liteLLM no terminal

O adaptador DEVE desabilitar a saída de depuração do liteLLM para que falhas do provedor não escrevam as linhas `Give Feedback / Get Help` e `LiteLLM.Info` na saída do terminal, mantendo a exceção tipada e o registro em log inalterados.

#### Scenario: Falha do provedor não imprime banner
- **WHEN** uma chamada ao provedor falha e a exceção é mapeada para o domínio
- **THEN** as linhas de depuração do liteLLM NÃO DEVEM ser escritas na saída padrão

#### Scenario: Exceção tipada continua propagando
- **WHEN** a chamada ao provedor falha
- **THEN** a exceção tipada correspondente DEVE seguir sendo lançada e registrada em log
