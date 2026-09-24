## Purpose

Produz embeddings de texto localmente ou via API, isolando o restante do sistema do provedor escolhido.

## ADDED Requirements

### Requirement: EmbeddingPort protocol

O sistema DEVE definir um protocolo `EmbeddingPort` com o método `embed(texts) -> list[list[float]]`, retornando um vetor para cada texto de entrada.

#### Scenario: Embedding de múltiplos textos
- **WHEN** `embed(["texto um", "texto dois"])` é chamado
- **THEN** dois vetores de floats DEVEM ser retornados

### Requirement: FastembedAdapter (local, default)

O sistema DEVE implementar `FastembedAdapter` usando `fastembed`, carregando o modelo `BAAI/bge-small-pt-v1.5` (384 dimensões) com lazy loading na primeira chamada de `embed()`. O adaptador DEVE tratar `ImportError` com mensagem sugerindo `pip install flowscope[llm]`.

#### Scenario: Primeira chamada carrega o modelo
- **WHEN** `embed()` é chamado pela primeira vez
- **THEN** o modelo DEVE ser baixado (se ausente), carregado e os embeddings retornados

#### Scenario: Fastembed não instalado
- **WHEN** `FastembedAdapter` é usado sem `fastembed` disponível
- **THEN** o `ImportError` DEVE ser capturado e uma exceção informativa DEVE ser lançada

### Requirement: LiteLLMEmbeddingAdapter (API)

O sistema DEVE implementar `LiteLLMEmbeddingAdapter` usando `litellm.embedding()`, aceitando `model` e `api_key`, e DEVE lançar uma exceção descritiva quando a chamada à API falhar.

#### Scenario: Embedding via API OpenAI
- **WHEN** `LiteLLMEmbeddingAdapter(model="openai/text-embedding-3-small", api_key="sk-...")` é usado
- **THEN** os embeddings DEVEM ser obtidos via chamada HTTP à API

#### Scenario: Erro de API tratado
- **WHEN** a chamada à API falha
- **THEN** uma exceção com mensagem descritiva DEVE ser lançada

### Requirement: Factory de embedding provider

O sistema DEVE fornecer `create_embedding_provider(config)` que instancia `FastembedAdapter` se `provider == "fastembed"` ou `LiteLLMEmbeddingAdapter` caso contrário, a partir da configuração persistida.

#### Scenario: Provider fastembed selecionado
- **WHEN** a config tem `{"provider": "fastembed", "model": "BAAI/bge-small-pt-v1.5"}`
- **THEN** `FastembedAdapter` DEVE ser retornado

#### Scenario: Provider API selecionado
- **WHEN** a config tem `{"provider": "openai", "model": "openai/text-embedding-3-small", "api_key": "sk-..."}`
- **THEN** `LiteLLMEmbeddingAdapter` DEVE ser retornado
