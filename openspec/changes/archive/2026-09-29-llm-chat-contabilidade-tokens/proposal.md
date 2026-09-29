## Why

A barra de status soma ao total de entrada todo o `prompt_tokens` reportado pelo provedor, incluindo os tokens servidos por cache de prompt. Como o prefixo estável (conhecimento, fundamentos e resumos) se repete a cada turno, o total exibido superestima o custo real do chat. Também não há visibilidade de quanto da janela de contexto a chamada atual ocupa.

## What Changes

- `LLMUsage` passa a reportar os tokens de cache-hit (leitura) e de cache-write, além de entrada e saída; o adaptador liteLLM extrai `usage.prompt_tokens_details.cached_tokens`, tolerando a ausência.
- A barra de status acumula `entrada_real = prompt_tokens - cached_tokens`, exibindo o total de entrada novo (não cacheado).
- Quando o provedor não reporta cache, um fallback determinístico estima o cache-hit: apenas para provedores que suportam cache e quando a assinatura do bloco estável não muda entre envios, usando a contagem de tokens do prefixo estável (`system` + instrução de formato + bloco estável) via `litellm.token_counter`.
- A barra de status passa a exibir o percentual ocupado da janela de contexto, entre parênteses e sem casa decimal, calculado a partir do `prompt_tokens` bruto da completion atual sobre a janela do modelo.
- Os presets ganham `context_window` como tamanho default por provedor/modelo; a resolução via `litellm.get_model_info(...)["max_input_tokens"]` enriquece o valor quando disponível.

## Capabilities

### New Capabilities

<!-- Nenhuma: a mudança estende o uso de tokens e o rótulo já existentes. -->

### Modified Capabilities

- `llm-chat-tokens`: o acúmulo de entrada passa a descontar os tokens de cache-hit e o rótulo passa a exibir o percentual da janela de contexto.
- `llm-provider`: o `LLMUsage` do adaptador reporta tokens de cache e a resolução de presets/modelo expõe a janela de contexto (`context_window` + `liteLLM.get_model_info`).
- `llm-chat-llm`: o use case estima de forma determinística o cache-hit quando o provedor não o reporta, condicionado à estabilidade do prefixo.

## Impact

- **Código**: `domain/llm/ports.py` (`LLMUsage`), `infrastructure/llm/adapter.py` (`_extrair_uso`), `infrastructure/llm/presets.py` (`context_window`), `application/chat/consultar.py` (estimativa), `presentation/gui/chat/tokens.py` (`ContadorTokens`, formatação), `presentation/gui/chat/chat_panel.py` e `app_status.py` (rótulo).
- **Dependências**: usa `litellm.token_counter` e `litellm.get_model_info` (já no grupo `[llm]`; nenhuma dependência nova).
- **Cache/Contadores**: nenhum novo cache persistente; a estimativa de fallback reusa o `litellm.token_counter`.
- **Compatibilidade**: campos novos de `LLMUsage` com default zero, sem quebrar consumidores (guidance, RAG).
