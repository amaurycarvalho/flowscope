## ADDED Requirements

### Requirement: EmbeddingPort protocol
O sistema DEVE definir um protocolo `EmbeddingPort` com método `embed(texts: list[str]) -> list[list[float]]` que retorna uma lista de vetores de embedding, um para cada texto de entrada.

#### Scenario: Embedding de múltiplos textos
- **WHEN** `embed(["texto um", "texto dois"])` é chamado
- **THEN** dois vetores de floats DEVEM ser retornados

### Requirement: FastembedAdapter (local, default)
O sistema DEVE implementar `FastembedAdapter` usando `fastembed`, carregando o modelo `BAAI/bge-small-pt-v1.5` (384 dimensões, otimizado para português) com lazy loading na primeira chamada de `embed()`. O adaptador DEVE tratar `ImportError` com mensagem sugerindo `pip install flowscope[llm]`.

#### Scenario: Primeira chamada carrega o modelo
- **WHEN** `embed()` é chamado pela primeira vez
- **THEN** o modelo DEVE ser baixado (se ausente) e carregado, e embeddings DEVEM ser retornados

#### Scenario: Fastembed não instalado
- **WHEN** `FastembedAdapter` é instanciado mas `fastembed` não está disponível
- **THEN** `ImportError` DEVE ser capturado e uma exceção informativa DEVE ser lançada

#### Scenario: Embedding de batch
- **WHEN** `embed()` recebe 10 textos
- **THEN** 10 vetores de 384 dimensões DEVEM ser retornados

### Requirement: LiteLLMEmbeddingAdapter (API)
O sistema DEVE implementar `LiteLLMEmbeddingAdapter` usando `litellm.embedding()`, aceitando `model` e `api_key` como parâmetros. O adaptador DEVE suportar os modelos `text-embedding-3-small` (OpenAI) e `text-embedding-004` (Gemini) via configuração.

#### Scenario: Embedding via API OpenAI
- **WHEN** `LiteLLMEmbeddingAdapter(model="openai/text-embedding-3-small", api_key="sk-...")` é usado
- **THEN** embeddings DEVEM ser obtidos via chamada HTTP à API OpenAI

#### Scenario: Erro de API tratado
- **WHEN** a chamada à API falha (ex: chave inválida)
- **THEN** uma exceção com mensagem descritiva DEVE ser lançada

### Requirement: Factory de embedding provider
O sistema DEVE fornecer uma factory `create_embedding_provider(config: dict) -> EmbeddingPort` que instancia `FastembedAdapter` se `provider == "fastembed"` ou `LiteLLMEmbeddingAdapter` caso contrário, usando a configuração do `~/.flowscope/config.json`.

#### Scenario: Provider fastembed selecionado
- **WHEN** config tem `{"provider": "fastembed", "model": "BAAI/bge-small-pt-v1.5"}`
- **THEN** `FastembedAdapter` DEVE ser retornado

#### Scenario: Provider API selecionado
- **WHEN** config tem `{"provider": "openai", "model": "openai/text-embedding-3-small", "api_key": "sk-..."}`
- **THEN** `LiteLLMEmbeddingAdapter` DEVE ser retornado
