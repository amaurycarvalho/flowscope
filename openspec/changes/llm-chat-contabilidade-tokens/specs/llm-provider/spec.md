## MODIFIED Requirements

### Requirement: Porta genérica de completion

O sistema DEVE definir uma porta `LLMPort` com um método `complete(messages: list[dict], system_prompt: str | None = None) -> LLMResposta` que envia uma lista de mensagens no formato `{"role", "content"}` e retorna o texto da resposta e o uso de tokens reportado pelo provedor. `LLMResposta` DEVE expor `texto: str` e `uso: LLMUsage`, e `LLMUsage` DEVE expor `entrada: int`, `saida: int`, `entrada_cache: int` e `cache_write: int`, com zero quando o provedor não reportar o dado. Consumidores DEVEM depender apenas dessa porta, nunca do liteLLM diretamente.

#### Scenario: Completion com histórico e system prompt

- **WHEN** `complete([{"role": "user", "content": "Olá"}], system_prompt="Seja conciso")` é chamado
- **THEN** a resposta DEVE ser retornada como `LLMResposta`, com o texto em `texto` e o uso em `uso`

#### Scenario: Completion sem system prompt

- **WHEN** `complete([{"role": "user", "content": "hello"}])` é chamado
- **THEN** a chamada DEVE ser enviada sem mensagem de sistema e a resposta DEVE ser retornada como `LLMResposta`

#### Scenario: Uso de tokens reportado

- **WHEN** o provedor reporta `prompt_tokens` e `completion_tokens` na resposta
- **THEN** `LLMResposta.uso.entrada` e `LLMResposta.uso.saida` DEVEM conter esses valores

#### Scenario: Uso com cache reportado

- **WHEN** o provedor reporta tokens de cache-hit e de cache-write na resposta
- **THEN** `LLMResposta.uso.entrada_cache` e `LLMResposta.uso.cache_write` DEVEM conter esses valores

#### Scenario: Uso ausente

- **WHEN** o provedor não reporta o uso de tokens
- **THEN** `LLMResposta.uso.entrada`, `saida`, `entrada_cache` e `cache_write` DEVEM ser zero, sem erro

### Requirement: Uso de tokens no adaptador liteLLM

O adaptador sobre o liteLLM DEVE extrair o uso de tokens do atributo `usage` da resposta do provedor e traduzi-lo para `LLMUsage`, tolerando a ausência do atributo e dos campos de cache sem falhar. Os tokens de cache-hit DEVEM ser lidos de `usage.prompt_tokens_details.cached_tokens` e os de cache-write de `usage.prompt_tokens_details.cache_creation_tokens` ou `cache_write_tokens`, cobrindo os nomes nativos normalizados pelo liteLLM (OpenAI, DeepSeek, Gemini e Anthropic).

#### Scenario: Resposta com usage

- **WHEN** a resposta do liteLLM traz `usage.prompt_tokens` e `usage.completion_tokens`
- **THEN** o adaptador DEVE devolver esses valores em `LLMUsage`

#### Scenario: Resposta com cache-hit

- **WHEN** a resposta do liteLLM traz `usage.prompt_tokens_details.cached_tokens`
- **THEN** o adaptador DEVE devolver esse valor em `LLMUsage.entrada_cache`

#### Scenario: Resposta sem usage

- **WHEN** a resposta do liteLLM não traz o atributo `usage`
- **THEN** o adaptador DEVE devolver `LLMUsage` com zeros, sem lançar exceção

#### Scenario: Uso sem detalhes de cache

- **WHEN** a resposta do liteLLM traz `usage` sem `prompt_tokens_details`
- **THEN** o adaptador DEVE devolver `entrada_cache` e `cache_write` iguais a zero, sem lançar exceção

## ADDED Requirements

### Requirement: Janela de contexto e suporte a cache nos presets

O sistema DEVE associar a cada preset de provedor/modelo uma janela de contexto padrão (`context_window`) e um indicativo de suporte a cache de prompt. A resolução da janela DEVE preferir a informação do liteLLM (`get_model_info(...)["max_input_tokens"]`) quando disponível e cair no valor do preset como fallback, sem exigir rede nem a dependência opcional. A informação DEVE ficar acessível aos consumidores pela infraestrutura, sem que a apresentação importe o liteLLM.

#### Scenario: Janela do preset como fallback

- **WHEN** a informação do liteLLM não está disponível para o modelo
- **THEN** a janela de contexto DEVE ser o valor `context_window` do preset do provedor

#### Scenario: Janela enriquecida pelo liteLLM

- **WHEN** o liteLLM expõe `max_input_tokens` para o modelo
- **THEN** a janela de contexto DEVE usar esse valor

#### Scenario: Suporte a cache declarado no preset

- **WHEN** o provedor suporta cache de prompt
- **THEN** o preset DEVE indicar esse suporte para habilitar a estimativa determinística do chat
