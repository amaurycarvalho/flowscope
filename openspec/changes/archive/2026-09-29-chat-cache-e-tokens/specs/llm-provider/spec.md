## MODIFIED Requirements

### Requirement: Porta genérica de completion

O sistema DEVE definir uma porta `LLMPort` com um método `complete(messages: list[dict], system_prompt: str | None = None) -> LLMResposta` que envia uma lista de mensagens no formato `{"role", "content"}` e retorna o texto da resposta e o uso de tokens reportado pelo provedor. `LLMResposta` DEVE expor `texto: str` e `uso: LLMUsage`, e `LLMUsage` DEVE expor `entrada: int` e `saida: int`, com zero quando o provedor não reportar o dado. Consumidores DEVEM depender apenas dessa porta, nunca do liteLLM diretamente.

#### Scenario: Completion com histórico e system prompt

- **WHEN** `complete([{"role": "user", "content": "Olá"}], system_prompt="Seja conciso")` é chamado
- **THEN** a resposta DEVE ser retornada como `LLMResposta`, com o texto em `texto` e o uso em `uso`

#### Scenario: Completion sem system prompt

- **WHEN** `complete([{"role": "user", "content": "hello"}])` é chamado
- **THEN** a chamada DEVE ser enviada sem mensagem de sistema e a resposta DEVE ser retornada como `LLMResposta`

#### Scenario: Uso de tokens reportado

- **WHEN** o provedor reporta `prompt_tokens` e `completion_tokens` na resposta
- **THEN** `LLMResposta.uso.entrada` e `LLMResposta.uso.saida` DEVEM conter esses valores

#### Scenario: Uso ausente

- **WHEN** o provedor não reporta o uso de tokens
- **THEN** `LLMResposta.uso.entrada` e `LLMResposta.uso.saida` DEVEM ser zero, sem erro

## ADDED Requirements

### Requirement: Uso de tokens no adaptador liteLLM

O adaptador sobre o liteLLM DEVE extrair o uso de tokens do atributo `usage` da resposta do provedor e traduzi-lo para `LLMUsage`, tolerando a ausência do atributo sem falhar.

#### Scenario: Resposta com usage

- **WHEN** a resposta do liteLLM traz `usage.prompt_tokens` e `usage.completion_tokens`
- **THEN** o adaptador DEVE devolver esses valores em `LLMUsage`

#### Scenario: Resposta sem usage

- **WHEN** a resposta do liteLLM não traz o atributo `usage`
- **THEN** o adaptador DEVE devolver `LLMUsage` com zeros, sem lançar exceção
