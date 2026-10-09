## Context

Ver `proposal.md` — Why. A árvore de conhecimento é montada por `application/chat/montar.py` a partir de fontes (`FonteConhecimento`, `FonteFundamentos`, `FonteDocumentos`, `FonteNoticias`, e as novas de `documentos-arvore-ramos`). `application/chat/arvore.py` constrói os ramos `/flowscope` e `/fundamentos` e mantém a invariante "nó sem filhos = folha". O manifesto (`application/chat/manifesto.py`) descreve o mapa canônico como constante e o protocolo de navegação; o prefixo de sistema combina `SYSTEM_PROMPT` + `INSTRUCAO_FORMATO` + manifesto (`application/chat/consultar.py`).

## Goals / Non-Goals

**Goals:**
- Garantir que a árvore nunca exponha nós internos vazios como folhas.
- Fazer o manifesto anunciar apenas ramos existentes.
- Orientar a LLM a usar a busca determinística (`buscar`) quando a semântica não estiver disponível e a não listar grupos grandes inteiros.

**Non-Goals:**
- Não prover índice vetorial nem alterar o `buscar_semantico`.
- Não impor teto ao `listar` (opção não escolhida).
- Não alterar os ramos de documentos/notícias/guidance nem o formato de cache.

## Decisions

### 1. Omitir ramos internos vazios na montagem, não relaxar o invariante

`ramo_flowscope` só anexa `/flowscope/abas` e `/flowscope/indicadores` quando têm itens; `ramo_fundamentos` só anexa `/fundamentos/tickers|campos|valores` quando preenchidos. Alternativa: marcar nós internos vazios com um flag `interno` e permitir `listar` devolver `[]`. Rejeitada: muda o invariante, o protocolo, `contar` e o índice, com impacto amplo para um ganho que a omissão já resolve.

### 2. Mapa e descrição do manifesto dinâmicos

`_mapa_arvore(arvore)` e `_descricao(arvore)` consultam `arvore.existe(...)` e só citam ramos presentes; `_caminhos_flowscope`/`_caminhos_fundamentos` detalham os sub-ramos existentes. Alternativa: manter `MAPA_ARVORE` constante. Rejeitada: anunciava `/flowscope/indicadores/<indicador>` e outros caminhos inexistentes, induzindo `nao_interno`/`caminho_invalido`.

### 3. Orientação de fallback no prefixo (manifesto + prompt)

O texto de `PROTOCOLO` (prefixo cacheável) e o `SYSTEM_PROMPT` passam a afirmar que, ao receber `indice_indisponivel`, a LLM deve usar `buscar(caminho, regex, em=[...])`, e que em ramos grandes deve preferir o nó `indice`/`buscar` a `listar`. Alternativa: confiar apenas na dica de runtime do `buscar_semantico`. Rejeitada: já existia e a LLM a ignorou, listando `/noticias/Geral` inteiro.

## Risks / Trade-offs

- **[Risco] Omissão de ramos pode surpreender consumidores que assumiam `/flowscope/indicadores` sempre presente** → o mapa dinâmico deixa de anunciá-lo; `existe` responde falso de forma consistente e o ramo reaparece sozinho quando passar a ter itens.
- **[Risco] Orientações de prompt não são garantidas** → mitigado pelo teto de 50 resultados do `buscar`, pela dica estruturada de `buscar_semantico` e por testes que verificam o texto do manifesto/prompt.
- **[Trade-off] O manifesto passa a variar com a composição de ramos** → é determinístico para a mesma árvore; a assinatura de estado continua derivada de arquivos/watchlist.

## Migration Plan

Sem migração de dados e sem persistência nova. Rollback = reverter a omissão dos ramos vazios, o mapa dinâmico e os textos de orientação.
