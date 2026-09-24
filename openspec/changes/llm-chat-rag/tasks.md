## 1. Pré-requisitos e Setup

- [ ] 1.1 Verificar que a `llm-chat` está implementada e registrar o resultado
- [ ] 1.2 Verificar que as portas `DocumentoIndexavel`/`DocumentSource` e as fontes `MaterialFactsSource`/`NoticiasSource` existem
- [ ] 1.3 Estender o grupo `[llm]` do `pyproject.toml` com `fastembed>=0.4` e verificar a instalação
- [ ] 1.4 Criar a estrutura de diretórios do VectorStore, embeddings e indexação

## 2. Infraestrutura — VectorStore

- [ ] 2.1 `VectorStore` em SQLite puro com tabela e índices, e verificar criação na primeira execução
- [ ] 2.2 `add(chunks)` com deduplicação e verificar `INSERT OR IGNORE`
- [ ] 2.3 `search(query_embedding, ticker?, k)` com cosine em Python puro, e verificar com/sem filtro e banco vazio
- [ ] 2.4 `chunk_text()` em Python puro, e verificar texto curto, múltiplos chunks e texto vazio

## 3. Infraestrutura — Embeddings

- [ ] 3.1 `EmbeddingPort` protocol e verificar contrato
- [ ] 3.2 `FastembedAdapter` com lazy loading e tratamento de `ImportError`, e verificar primeira chamada
- [ ] 3.3 `LiteLLMEmbeddingAdapter` com tratamento de erro HTTP, e verificar com mock
- [ ] 3.4 `create_embedding_provider(config)` e verificar os dois provedores

## 4. Infraestrutura — Extração e Fontes

- [ ] 4.1 Extração de texto de HTML (informe mensal), e verificar com fixture
- [ ] 4.2 Extração de texto de PDF via `pypdf`, reutilizando o extrator existente, e verificar com fixture
- [ ] 4.3 Confirmar/reconciliar `MaterialFactsSource` e `NoticiasSource`, e verificar testes existentes
- [ ] 4.4 Fontes baseadas nos caches de documentos (relevantes, informe mensal, BDR) e verificar com caches temporários

## 5. Aplicação — Pipeline e Consulta

- [ ] 5.1 `IndexarDocumentosUseCase` (fontes → texto → chunk → embed → grava) com progresso, e verificar fluxo
- [ ] 5.2 Erro em uma fonte não interrompe as outras, e verificar fonte que falha
- [ ] 5.3 `ConsultarDocumentosUseCase` (embed → search → prompt RAG → `LLMPort`), e verificar com mock
- [ ] 5.4 `build_rag_prompt()` com fontes e datas, e verificar o prompt montado
- [ ] 5.5 Estado sem documentos indexados retorna orientação, e verificar mensagem
- [ ] 5.6 Integrar a consulta RAG à aba "Chat AI" como fonte adicional de contexto (ponto de extensão da `llm-chat`), e verificar com mock e índice vazio

## 6. Testes de Infraestrutura

- [ ] 6.1 VectorStore: criar, inserir, buscar e deduplicar
- [ ] 6.2 Adaptadores de embedding com mocks
- [ ] 6.3 Consumo do `LLMPort` da `llm-core` com mock
- [ ] 6.4 Fontes de documentos com mocks e caches temporários
- [ ] 6.5 Casos de uso com mocks (fluxo completo, fonte falhando, VectorStore vazio)

## 7. Config — Embedding

- [ ] 7.1 `load_embedding_config()`/`save_embedding_config()` no sub-bloco `llm.embedding` com read-modify-write, e verificar preservação de `llm.chat`
- [ ] 7.2 Estender `check_llm_deps()` para exigir `fastembed`, e verificar GUI e CLI
- [ ] 7.3 `get_embedding_presets()` e verificar presets fastembed/OpenAI/Gemini/Custom

## 8. CLI

- [ ] 8.1 Argumento `--index <TICKER>` com `--data-inicio` e `--data-fim`, e verificar parsing
- [ ] 8.2 `run_index(args)` com verificação de dependências e dispatch, e verificar código de saída 1 sem `[llm]`

## 9. Quality Gate

- [ ] 9.1 `make lint` e `make complexity` limpos
- [ ] 9.2 `pytest -m "not llm"` + `pytest -m "llm"` passam
- [ ] 9.3 Testes existentes sem regressão
- [ ] 9.4 Executar `openspec validate llm-chat-rag` e garantir que a change permanece válida
