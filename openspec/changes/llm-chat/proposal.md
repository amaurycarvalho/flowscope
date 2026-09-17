## Why

O FlowScope extrai dados da B3 mas não permite consultar esses dados em linguagem natural. Com `structured-earnings` fornecendo proventos e os documentos estruturados/regulatórios da B3, além dos documentos em PDF (avisos de BDR e documentos relevantes) e do informe mensal em HTML, o próximo passo é permitir que o usuário faça perguntas sobre qualquer ticker e receba respostas baseadas nos documentos indexados — um assistente RAG integrado à GUI, com pesquisa semântica via SQLite local e LLM via API.

Esta change também centraliza a **preparação para indexação** (contratos `DocumentoIndexavel`/`DocumentSource`, `to_text`/extração de texto e fontes concretas), que estava dispersa nas changes de extração.

## What Changes

- Novo módulo `domain/chat/` com `ChatMessage`, `ChatSession` (in-memory) e as portas `DocumentoIndexavel` (protocolo) e `DocumentSource` (ABC).
- Fontes de documentos (`DocumentSource`) já implementadas, reconciliadas com o código: `MaterialFactsSource` (fatos relevantes/assembleias/avisos via `RegulacaoRepository`) e `NoticiasSource` (Plantão B3).
- **Transferido das changes de extração**: `InformeMensalSource` (lê o cache `~/.cache/flowscope/informe-mensal/` e produz texto do HTML) e `RelevantesSource` (lê o cache `~/.cache/flowscope/documentos-relevantes/` e extrai texto dos PDFs).
- Extração de texto para indexação (HTML→texto e PDF→texto via `pypdf`) como responsabilidade desta change.
- VectorStore em SQLite puro com busca por cosine similarity — zero dependências nativas adicionais para armazenamento.
- Módulo de embeddings com dois provedores: `fastembed` (local, default) e liteLLM (API, configurável).
- Módulo de chat LLM via liteLLM com suporte a OpenAI, Claude, Gemini, DeepSeek, Copilot e OpenAI-compatible.
- Pipeline de indexação via `IndexarDocumentosUseCase`, consumindo as `DocumentSource` disponíveis.
- Chunker de texto em Python puro (split por parágrafo, overlap configurável, sem langchain).
- Widget `ChatPanel` tkinter reutilizável com scroll, copy/paste livre e envio de perguntas.
- Duas abas de chat na GUI: "Chat Geral" (busca global) e "Chat Ticker" (busca filtrada por `WHERE ticker = ?`).
- Diálogo de configuração de provedores LLM com presets.
- Abas de chat desabilitadas quando `chat.provider` não está configurado.
- Dependências opcionais `[llm]` em `pyproject.toml`: `litellm`, `fastembed`, `pypdf`.
- Testes com marcador `pytest.mark.llm`.
- README com instrução `pip install flowscope[llm]`.
- CLI: `--index <TICKER>` para pré-indexar documentos.

## Capabilities

### New Capabilities

- `llm-chat-domain`: `ChatMessage`, `ChatSession`, protocolo `DocumentoIndexavel`, ABC `DocumentSource`
- `llm-chat-vector-store`: VectorStore SQLite puro, busca cosine, chunker sem deps nativas
- `llm-chat-embeddings`: `FastembedAdapter` (local) + `LiteLLMEmbeddingAdapter` (API), `EmbeddingPort`
- `llm-chat-llm`: `LiteLLMChatAdapter`, `ChatPort`, prompt RAG
- `llm-chat-indexing`: `DocumentSource` concretas (`MaterialFactsSource`, `NoticiasSource`, `InformeMensalSource`, `RelevantesSource`), extração de texto, `IndexarDocumentosUseCase`, `ConsultarDocumentosUseCase`
- `llm-chat-gui`: `ChatPanel` widget, `ConfigDialog`, abas Chat Geral + Chat Ticker
- `llm-chat-config`: Persistência em `config.json`, detecção `[llm]`, presets

### Modified Capabilities

- `cli-interface`: Novo argumento `--index <TICKER>` com `--data-inicio` e `--data-fim`

## Impact

- **Dependências**: Grupo opcional `[llm]` com `litellm`, `fastembed`, `pypdf`
- **Pré-requisitos**: `structured-earnings` implementada; caches de documento das changes `informe-mensal` e `documentos-relevantes` para as fontes correspondentes
- **Binário**: ~45MB base; ~185MB com `[llm]`
- **Cache**: `~/.flowscope/fii_docs.db` + leitura dos caches `~/.cache/flowscope/bdr/`, `informe-mensal/` e `documentos-relevantes/`
- **Ticker-agnóstico**: Qualquer ticker pode ser indexado e consultado; fontes retornam vazio quando não há dados
