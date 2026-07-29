## Context

As changes `structured-earnings` e `informe-mensal` fornecem dados estruturados sobre qualquer ticker com dados na B3. Esta change adiciona consulta em linguagem natural via RAG, com VectorStore local, embeddings via fastembed, e chat LLM via API.

Três fontes de documentos alimentam o VectorStore: proventos (type=41), informes mensais (type=40) e documentos relevantes em PDF. O botão "Atualizar Documentos" indexa todas as fontes disponíveis para o ticker selecionado. Para tickers sem dados em uma fonte, essa fonte simplesmente retorna vazio.

Dependências de IA/ML são opcionais via `pip install flowscope[llm]`.

## Goals / Non-Goals

**Goals:**
- VectorStore SQLite puro com cosine similarity
- Embeddings: fastembed local default, liteLLM API alternativo
- Chat LLM via liteLLM com 5+ provedores
- Pipeline de indexação unificado para 3 fontes (DocumentSource ABC)
- Widget ChatPanel tkinter reutilizável
- ConfigDialog com presets
- CLI: `--index <TICKER>`

**Non-Goals:**
- Persistência de histórico, streaming, fine-tuning, OCR, langchain

## Decisions

### 1. SQLite puro para VectorStore

Python puro, zero deps nativas. Para ~5k chunks, cosine O(n) leva ~5-10ms.

### 2. fastembed como embedding provider default

~120MB vs ~1.5GB do sentence-transformers. ONNX runtime, modelo BGE-small-pt-v1.5 (384d).

### 3. Protocolos separados: EmbeddingPort e ChatPort

Ciclos de vida diferentes (indexação vs chat). Testáveis isoladamente.

### 4. DocumentSource ABC com 3 implementações

Cada fonte tem lógica radicalmente diferente. ABC isola, permite novas fontes sem modificar o pipeline.

### 5. ChatPanel parametrizado por ticker

Widget único `ChatPanel(ticker: str | None)`. Única diferença: filtro WHERE no VectorStore.

### 6. Config no config.json existente

Bloco `llm` no `~/.flowscope/config.json`.

### 7. Dependências opcionais + pytest.mark.llm

Binário base não cresce. CI: `-m "not llm"` + `-m "llm"`.

## Risks / Trade-offs

- **[Risco] fastembed não instala** → fallback para embedding via API no ConfigDialog
- **[Trade-off] Sem streaming** → resposta completa, sem token-a-token
- **[Trade-off] Sem persistência de sessão** → simplifica, evita preocupações com privacidade
