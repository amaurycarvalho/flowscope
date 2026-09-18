## Context

As changes de extração fornecem dados e documentos sobre qualquer ticker com dados na B3: proventos e documentos estruturados, informe mensal (HTML), avisos de BDR e documentos relevantes (PDF). Esta change adiciona consulta em linguagem natural via RAG, com VectorStore local, embeddings via fastembed e chat LLM via API.

As portas `DocumentoIndexavel` e `DocumentSource` vivem em `domain/chat/ports.py`. As fontes concretas já implementadas são `MaterialFactsSource` (fatos relevantes/assembleias/avisos via `RegulacaoRepository`) e `NoticiasSource` (Plantão B3). Esta change recebe, transferidas das changes de extração, `InformeMensalSource` e `RelevantesSource`, que leem os caches de documento em disco e produzem texto para indexação.

Dependências de IA/ML são opcionais via `pip install flowscope[llm]`. A camada base de LLM (porta `LLMPort`, adaptador liteLLM, presets, rate limiting e exceções) é fornecida pela change `llm-core`; esta change a consome e concentra-se em embeddings, VectorStore, RAG e GUI de chat.

## Goals / Non-Goals

**Goals:**
- VectorStore SQLite puro com cosine similarity
- Embeddings: fastembed local default, liteLLM API alternativo
- Consumo da porta `LLMPort` da `llm-core` para o prompt RAG
- Pipeline de indexação unificado sobre `DocumentSource`
- Fontes concretas: `MaterialFactsSource`, `NoticiasSource`, `InformeMensalSource`, `RelevantesSource`
- Extração de texto para indexação (HTML→texto, PDF→texto via `pypdf`)
- Widget ChatPanel tkinter reutilizável
- Configuração de embedding persistida em `llm.embedding`
- CLI: `--index <TICKER>`

**Non-Goals:**
- Cliente de LLM, presets de completion, rate limiting e diálogo de configuração (propriedade da `llm-core`)
- Persistência de histórico, streaming, fine-tuning, OCR, langchain
- Aquisição/download dos documentos (pertence às changes de extração)

## Decisions

### 1. SQLite puro para VectorStore

Python puro, zero deps nativas. Para ~5k chunks, cosine O(n) leva ~5-10ms.

### 2. fastembed como embedding provider default

~120MB vs ~1.5GB do sentence-transformers. ONNX runtime, modelo BGE-small-pt-v1.5 (384d).

### 3. EmbeddingPort próprio e LLMPort herdado da llm-core

Embedding e completion têm ciclos de vida diferentes (indexação vs chat) e são testáveis isoladamente. Esta change define apenas o `EmbeddingPort`; a porta de completion (`LLMPort`) e a factory vêm da `llm-core`.

### 4. `DocumentSource` ABC e fontes concretas

`DocumentSource` (em `domain/chat/ports.py`) expõe `categoria` e `obter_documentos(ticker)`. Cada fonte tem lógica radicalmente diferente e isola o pipeline, permitindo novas fontes sem modificá-lo.

- **Já implementadas**: `MaterialFactsSource`, `NoticiasSource`.
- **Transferidas**: `InformeMensalSource` (lê `~/.cache/flowscope/informe-mensal/<TICKER>/...` e converte o HTML em texto) e `RelevantesSource` (lê `~/.cache/flowscope/documentos-relevantes/<TICKER>/.../<cat>/<id>.pdf` e extrai texto com `pypdf`).

A extração de texto para indexação pertence a esta change; a aquisição/cache permanece nas changes de extração.

### 5. ChatPanel parametrizado por ticker

Widget único `ChatPanel(ticker: str | None)`. Única diferença: filtro WHERE no VectorStore.

### 6. Config no config.json existente

A `llm-core` persiste a configuração de completion em `llm.chat`. Esta change persiste a configuração de embedding no sub-bloco `llm.embedding` do mesmo `~/.flowscope/config.json`, reutilizando o read-modify-write da `llm-core` para preservar as demais chaves.

### 7. Dependências opcionais + pytest.mark.llm

A `llm-core` define `[llm]` com `litellm`; esta change estende o grupo com `fastembed` (`pypdf` já é dependência base). Binário base não cresce. CI: `-m "not llm"` + `-m "llm"`.

### 8. Herança da camada de LLM da `llm-core`

Esta change NÃO define `ChatPort`, `LiteLLMChatAdapter`, factory de chat, presets de completion nem `ConfigDialog`. Ela consome `LLMPort`, `create_llm_provider`, `load_llm_config` e as exceções tipadas da `llm-core`, adicionando apenas o prompt RAG e a orquestração do `ConsultarDocumentosUseCase`. O botão "Configurar" do ChatPanel abre o diálogo da `llm-core`.

## Risks / Trade-offs

- **[Risco] fastembed não instala** → fallback para embedding via API, configurável no diálogo da `llm-core`
- **[Risco] PDFs sem texto extraível** → a fonte retorna apenas metadados/vazio, sem interromper a indexação
- **[Trade-off] Sem streaming** → resposta completa, sem token-a-token
- **[Trade-off] Sem persistência de sessão** → simplifica, evita preocupações com privacidade

## Migration Plan

1. Confirmar que a change `llm-core` está implementada (`LLMPort`, `create_llm_provider`, `load_llm_config`, `check_llm_deps`, exceções tipadas).
2. Reconciliar as portas e fontes já implementadas (`DocumentSource`, `DocumentoIndexavel`, `MaterialFactsSource`, `NoticiasSource`).
3. Implementar `InformeMensalSource` e `RelevantesSource` sobre os caches em disco.
4. Implementar VectorStore, embeddings, RAG, GUI de chat e CLI, consumindo a `llm-core`.
5. Rollback: as mudanças são aditivas e opcionais via `[llm]`.
