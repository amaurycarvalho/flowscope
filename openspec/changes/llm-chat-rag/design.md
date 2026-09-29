## Context

Ver `proposal.md` — Why. A change `llm-chat` fornece o chat não vetorial e a `llm-core` fornece a porta `LLMPort`. Esta change adiciona a recuperação vetorial como evolução, absorvendo o escopo vetorial que antes constava da `llm-chat` (VectorStore, embeddings, chunker, indexação, config de embedding e `--index`).

As portas `DocumentoIndexavel` e `DocumentSource` vivem em `domain/chat/ports.py` e já existem as fontes `MaterialFactsSource` e `NoticiasSource`.

Esta change **depende de** `cache-prompt-chat`: o prompt do chat passa a ter um **prefixo estável cacheável** (instruções + contexto: conhecimento, fundamentos e resumos) e um **sufixo volátil** (fontes por pergunta + pergunta). A recuperação vetorial depende da pergunta, portanto entra no sufixo e NÃO pode compor o prefixo nem a assinatura do contexto estável.

## Goals / Non-Goals

**Goals:**
- VectorStore SQLite puro com cosine similarity.
- Embeddings: fastembed local (default) e liteLLM (API).
- Pipeline de indexação unificado sobre `DocumentSource` e consulta RAG consumindo `LLMPort`.
- Extração de texto (HTML→texto, PDF→`pypdf`) e chunker sem `langchain`.
- Configuração de embedding em `llm.embedding` e CLI `--index`.
- Fonte vetorial posicionada no sufixo volátil, sem afetar o prefixo estável cacheável.

**Non-Goals:**
- Chat, aba de chat e montagem de contexto (propriedade da `llm-chat`; o layout prefixo/sufixo é da `cache-prompt-chat`).
- Cliente de LLM, presets de completion e diálogo de configuração (propriedade da `llm-core`).
- Aquisição/download dos documentos (changes de extração e `noticias-b3`).

## Decisions

### 1. SQLite puro para VectorStore

Python puro, zero dependências nativas. Para ~5k chunks, a busca cosine O(n) leva ~5-10ms, suficiente para o volume esperado.

Alternativa considerada: banco vetorial dedicado (ex.: `sqlite-vec`, Chroma) — descartado por adicionar dependências nativas e complexidade de empacotamento.

### 2. fastembed como provider default de embedding

~120MB contra ~1.5GB do `sentence-transformers`. ONNX runtime com o modelo `BAAI/bge-small-pt-v1.5` (384 dimensões, português).

Alternativa considerada: embeddings apenas via API — descartado como default por exigir rede e chave a cada indexação.

### 3. EmbeddingPort próprio e LLMPort herdado da llm-core

Embedding e completion têm ciclos de vida diferentes (indexação em lote vs. chat interativo) e são testáveis isoladamente. Esta change define apenas o `EmbeddingPort`; a porta de completion vem da `llm-core`.

### 4. DocumentSource ABC e fontes concretas

Cada fonte tem lógica radicalmente diferente e isola o pipeline, permitindo novas fontes sem modificá-lo. As fontes cobrem material facts (via `RegulacaoRepository`), notícias do Plantão B3 e os documentos em cache (documentos relevantes, informe mensal, BDR), reutilizando a extração de texto.

### 5. Config no config.json existente

A configuração de embedding ocupa o sub-bloco `llm.embedding` do `~/.flowscope/config.json`, com read-modify-write preservando as demais chaves (incluindo `llm.chat` da `llm-core`).

### 6. Dependências opcionais

A `llm-core` define `[llm]` com `litellm`; esta change estende com `fastembed` (`pypdf` já é base). O binário base não cresce.

### 7. Integração com o Chat AI via fonte adicional volátil

A consulta RAG é oferecida à aba "Chat AI" como fonte adicional de contexto, pelo ponto de extensão da `llm-chat`, recebendo a pergunta para a recuperação semântica. Por **depender da pergunta**, ela é **volátil**: pela `cache-prompt-chat`, entra no **sufixo** do prompt e NÃO compõe o prefixo estável cacheável nem a assinatura do contexto estável. A indexação permanece manual (CLI `--index` da `llm-chat-rag`). Sem documentos indexados, a fonte retorna vazio e o chat segue com a cascata lexical.

Alternativa considerada: substituir a cascata de documentos pela busca vetorial — descartada por tornar o RAG obrigatório e quebrar o fallback quando não há índice.

## Risks / Trade-offs

- **[Risco] fastembed não instala** → fallback para embedding via API, configurável no diálogo.
- **[Risco] PDFs sem texto extraível** → a fonte retorna metadados/vazio sem interromper a indexação.
- **[Risco] Busca O(n)** → aceitável para o volume atual; reavaliar se o número de chunks crescer muito.
- **[Risco] Fonte vetorial no prefixo estável invalidar o cache de prompt a cada turno** → **Mitigação**: pela `cache-prompt-chat`, a fonte RAG entra no sufixo, fora da assinatura do contexto estável; teste headless garante que o prefixo não muda com a RAG ativa.
- **[Trade-off] Indexação manual** → o usuário dispara via GUI/CLI, sem indexação automática em background.

## Migration Plan

1. Confirmar que a `llm-chat` e a `llm-core` estão implementadas.
2. Confirmar que a `cache-prompt-chat` está implementada (prefixo estável cacheável + sufixo volátil).
3. Reconciliar as portas e fontes já existentes, posicionando a fonte RAG no sufixo, fora da assinatura do contexto estável.
4. Implementar VectorStore, embeddings, extração, indexação e consulta RAG.
5. Expor a configuração de embedding e o CLI `--index`.
6. Rollback: mudanças aditivas e opcionais via `[llm]`.

## Open Questions

- O diálogo de configuração da `llm-core` deve ganhar uma seção de embedding ou a configuração de embedding fica em um diálogo próprio? (resolvível durante a implementação, sem alterar specs)
