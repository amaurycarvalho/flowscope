## Context

As changes de extração fornecem dados e documentos sobre qualquer ticker com dados na B3: proventos e documentos estruturados, informe mensal (HTML), avisos de BDR e documentos relevantes (PDF). Esta change adiciona consulta em linguagem natural via RAG, com VectorStore local, embeddings via fastembed e chat LLM via API.

As portas `DocumentoIndexavel` e `DocumentSource` vivem em `domain/chat/ports.py`. As fontes concretas já implementadas são `MaterialFactsSource` (fatos relevantes/assembleias/avisos via `RegulacaoRepository`) e `NoticiasSource` (Plantão B3). Esta change recebe, transferidas das changes de extração, `InformeMensalSource` e `RelevantesSource`, que leem os caches de documento em disco e produzem texto para indexação.

Dependências de IA/ML são opcionais via `pip install flowscope[llm]`.

## Goals / Non-Goals

**Goals:**
- VectorStore SQLite puro com cosine similarity
- Embeddings: fastembed local default, liteLLM API alternativo
- Chat LLM via liteLLM com 5+ provedores
- Pipeline de indexação unificado sobre `DocumentSource`
- Fontes concretas: `MaterialFactsSource`, `NoticiasSource`, `InformeMensalSource`, `RelevantesSource`
- Extração de texto para indexação (HTML→texto, PDF→texto via `pypdf`)
- Widget ChatPanel tkinter reutilizável
- ConfigDialog com presets
- CLI: `--index <TICKER>`

**Non-Goals:**
- Persistência de histórico, streaming, fine-tuning, OCR, langchain
- Aquisição/download dos documentos (pertence às changes de extração)

## Decisions

### 1. SQLite puro para VectorStore

Python puro, zero deps nativas. Para ~5k chunks, cosine O(n) leva ~5-10ms.

### 2. fastembed como embedding provider default

~120MB vs ~1.5GB do sentence-transformers. ONNX runtime, modelo BGE-small-pt-v1.5 (384d).

### 3. Protocolos separados: EmbeddingPort e ChatPort

Ciclos de vida diferentes (indexação vs chat). Testáveis isoladamente.

### 4. `DocumentSource` ABC e fontes concretas

`DocumentSource` (em `domain/chat/ports.py`) expõe `categoria` e `obter_documentos(ticker)`. Cada fonte tem lógica radicalmente diferente e isola o pipeline, permitindo novas fontes sem modificá-lo.

- **Já implementadas**: `MaterialFactsSource`, `NoticiasSource`.
- **Transferidas**: `InformeMensalSource` (lê `~/.cache/flowscope/informe-mensal/<TICKER>/...` e converte o HTML em texto) e `RelevantesSource` (lê `~/.cache/flowscope/documentos-relevantes/<TICKER>/.../<cat>/<id>.pdf` e extrai texto com `pypdf`).

A extração de texto para indexação pertence a esta change; a aquisição/cache permanece nas changes de extração.

### 5. ChatPanel parametrizado por ticker

Widget único `ChatPanel(ticker: str | None)`. Única diferença: filtro WHERE no VectorStore.

### 6. Config no config.json existente

Bloco `llm` no `~/.flowscope/config.json`.

### 7. Dependências opcionais + pytest.mark.llm

Binário base não cresce. CI: `-m "not llm"` + `-m "llm"`.

## Risks / Trade-offs

- **[Risco] fastembed não instala** → fallback para embedding via API no ConfigDialog
- **[Risco] PDFs sem texto extraível** → a fonte retorna apenas metadados/vazio, sem interromper a indexação
- **[Trade-off] Sem streaming** → resposta completa, sem token-a-token
- **[Trade-off] Sem persistência de sessão** → simplifica, evita preocupações com privacidade

## Migration Plan

1. Reconciliar as portas e fontes já implementadas (`DocumentSource`, `DocumentoIndexavel`, `MaterialFactsSource`, `NoticiasSource`).
2. Implementar `InformeMensalSource` e `RelevantesSource` sobre os caches em disco.
3. Implementar VectorStore, embeddings, chat, GUI, config e CLI.
4. Rollback: as mudanças são aditivas e opcionais via `[llm]`.
