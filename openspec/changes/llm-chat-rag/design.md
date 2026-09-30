## Context

Ver `proposal.md` — Why. A change `llm-chat` fornece o chat não vetorial e a `llm-core` fornece a porta `LLMPort`. Esta change adiciona a recuperação vetorial como evolução, absorvendo o escopo vetorial que antes constava da `llm-chat` (VectorStore, embeddings, chunker, indexação, config de embedding e `--index`).

As portas `DocumentoIndexavel` e `DocumentSource` vivem em `domain/chat/ports.py` e já existem as fontes `MaterialFactsSource` e `NoticiasSource`.

Esta change **depende de** `chat-arvore-navegavel`: o chat passa a expor o estado local como árvore navegável, com manifesto estável como prefixo cacheável e a operação `buscar_semantico` no protocolo. A recuperação vetorial é o backend dessa operação e NÃO altera o manifesto nem a assinatura do estado.

## Goals / Non-Goals

**Goals:**
- VectorStore SQLite puro com cosine similarity.
- Embeddings: fastembed local (default) e liteLLM (API).
- Pipeline de indexação unificado sobre `DocumentSource` e consulta RAG consumindo `LLMPort`.
- Extração de texto (HTML→texto, PDF→`pypdf`) e chunker sem `langchain`.
- Configuração de embedding em `llm.embedding` e CLI `--index`.
- Backend vetorial da operação `buscar_semantico`, opcional e sem afetar o manifesto da árvore.

**Non-Goals:**
- Chat, aba de chat, árvore de conhecimento e protocolo de navegação (propriedade da `llm-chat` e da `chat-arvore-navegavel`).
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

### 7. Integração com o Chat AI como backend de `buscar_semantico`

A consulta RAG é oferecida à aba "Chat AI" como **backend da operação `buscar_semantico`** do protocolo da árvore (`chat-arvore-navegavel`), que é o ponto de extensão do chat. A operação existe na árvore independentemente desta change: sem backend, retorna `indice_indisponivel` e o chat segue na navegação lexical. A indexação permanece manual (CLI `--index`). A presença ou ausência do backend NÃO altera o manifesto nem a assinatura do estado.

Alternativa considerada: oferecer a consulta como fonte adicional volátil no sufixo do prompt (desenho anterior, dependente da `cache-prompt-chat`) — descartada porque a `chat-arvore-navegavel` substitui a cascata e expõe a recuperação como operação do protocolo.

Alternativa considerada: substituir a cascata de documentos pela busca vetorial — descartada por tornar o RAG obrigatório e quebrar o fallback quando não há índice.

## Risks / Trade-offs

- **[Risco] fastembed não instala** → fallback para embedding via API, configurável no diálogo.
- **[Risco] PDFs sem texto extraível** → a fonte retorna metadados/vazio sem interromper a indexação.
- **[Risco] Busca O(n)** → aceitável para o volume atual; reavaliar se o número de chunks crescer muito.
- **[Risco] Backend vetorial alterar o manifesto/invalidar o cache a cada turno** → **Mitigação**: o backend implementa apenas a operação `buscar_semantico`; teste garante que o manifesto e a assinatura da árvore permanecem byte-a-byte idênticos com e sem backend.
- **[Trade-off] Indexação manual** → o usuário dispara via GUI/CLI, sem indexação automática em background.

## Migration Plan

1. Confirmar que a `llm-chat` e a `llm-core` estão implementadas.
2. Confirmar que a `chat-arvore-navegavel` está implementada (árvore + operação `buscar_semantico`).
3. Reconciliar as portas e fontes já existentes, registrando o backend vetorial na operação `buscar_semantico`, sem tocar o manifesto.
4. Implementar VectorStore, embeddings, extração, indexação e consulta RAG.
5. Expor a configuração de embedding e o CLI `--index`.
6. Rollback: mudanças aditivas e opcionais via `[llm]`.

## Open Questions

- O diálogo de configuração da `llm-core` deve ganhar uma seção de embedding ou a configuração de embedding fica em um diálogo próprio? (resolvível durante a implementação, sem alterar specs)
