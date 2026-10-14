## Context

Ver `proposal.md` — Why. Hoje `ResumirDocumentoUseCase.resumir` (`application/resumo_documento.py`) e `AvaliarGuidanceUseCase._tentar_llm` (`application/avaliar_guidance.py`) montam uma única mensagem `user` colando instruções e conteúdo, sem `system_prompt`. A porta `LLMPort.complete(messages, system_prompt)` e o `LiteLLMChatAdapter` já prefixam uma mensagem `system` quando ela é informada, então a mudança é restrita à camada de aplicação. O chat já usa esse padrão de prefixo estável (`application/chat/consultar.py`), servindo de referência.

## Goals / Non-Goals

**Goals:**
- Instruções de resumo e de avaliação de guidance em prefixos de sistema constantes e idênticos entre itens.
- Mensagem `user` restrita ao conteúdo variável (texto do documento ou trecho).
- Legibilidade/manutenabilidade: instruções como constante nomeada no módulo do caso de uso.
- Documentar o payload separado em `docs/misc/llm-payloads.md`.

**Non-Goals:**
- Adicionar `cache_control` ou qualquer marcação específica de provedor para forçar cache.
- Medir/observar cache hit no caminho de resumo (o `uso` continua descartado).
- Alterar limites, truncamento, parser de resposta, persistência ou o loop do chat.

## Decisions

### 1. Instruções como constante de módulo e `system_prompt` na porta

Cada caso de uso ganha uma constante de módulo (ex.: `SYSTEM_PROMPT`) com o texto enxuto atual acrescido de poucas regras da versão detalhada. `resumir` e `_tentar_llm` passam a chamar `complete([{"role": "user", "content": <conteúdo>}], system_prompt=SYSTEM_PROMPT)`. Alternativa: manter `_montar_prompt` e passar tudo no `user` — rejeitada por não estabilizar o prefixo nem separar responsabilidades.

### 2. Adaptar o texto enxuto, não adotar o verboso

Mantém-se a redação atual e incorporam-se apenas regras de baixo custo e alto valor: vetar markdown/listas/comentários, delimitar a saída (`CURTO:`/`LONGO:`, `GUIDANCE:`…`PERIODO:`), exigir fidelidade ao conteúdo e, no guidance, saída vazia quando `NAO`, valor único replicado em mínimo/máximo e ponto decimal sem símbolo de moeda. Regras redundantes com o código (documento vazio, truncamento) ficam de fora.

### 3. Remover o trailer `Documento:`/`Trecho:`

Com o texto no `user`, o rótulo deixa de ser necessário; o prefixo de sistema já referencia "a seguir" / "um trecho". Alternativa: manter o trailer — rejeitada por poluir a mensagem variável sem ganho.

### 4. Cache é efeito oportunista, não requisito

O split é condição necessária para cache de prefixo, mas o prefixo enxuto pode ficar abaixo do mínimo de cache automático de alguns provedores. Não se adiciona `cache_control` nem se infla o texto só para atingir limiar; o ganho garantido é legibilidade/manutenabilidade.

### 5. Orçamento de caracteres compatível com o XYZ

Elevar os tetos de salvaguarda do resumo (curto 280 → 450, longo 1500 → 2000) e declarar no prompt um orçamento logo abaixo deles (curto 400, longo 1.800), instruindo a planejar X, Y e Z dentro do orçamento sem omitir a conclusão (Z). Alternativa: manter os tetos antigos e pedir o XYZ sem conclusão explícita — rejeitada por contrariar a spec (XYZ nos dois resumos) e por continuar cortando conteúdo. Verificação empírica no RG `1348111.pdf` (RZTR11): com os tetos antigos, o longo produzia 1500–1808 caracteres e o truncamento em fronteira descartava o fecho `Conclui-se…`; com os novos valores, o conteúdo cabe e a conclusão é preservada.

## Risks / Trade-offs

- [Prefixo curto pode não disparar cache no provedor] → aceito; cache tratado como oportunista. Se virar meta, exige `cache_control`/provedor com limiar menor, em change própria.
- [Acrescentar regras ao prompt muda o comportamento do modelo] → regras são conservadoras e alinhadas ao parser tolerante existente; os testes verificam a presença das instruções.
- [Testes que hoje leem `messages[0]["content"]` quebram] → ajustar os helpers para ler `system_prompt` e a mensagem `user` separadamente.
- [Guidance com prefixo constante mas fontes variadas] → desejado: o prefixo permanece idêntico e só o trecho muda, permitindo cache entre fontes.
- [Resumos persistidos antes da mudança continuam com o tamanho antigo] → a regeneração só ocorre para resumos truncados (sem pontuação final); resumos íntegros antigos não são refeitos automaticamente. Aceito: o cache se renova ao regenerar itens.
- [Resumos mais longos aumentam o contexto consumido pelo chat] → teto de 2000 caracteres é modesto frente ao orçamento de navegação por turno; sem impacto relevante nas cotas.

## Migration Plan

Sem migração de dados. Rollback: reintroduzir o texto no `user` e remover o `system_prompt`, revertendo o refactor.

## Open Questions

Nenhuma pendente.
