## Why

A captura de guidance da watchlist está funcional e cobre os RGs mais recentes, mas a qualidade da informação derivada ainda é frágil: quando o mesmo RG possui avaliação `ia` e `deterministico`, a derivação do guidance corrente pode escolher o determinístico (`RZAK11` expõe `1,05` em vez da faixa `1,00–1,10`), períodos vagos como “não especificado” são aceitos, e uma resposta ruim marcada como `ia` nunca é reavaliada. Isso permite que o valor exibido fique incorreto ou desatualizado sem qualquer sinal.

## What Changes

- Derivar o guidance corrente com desempate explícito: entre entradas com a mesma data de relatório, `ia` prevalece sobre `deterministico`; persistir o momento da avaliação para desempatar avaliações do mesmo método.
- Registrar no ledger a proveniência da avaliação (`avaliado_em`, versão do prompt e, quando disponível, modelo) e reavaliar entradas `ia` quando a versão do prompt/modelo mudar, tratando entradas antigas sem versão como desatualizadas.
- Tornar a interpretação da resposta da IA tolerante a formato (`R$`, separador de milhar, faixa, “por cota”) e tratar `GUIDANCE: SIM` sem valores interpretáveis como falha da IA, recorrendo à extração determinística em vez de gravar ausência indevida.
- Normalizar o período retornado pela IA, convertendo valores vagos (`não especificado`, `sem período`, `N/A`) em ausência de período e preservando períodos reconhecidos.
- Registrar em log o conflito em que a IA conclui ausência em todas as fontes, mas o extrator determinístico encontra guidance, sem sobrescrever automaticamente a decisão da IA.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `relatorio-gerencial-guidance`: a derivação do guidance corrente passa a desempatar por método e momento da avaliação; o ledger passa a guardar proveniência/versão e a permitir reavaliação por mudança de prompt/modelo; a leitura da resposta da IA passa a ser tolerante e a tratar resposta incompleta como falha com fallback determinístico; o período passa a ser normalizado.

## Impact

- Código: `domain/fii/guidance.py`, `infrastructure/guidance_store.py`, `application/avaliar_guidance.py`, `application/documentos/document_guidance.py`, `infrastructure/llm/adapter.py` (exposição do modelo, se disponível) e teste/fixtures de guidance.
- Cache: `~/.cache/flowscope/guidance/<TICKER>.json` ganha campos opcionais de proveniência; entradas antigas continuam legíveis e são consideradas desatualizadas para reavaliação por IA.
- Sem novas dependências e sem mudança na prioridade global das fontes fundamentalistas.
- A correção de `RZAK11` e `GGRC11` aparece na próxima leitura do ledger/derivação; a reavaliação por IA ocorre no próximo processamento de RGs (leitura ou “Resumir pendentes”).
