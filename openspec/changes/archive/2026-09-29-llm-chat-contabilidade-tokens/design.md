## Context

Ver `proposal.md` — Why. O acúmulo atual (`ContadorTokens.acumular`, `presentation/gui/chat/tokens.py:30`) soma `LLMUsage.entrada` cru, e o adaptador (`infrastructure/llm/adapter.py:112`) só lê `prompt_tokens`/`completion_tokens`. O prefixo estável é reenviado a cada turno e memoizado por assinatura em `presentation/gui/chat/envio.py:118` (`_bloco_cache`), o que dá a evidência determinística de quando o provedor pode ter cacheado. O liteLLM 1.101.0 normaliza `usage.prompt_tokens_details.cached_tokens` para os provedores suportados e expõe a janela via `get_model_info(...)["max_input_tokens"]`.

## Goals / Non-Goals

**Goals:**

- Exibir na barra de status o total de entrada **novo** (não cacheado) e o **% de ocupação da janela de contexto** da chamada atual.
- Reportar o cache-hit do provedor no domínio, sem que a apresentação dependa do liteLLM.
- Estimar o cache-hit de forma determinística quando o provedor omitir o dado.

**Non-Goals:**

- Não mudar o comportamento de cache do provedor (nenhum `cache_control`/marcação de prefixo é enviado).
- Não persistir histórico de tokens entre sessões.
- Não alterar o gate de confirmação nem a composição do prompt (isso é da change `llm-chat-contexto-sob-demanda`).
- Não cobrar/estimar custo monetário.

## Decisions

### D1: `LLMUsage` reporta cache-read e cache-write

Adicionar campos com default zero em `LLMUsage` (`domain/llm/ports.py`): `entrada_cache` (tokens de leitura de cache) e `cache_write` (tokens de criação de cache). O adaptador lê `usage.prompt_tokens_details.cached_tokens` e `cache_creation_tokens`/`cache_write_tokens`, tolerando `None`, `dict` ou objeto. Campos com default não quebram consumidores (guidance, RAG).

**Alternativas:** ler `_hidden_params.cache_hit` (booleano, informação pobre); ler `usage.cache_read_input_tokens` direto (não normalizado entre provedores).

### D2: Semântica do rótulo — custo vs. ocupação

- A **entrada acumulada** na barra de status passa a somar `entrada_real = prompt_tokens - cached_tokens`.
- O **% da janela** usa o `prompt_tokens` **bruto** da completion atual (cache incluído), pois cache ainda ocupa espaço no contexto.

Decisão confirmada com o usuário (opção A). São dois números derivados do mesmo `LLMUsage`. O rótulo passa a exibir três valores separados por ` / `, no formato `Tokens: X entrada / Y saída / Z contexto (N%)`, em que `Z` é o `prompt_tokens` bruto da completion mais recente (base do percentual), rotulado `contexto` e formatado como os demais. Quando a janela é desconhecida, o percentual é omitido, mas `Z contexto` permanece.

**Alternativas descartadas:** `%` sobre a entrada ajustada (subestima a ocupação) e `%` sobre o acumulado da sessão (ultrapassa 100% e não representa a janela).

### D3: Estimativa de fallback no caso de uso, com confirmação de assinatura

Quando o provedor não reporta `cached_tokens`, estimar `entrada_cache` como a contagem de tokens do prefixo estável (`system` + instrução de formato + bloco estável) — a porção comprovadamente idêntica — e só quando:

1. a assinatura do bloco estável **não mudou** em relação ao envio anterior (informação já disponível via `_bloco_cache`/`assinatura`), e
2. o provedor **suporta cache de prompt** (flag no preset).

A estimativa vive em `application/chat/consultar.py`, que já monta o prefixo e recebe o `uso` de cada completion. Dependências injetadas: um contador de tokens (porta na fronteira) e a flag de suporte a cache. O resultado é memoizado por assinatura para não recontar a cada turno.

**Alternativas:** estimar na apresentação (importaria liteLLM, hoje proibido) ou no adaptador (não conhece a assinatura nem o turno anterior).

### D4: Janela de contexto resolvida na infraestrutura

`PROVIDER_PRESETS` (`infrastructure/llm/presets.py`) ganha `context_window` por provedor/modelo como default. A resolução via `litellm.get_model_info(model)["max_input_tokens"]` enriquece o valor quando disponível, ficando atrás de uma porta/adapte de infraestrutura para a apresentação não importar liteLLM. O `%` é `int(prompt_tokens * 100 / context_window)`.

**Alternativas:** só presets (perde atualização do registro do liteLLM) ou só liteLLM (quebra sem a dependência opcional e sem rede).

### D5: Contagem de tokens sem nova dependência

Usar `litellm.token_counter(model=..., text=...)`, já empacotado no grupo `[llm]` (o build já coleta os encodings do tiktoken, conforme `llm-config`). Nenhuma dependência nova.

## Risks / Trade-offs

- [Estimativa pode "inventar" cache que não ocorreu] → só estimar com suporte declarado no preset e assinatura inalterada; nunca estimar sobre `cache_write`.
- [Contagem de tokens a cada turno adiciona latência] → memoizar por assinatura do prefixo.
- [Janela default divergente do provedor real] → preferir `get_model_info`; presets são fallback; o `%` pode passar de 100 se a janela estiver desatualizada, e isso é aceitável como sinal.
- [Provedores OpenAI-compatible reportam `cached_tokens` de formas diferentes] → leitura tolerante no adaptador, cobrindo os nomes nativos normalizados pelo liteLLM.
- [Somar 3 chamadas (change B) aumenta o peso do cache] → sem impacto neste desenho; cada completion é contabilizada individualmente.

## Migration Plan

1. Estender `LLMUsage` (compatível).
2. Estender `_extrair_uso` e os presets (`context_window`, flag de cache).
3. Adicionar o contador/porta e a resolução de janela na infraestrutura; ligar no wiring.
4. Ajustar `ContadorTokens` e a formatação; atualizar o rótulo.
5. Implementar a estimativa em `ConsultarChatUseCase` e seu teste.
6. Atualizar specs e testes; sem migração de `config.json` (nenhum campo persistido novo).

## Open Questions

- Nenhuma bloqueante. O nome final da flag de suporte a cache nos presets (`cache_prompt`) fica a critério da implementação.
