## 1. Pré-requisitos e Setup

- [ ] 1.1 Verificar que `structured-earnings` está implementada (B3FundosClient, ticker-resolution, value objects, DocumentoProvento, ProventosRepository)
- [ ] 1.2 Verificar que `informe-mensal` está implementada (InformeMensal, InformeMensalRepository, multi-table parser)
- [ ] 1.3 Adicionar grupo `[llm]` ao `pyproject.toml` com `litellm>=1.50`, `fastembed>=0.4`, `PyPDF2>=3.0`
- [ ] 1.4 Marcador pytest `llm` em `pyproject.toml`
- [ ] 1.5 Criar estrutura de diretórios completa
- [ ] 1.6 Atualizar README.md com seção "Chat com IA" e `pip install flowscope[llm]`

## 2. Domínio — Chat Models e Ports

- [ ] 2.1 `ChatMessage`, `ChatSession` em `domain/chat/models.py`
- [ ] 2.2 `DocumentoIndexavel` protocol, `DocumentSource` ABC, `DocumentoMeta` em `domain/chat/ports.py`
- [ ] 2.3 Criar `domain/chat/__init__.py`

## 3. Domínio — to_text() nas Entidades (deltas)

- [ ] 3.1 `DocumentoProvento.to_text()` — texto denso para embedding
- [ ] 3.2 `InformeMensal.to_text()` — texto denso para embedding

## 4. Testes do Domínio

- [ ] 4.1 Testar `ChatMessage`, `ChatSession`
- [ ] 4.2 Testar `to_text()` em ambas as entidades

## 5. Infraestrutura — VectorStore

- [ ] 5.1 `VectorStore` em `infrastructure/vector_store/store.py` — SQLite, tabela, índices
- [ ] 5.2 `add(chunks)` com INSERT OR IGNORE
- [ ] 5.3 `search(query_embedding, ticker?, k)` — cosine similarity Python puro
- [ ] 5.4 `chunk_text()` em `infrastructure/vector_store/chunker.py`

## 6. Infraestrutura — Embeddings

- [ ] 6.1 `EmbeddingPort` protocol
- [ ] 6.2 `FastembedAdapter` — lazy loading, batch, ImportError handling
- [ ] 6.3 `LiteLLMEmbeddingAdapter` — API, erro HTTP
- [ ] 6.4 `create_embedding_provider(config)` factory

## 7. Infraestrutura — Chat LLM

- [ ] 7.1 `ChatPort` protocol
- [ ] 7.2 `LiteLLMChatAdapter` — `chat()`, base_url custom
- [ ] 7.3 `build_rag_prompt()`
- [ ] 7.4 `create_chat_provider(config)` factory

## 8. Infraestrutura — Document Sources

- [ ] 8.1 `listar_documentos_relevantes()` no `B3FundosClient`
- [ ] 8.2 `ProventosSource` — usa `ProventosRepository`, retorna vazio se ticker sem resolução
- [ ] 8.3 `InformeMensalSource` — usa `InformeMensalRepository`, retorna vazio se ticker sem resolução
- [ ] 8.4 `RelevantesSource` — PDF download, PyPDF2, cache

## 9. Aplicação — Use Cases

- [ ] 9.1 `IndexarDocumentosUseCase` — 3 sources, VectorStore, EmbeddingPort, progress
- [ ] 9.2 `ConsultarDocumentosUseCase` — embed → search → prompt → chat → resposta + fontes
- [ ] 9.3 Erro em uma fonte não interrompe as outras

## 10. Testes Infraestrutura

- [ ] 10.1 VectorStore: criar, inserir, buscar, deduplicar
- [ ] 10.2 Embedding adapters com mocks
- [ ] 10.3 Chat adapter com mock
- [ ] 10.4 Document sources com mocks
- [ ] 10.5 Use cases com mocks — fluxo completo, fonte falhando, VectorStore vazio

## 11. Config — LLM Config

- [ ] 11.1 `load_llm_config()`, `save_llm_config()`, `get_presets()`, `check_llm_deps()`

## 12. GUI — ChatPanel

- [ ] 12.1 `ChatPanel(tkinter.Frame)` — mensagens, scroll, entrada, enviar
- [ ] 12.2 Estado não configurado, estado sem documentos
- [ ] 12.3 Copy/paste livre, scroll automático
- [ ] 12.4 Barra de progresso "Atualizar Documentos"

## 13. GUI — ConfigDialog

- [ ] 13.1 `ConfigDialog(tkinter.Toplevel)` — presets, API key, testar conexão

## 14. GUI — Integração

- [ ] 14.1 Aba "Chat Geral" com `ChatPanel(ticker=None)`
- [ ] 14.2 Aba "Chat Ticker" com `ChatPanel(ticker=<selecionado>)`
- [ ] 14.3 Visibilidade condicionada a `chat.provider`

## 15. CLI

- [ ] 15.1 `--index <TICKER>` com `--data-inicio`, `--data-fim`
- [ ] 15.2 `run_index(args)`, verificação de deps, dispatch

## 16. Testes GUI

- [ ] 16.1 ChatPanel estados, ConfigDialog presets, load_llm_config

## 17. Quality Gate

- [ ] 17.1 `make lint` limpo
- [ ] 17.2 `pytest -m "not llm"` + `pytest -m "llm"` passam
- [ ] 17.3 Testes existentes sem regressão
