## Context

Ver `proposal.md` — Why. Hoje `application/resumo_documento.py` corta `curto[:280]` e `longo[:1500]` de forma bruta (corte no meio da palavra, confirmado em cache: `curto` termina em "…rendimentos; co", `longo` em "…aquisições, com"). O `texto` de documento é devolvido inteiro truncado em `TETO_DOCUMENTO = 12000` (`application/chat/documentos.py`), e a operação `obter` não tem paginação (`application/chat/protocolo.py`). O chat consome esses valores diretamente, então o modelo recebe dados incompletos. A change `chat-navegacao-granular` (pendente) adiciona índice/folhas de documento e foco; esta change mexe apenas no conteúdo (resumos e texto).

## Goals / Non-Goals

**Goals:**
- Resumos sem corte no meio da palavra, com o prompt pedindo frases/parágrafos.
- Poder regerar os resumos já truncados sem limpeza manual.
- Leitura paginada do texto integral para documentos longos.

**Non-Goals:**
- Não alterar o formato de persistência de resumos/texto nem as raízes de cache.
- Não implementar busca semântica.
- Não mudar a árvore de documentos além da leitura paginada.

## Decisions

### 1. Truncamento em fronteira, com os tetos mantidos

Novo helper corta no último fim de frase (`. `, `; `, `! `, `? `) até o teto e, na falta, no último espaço; só corta duro se não houver fronteira. Os tetos de 280/1500 caracteres são mantidos como salvaguarda. Alternativa: aumentar os tetos — rejeitada por inflar o contexto sem resolver o corte no meio da palavra.

### 2. Prompt por frases, não por contagem de caracteres

O prompt passa a pedir o curto em 1–2 frases e o longo em parágrafos. Motivo: LLMs não contam caracteres com precisão e estouravam o teto, forçando o corte bruto. Alternativa: pedir "até N caracteres" — rejeitada porque foi a causa do problema.

### 3. Regeneração por detecção de truncamento

O lote "Resumir pendentes" passa a considerar desatualizado o resumo persistido que não termina em pontuação final (`.`, `!`, `?`, `;`, `:`, `…`) após normalizar espaços, e o refaz. Resumos íntegros não são refeitos. Alternativa: apagar todos os resumos e reprocessar — rejeitada pelo custo de LLM.

### 4. Paginação na operação `obter`

`obter(caminho, offset, limite)` opcional para nós de content pesado. O nó `texto` guarda o texto completo (não truncado na construção) e devolve a página; o resultado sinaliza `total`, `offset`, `limite` e `continua`. O limite padrão por página substitui o `TETO_DOCUMENTO` fixo. Alternativa: dividir o texto em nós por seção — mais complexo e dependente do formato do PDF.

### 5. Orientação de paginação no manifesto/playbook

Adicionar uma regra: "para textos longos, leia em páginas sucessivas via `obter` com `offset`/`limite` até `continua` ser falso". Alternativa: deixar implícito — rejeitada porque o modelo precisa saber que a paginação existe.

## Risks / Trade-offs

- **[Risco] Paginação muda o contrato de `obter`** → campos opcionais preservam o uso atual; o resultado ganha metadados de página de forma determinística.
- **[Risco] Regeração consome LLM** → só resumos truncados são refeitos; a detecção é determinística.
- **[Trade-off] Texto completo do documento fica em memória no nó** → lido do cache uma vez por ticker, como hoje; a página limita o envio à LLM.
- **[Risco] Conflito com `chat-navegacao-granular`** (mesma capability `llm-chat-tree`) → arquivar aquela change antes desta.

## Migration Plan

Sem migração de dados obrigatória: os resumos truncados são regerados pelo lote quando o usuário o executar; a paginação é compatível com o uso atual. Rollback = restaurar o corte fixo e remover `offset`/`limite`.
