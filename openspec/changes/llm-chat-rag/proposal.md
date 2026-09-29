## Why

A `llm-chat` responde a partir dos resumos e do texto já cacheados, com uma cascata lexical e sem embeddings. Isso atende perguntas diretas, mas não escala para busca semântica sobre grandes volumes de documentos. Esta change adiciona a recuperação vetorial como evolução dependente da `llm-chat` e da `cache-prompt-chat`, que define o prefixo estável cacheável e o sufixo volátil do prompt.

## What Changes

- VectorStore em SQLite puro, com busca top-k por cosine similarity e filtro opcional por ticker.
- Módulo de embeddings com dois provedores: `fastembed` (local, default) e liteLLM (API).
- Porta `DocumentoIndexavel`/`DocumentSource` e fontes concretas, com extração de texto (HTML e PDF).
- Pipeline de indexação (`IndexarDocumentosUseCase`) e consulta RAG (`ConsultarDocumentosUseCase`) consumindo a porta `LLMPort` da `llm-core`.
- Integração da consulta RAG à aba "Chat AI" como fonte adicional **volátil** (depende da pergunta), pelo ponto de extensão da `llm-chat`: pela `cache-prompt-chat`, ela DEVE compor o **sufixo** do prompt, nunca o prefixo estável cacheável nem a assinatura do contexto estável.
- Chunker de texto em Python puro.
- Configuração de embedding persistida em `llm.embedding` e presets de provedores de embedding.
- Dependência opcional `fastembed` no grupo `[llm]`.
- CLI `--index <TICKER>` com `--data-inicio` e `--data-fim`.

## Capabilities

### New Capabilities

- `llm-chat-rag-vector-store`: VectorStore SQLite puro, busca por cosine similarity e chunker.
- `llm-chat-rag-embeddings`: `EmbeddingPort`, adaptadores `fastembed` e liteLLM e factory.
- `llm-chat-rag-indexing`: portas `DocumentoIndexavel`/`DocumentSource`, fontes concretas, extração de texto, indexação e consulta RAG, com a fonte vetorial volátil no sufixo do prompt.
- `llm-chat-rag-config`: persistência de `llm.embedding`, detecção estendida de `[llm]` e presets de embedding.
- `llm-chat-rag-cli`: argumento `--index` no CLI.

### Modified Capabilities

<!-- Nenhuma: a regra de prefixo estável/sufixo volátil é adicionada pela `cache-prompt-chat`; esta change apenas a respeita e a referencia. -->

## Impact

- **Depende de**: `llm-chat` implementada (infraestrutura de caches e contexto), `llm-core` (porta `LLMPort`) e **`cache-prompt-chat`** (prefixo estável cacheável + sufixo volátil). Depende, transitivamente, de `background-job-manager`, `carga-principal-background`, `leituras-catalogo-background` e `reduzir-testes-ui`.
- **Dependências**: estende o grupo `[llm]` da `llm-core` (`litellm`) com `fastembed`; `pypdf` já é dependência base.
- **Cache**: `~/.flowscope/fii_docs.db` e leitura dos caches de documentos.
- **Binário**: ~45MB base; ~185MB com `[llm]`.
- **Ticker-agnóstico**: qualquer ticker pode ser indexado e consultado; fontes retornam vazio quando não há dados.
