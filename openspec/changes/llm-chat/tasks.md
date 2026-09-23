## 1. Pré-requisitos e Setup

- [ ] 1.1 Verificar que a change `llm-core` está implementada (`LLMPort`, `create_llm_provider`, `load_llm_config`, `check_llm_deps`, exceções tipadas)
- [ ] 1.2 Verificar que `structured-earnings` está implementada (B3FundosClient, ticker-resolution, value objects, DocumentoProvento, ProventosRepository)
- [ ] 1.3 Verificar que as portas `DocumentoIndexavel` e `DocumentSource` já existem em `domain/chat/ports.py`
- [ ] 1.4 Verificar que as fontes `MaterialFactsSource` e `NoticiasSource` já existem em `infrastructure/document_sources/`
- [ ] 1.5 Verificar que os caches de `informe-mensal` e `documentos-relevantes` existem e são legíveis
- [ ] 1.6 Estender o grupo `[llm]` do `pyproject.toml` com `fastembed>=0.4` (`litellm` já é adicionado pela `llm-core`; `pypdf` já é base)
- [ ] 1.7 Criar a estrutura de diretórios restante
- [ ] 1.8 Atualizar README.md com seção "Chat com IA" e `pip install flowscope[llm]`

## 2. Domínio — Chat Models e Ports (reconciliação)

- [ ] 2.1 `ChatMessage`, `ChatSession` em `domain/chat/models.py`
- [ ] 2.2 Confirmar `DocumentoIndexavel` e `DocumentSource` em `domain/chat/ports.py` (já implementados)
- [ ] 2.3 Atualizar `domain/chat/__init__.py` com os novos modelos

## 3. Extração de texto para indexação (transferido)

- [ ] 3.1 Extração de texto de HTML (informe mensal) para a `InformeMensalSource`
- [ ] 3.2 Extração de texto de PDF via `pypdf` para a `RelevantesSource`, reutilizando/generalizando o extrator existente de BDR
- [ ] 3.3 `to_text()`/representação textual densa das entidades usadas pelas fontes

## 4. Testes do Domínio

- [ ] 4.1 Testar `ChatMessage`, `ChatSession`
- [ ] 4.2 Testar a extração de texto (HTML e PDF) com fixtures

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

## 7. Infraestrutura — RAG sobre o LLMPort da llm-core

- [ ] 7.1 Consumir `LLMPort`/`create_llm_provider` da `llm-core` no fluxo de consulta, sem definir cliente de LLM próprio
- [ ] 7.2 `build_rag_prompt()` — system prompt, chunks com fonte/data e pergunta
- [ ] 7.3 Mapear `LLMUnavailableError` da `llm-core` para o estado "Chat desabilitado" na GUI

## 8. Infraestrutura — Document Sources (reconciliadas + transferidas)

- [ ] 8.1 Confirmar `MaterialFactsSource` (fatos relevantes via `RegulacaoRepository`)
- [ ] 8.2 Confirmar `NoticiasSource` (Plantão B3)
- [ ] 8.3 `InformeMensalSource` — lê o cache `informe-mensal/`, converte HTML em texto, retorna vazio se ticker sem dados
- [ ] 8.4 `RelevantesSource` — lê o cache `documentos-relevantes/`, extrai texto do PDF, retorna vazio se ticker sem dados
- [ ] 8.5 Registrar as fontes disponíveis na factory/composição de indexação

## 9. Aplicação — Use Cases

- [ ] 9.1 `IndexarDocumentosUseCase` — sources disponíveis, VectorStore, EmbeddingPort, progress
- [ ] 9.2 `ConsultarDocumentosUseCase` — embed → search → prompt RAG → `LLMPort` da `llm-core` → resposta + fontes
- [ ] 9.3 Erro em uma fonte não interrompe as outras

## 10. Testes Infraestrutura

- [ ] 10.1 VectorStore: criar, inserir, buscar, deduplicar
- [ ] 10.2 Embedding adapters com mocks
- [ ] 10.3 Consumo do `LLMPort` da `llm-core` com mock
- [ ] 10.4 Document sources com mocks (incluindo `InformeMensalSource` e `RelevantesSource` sobre caches temporários)
- [ ] 10.5 Use cases com mocks — fluxo completo, fonte falhando, VectorStore vazio

## 11. Config — Embedding Config

- [ ] 11.1 `load_embedding_config()`/`save_embedding_config()` no sub-bloco `llm.embedding`, reutilizando o read-modify-write da `llm-core`
- [ ] 11.2 Estender `check_llm_deps()` da `llm-core` para também exigir `fastembed`
- [ ] 11.3 `get_embedding_presets()`

## 12. GUI — ChatPanel

- [ ] 12.1 `ChatPanel(tkinter.Frame)` — mensagens, scroll, entrada, enviar
- [ ] 12.2 Estado não configurado, estado sem documentos
- [ ] 12.3 Copy/paste livre, scroll automático
- [ ] 12.4 Barra de progresso "Atualizar Documentos"

## 13. GUI — Integração com o diálogo da llm-core

- [ ] 13.1 Botão "Configurar" do ChatPanel abre o `LLMConfigDialog` da `llm-core`

## 14. GUI — Integração

- [ ] 14.1 Aba "Chat Geral" com `ChatPanel(ticker=None)`
- [ ] 14.2 Aba "Chat Ticker" com `ChatPanel(ticker=<selecionado>)`
- [ ] 14.3 Visibilidade condicionada a `llm.chat.provider`

## 15. CLI

- [ ] 15.1 `--index <TICKER>` com `--data-inicio`, `--data-fim`
- [ ] 15.2 `run_index(args)`, verificação de deps, dispatch

## 16. Testes GUI

- [ ] 16.1 ChatPanel estados, integração com o diálogo da `llm-core`, load_embedding_config

## 17. Quality Gate

- [ ] 17.1 `make lint complexity` limpo
- [ ] 17.2 `pytest -m "not llm"` + `pytest -m "llm"` passam
- [ ] 17.3 Testes existentes sem regressão
- [ ] 17.4 Executar `openspec validate llm-chat` e garantir que a change permanece válida
