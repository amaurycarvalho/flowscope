## Context

Ver `proposal.md` — Why. O lote de resumo compartilha o trabalho `executar_resumos` (`presentation/gui/resumos_job.py`), que percorre os itens em duas fases e publica eventos pelo `JobContext`. A política de continuidade por item (`continuar_em_erro`) é `False` para Documentos e `True` para Notícias (`app_resumos_actions._resumir_noticias_pendentes`). Hoje qualquer exceção em `_resumir` publica um `Erro` e, se `continuar_em_erro`, prossegue — de modo que uma cota esgotada gera uma tentativa falha por item. O adaptador (`infrastructure/llm/adapter.py`) já mapeia HTTP 429 para `LLMRateLimitError` e o classifica como transitório, repetindo a chamada até 3 vezes por item.

## Goals / Non-Goals

**Goals:**
- Interromper o lote imediatamente quando o provedor esgotar cota/limite, em ambos os painéis.
- Preservar os resumos já gravados e manter pendentes os itens não processados.
- Reportar a cota uma única vez, com mensagem que oriente aguardar/reconfigurar, e registrar em log sem traceback por item.

**Non-Goals:**
- Distinguir 429 de cota diária de 429 de janela por minuto.
- Alterar a política de retry do adaptador ou o rate limiter.
- Adicionar confirmação prévia para lotes grandes (fica para uma change futura, se necessário).

## Decisions

### 1. Cota esgotada é fatal para o lote, no próprio trabalho

Em `_resumir`, capturar `LLMRateLimitError` antes do `except Exception` genérico: publicar `ctx.erro` e **retornar**, independentemente de `continuar_em_erro`. Assim o sinal de cota interrompe a fase de resumo e o `executar_resumos` encerra. Alternativa: continuar e apenas contar a falha — rejeitada, pois mantém o martelo na API e o flood de logs.

### 2. O host distingue a interrupção por cota

`_interromper_resumos` verifica `isinstance(exc, LLMRateLimitError)`, marca `_resumos_cota` e registra um único `logger.warning` **sem** `exc_info`. Como o lote aborta na primeira ocorrência, não há traceback por item. Em `_finalizar_resumos_job`, quando `_resumos_cota`, exibir um desfecho único com a contagem gerada e a orientação, suprimindo a mensagem normal. Alternativa: reusar a mensagem de itens para cota — rejeitada por ser ambígua e ruidosa.

### 3. Mensagem dedicada de cota

`mensagem_erro_llm` para `LLMRateLimitError` passa a mencionar o limite de uso da IA e a possibilidade de aguardar a renovação ou reconfigurar o provedor, distinta da mensagem genérica do provedor.

### 4. Sem alteração no adaptador

O retry transitório do adaptador é mantido: o limite por RPM já suaviza a cadência e a interrupção no lote resolve o caso de cota esgotada. Mexer no retry exigiria distinguir tipos de 429, o que é frágil.

## Risks / Trade-offs

- [429 transitório de janela por minuto também aborta o lote] → o rate limiter de RPM já evita rajadas; abortar é preferível a insistir. O usuário retoma quando quiser.
- [Abortar perde o resumo parcial do item corrente] → mitigação já existente: cada resumo é gravado imediatamente após a geração, então só o item em processamento é perdido.
- [Mensagem única pode esconder que houve itens pulados] → o desfecho inclui a contagem gerada; os pendentes seguem visíveis pelo botão reabilitado.

## Migration Plan

Sem migração. Itens não processados permanecem pendentes e são retomados num novo lote quando a cota for restabelecida. Rollback: remover o tratamento específico de `LLMRateLimitError` resta para o comportamento atual de continuidade.

## Open Questions

Nenhuma pendente.
