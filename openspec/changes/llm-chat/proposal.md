## Why

O FlowScope extrai dados da B3 mas não permite consultar esses dados em linguagem natural. Com `structured-earnings` e `informe-mensal` fornecendo documentos estruturados (proventos, informes mensais) e a futura extração de documentos relevantes em PDF, o próximo passo é permitir que o usuário faça perguntas sobre qualquer ticker e receba respostas baseadas nos documentos indexados — um assistente RAG integrado à GUI, com pesquisa semântica via SQLite local e LLM via API.

## What Changes

- Novo módulo `domain/chat/` com `ChatMessage`, `ChatSession` (in-memory) e protocolo `DocumentoIndexavel` (implementado por `DocumentoProvento.to_text()` e `InformeMensal.to_text()`)
- VectorStore em SQLite puro com busca por cosine similarity — zero dependências nativas adicionais para armazenamento
- Módulo de embeddings com dois provedores: `fastembed` (local, default) e liteLLM (API, configurável)
- Módulo de chat LLM via liteLLM com suporte a OpenAI, Claude, Gemini, DeepSeek, Copilot e OpenAI-compatible
- Pipeline de indexação: `DocumentSource` (ABC) com 3 implementações concretas — `ProventosSource`, `InformeMensalSource`, `RelevantesSource` — alimentando o VectorStore via `IndexarDocumentosUseCase`
- Chunker de texto em Python puro (split por parágrafo, overlap configurável, sem langchain)
- Widget `ChatPanel` tkinter reutilizável com scroll, copy/paste livre e envio de perguntas
- Duas abas de chat na GUI: "Chat Geral" (busca global, sem filtro de ticker) e "Chat Ticker" (busca filtrada por `WHERE ticker = ?`)
- Diálogo de configuração de provedores LLM com presets
- Abas de chat desabilitadas quando `chat.provider` não está configurado
- Dependências opcionais `[llm]` em `pyproject.toml`: `litellm`, `fastembed`, `PyPDF2`
- Testes com marcador `pytest.mark.llm`
- README com instrução `pip install flowscope[llm]`
- CLI: `--index <TICKER>` para pré-indexar documentos

## Capabilities

### New Capabilities

- `llm-chat-domain`: `ChatMessage`, `ChatSession`, protocolo `DocumentoIndexavel`, ABC `DocumentSource`
- `llm-chat-vector-store`: VectorStore SQLite puro, busca cosine, chunker sem deps nativas
- `llm-chat-embeddings`: `FastembedAdapter` (local) + `LiteLLMEmbeddingAdapter` (API), `EmbeddingPort`
- `llm-chat-llm`: `LiteLLMChatAdapter`, `ChatPort`, prompt RAG
- `llm-chat-indexing`: 3 `DocumentSource` concretos, `IndexarDocumentosUseCase`, `ConsultarDocumentosUseCase`
- `llm-chat-gui`: `ChatPanel` widget, `ConfigDialog`, abas Chat Geral + Chat Ticker
- `llm-chat-config`: Persistência em `config.json`, detecção `[llm]`, presets

### Modified Capabilities

- `cli-interface`: Novo argumento `--index <TICKER>` com `--data-inicio` e `--data-fim`

## Impact

- **Dependências**: Grupo opcional `[llm]` com `litellm`, `fastembed`, `PyPDF2`
- **Pré-requisitos**: `structured-earnings` e `informe-mensal` implementadas
- **Binário**: ~45MB base; ~185MB com `[llm]`
- **Cache**: `~/.flowscope/fii_docs.db` + PDFs em `~/.cache/flowscope/pdfs/`
- **Ticker-agnóstico**: Qualquer ticker pode ser indexado e consultado; fontes retornam vazio quando não há dados
