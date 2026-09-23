# llm-provider Specification

## Purpose

Fornece a camada base reutilizável de consumo de LLM: uma porta genérica de completion, um adaptador sobre o liteLLM com presets de provedores, throttling configurável por RPM e exceções tipadas para que os consumidores (chat RAG, resumo de documentos) decidam como reagir a cada situação.

## Requirements

### Requirement: Porta genérica de completion

O sistema DEVE definir uma porta `LLMPort` com um método `complete(messages: list[dict], system_prompt: str | None = None) -> str` que envia uma lista de mensagens no formato `{"role", "content"}` e retorna a resposta do LLM como string. Consumidores DEVEM depender apenas dessa porta, nunca do liteLLM diretamente.

#### Scenario: Completion com histórico e system prompt
- **WHEN** `complete([{"role": "user", "content": "Olá"}], system_prompt="Seja conciso")` é chamado
- **THEN** a resposta do LLM DEVE ser retornada como string

#### Scenario: Completion sem system prompt
- **WHEN** `complete([{"role": "user", "content": "hello"}])` é chamado
- **THEN** a chamada DEVE ser enviada sem mensagem de sistema e a resposta DEVE ser retornada como string

### Requirement: Adaptador liteLLM com presets de provedores

O sistema DEVE implementar um adaptador de LLM sobre `litellm.completion()` que aceita `model`, `api_url` e `api_key`. O adaptador DEVE usar `custom_llm_provider="openai"` e `api_base=<api_url>` quando um `api_url` for informado. O sistema DEVE fornecer presets pré-configurados para os provedores suportados:

| Provedor | Modelo | API URL |
|---|---|---|
| `none` | — (determinístico) | — (sem rede) |
| `openai` | `gpt-4o-mini` | `https://api.openai.com/v1` |
| `gemini` | `gemini-3.1-flash-lite` | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `copilot` | `gpt-4o` | `https://models.inference.ai.azure.com` |
| `claude` | `claude-sonnet-4-20250514` | `https://api.anthropic.com/v1` |
| `deepseek` | `deepseek-chat` | `https://api.deepseek.com/v1` |
| `ollama` | `llama3.2` | `http://localhost:11434/v1` |
| `custom` | definido pelo usuário | definido pelo usuário |

#### Scenario: Completion via OpenAI
- **WHEN** o provedor `openai` é usado
- **THEN** a chamada DEVE usar `model="gpt-4o-mini"` e `api_base="https://api.openai.com/v1"`

#### Scenario: Completion via provedor com API URL customizada
- **WHEN** o provedor `custom` é usado com `model` e `api_url` informados
- **THEN** a chamada DEVE usar o modelo e a `api_base` informados

#### Scenario: Provedor desconhecido
- **WHEN** um provedor fora dos presets é informado
- **THEN** o sistema DEVE rejeitar a configuração com uma exceção de configuração

### Requirement: Rate limiting com RPM configurável

O sistema DEVE limitar a taxa de chamadas LLM a um número configurável de requisições por minuto (RPM), com valor padrão de 5 RPM. Ao atingir o limite, as chamadas DEVEM ser enfileiradas e aguardar a liberação de uma janela, em vez de falharem. O rate limiter DEVE ser seguro para uso concorrente a partir de múltiplas threads.

#### Scenario: Chamadas acima do limite são desaceleradas
- **WHEN** mais chamadas do que o RPM configurado são feitas em sequência
- **THEN** as chamadas excedentes DEVEM aguardar até que uma nova janela de permissão se abra, sem erro de cota

#### Scenario: RPM padrão
- **WHEN** nenhum RPM é informado na configuração
- **THEN** o limite DEVE ser de 5 requisições por minuto

#### Scenario: RPM customizado
- **WHEN** o RPM é configurado como 15
- **THEN** o rate limiter DEVE permitir até 15 requisições por minuto

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

### Requirement: Factory de provedor LLM

O sistema DEVE fornecer `create_llm_provider(config: dict) -> LLMPort` que instancia o adaptador a partir de `provider`, `api_url`, `model`, `api_key` e `rpm`. A factory DEVE lançar `LLMUnavailableError` quando o provedor for `none` ou as dependências `[llm]` estiverem ausentes, e `LLMConfigurationError` quando o provedor `custom` não tiver `model` ou `api_url`.

#### Scenario: Provider configurado
- **WHEN** a config tem `provider: "deepseek"`, `model: "deepseek-chat"` e `api_key` preenchida
- **THEN** a factory DEVE retornar um `LLMPort` pronto para uso

#### Scenario: Provider none
- **WHEN** a config tem `provider: "none"`
- **THEN** a factory DEVE lançar `LLMUnavailableError`

#### Scenario: Custom incompleto
- **WHEN** a config tem `provider: "custom"` sem `model`
- **THEN** a factory DEVE lançar `LLMConfigurationError`

### Requirement: Ausência do banner de depuração do liteLLM no terminal

O adaptador DEVE desabilitar a saída de depuração do liteLLM para que falhas do provedor não escrevam as linhas `Give Feedback / Get Help` e `LiteLLM.Info` na saída do terminal, mantendo a exceção tipada e o registro em log inalterados.

#### Scenario: Falha do provedor não imprime banner
- **WHEN** uma chamada ao provedor falha e a exceção é mapeada para o domínio
- **THEN** as linhas de depuração do liteLLM NÃO DEVEM ser escritas na saída padrão

#### Scenario: Exceção tipada continua propagando
- **WHEN** a chamada ao provedor falha
- **THEN** a exceção tipada correspondente DEVE seguir sendo lançada e registrada em log
