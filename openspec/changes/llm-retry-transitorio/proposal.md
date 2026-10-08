## Why

Uma indisponibilidade temporária do provedor (HTTP 503 por alta demanda) aborta o resumo em lote de documentos inteiro no primeiro item, mesmo sendo um erro explicitamente transitório e retentável. Hoje o adaptador liteLLM faz uma única tentativa por chamada e não há nenhum retry no caminho de LLM, então um pico momentâneo do provedor interrompe um lote que poderia se recuperar sozinho.

## What Changes

- Adicionar retry com backoff exponencial e jitter no `LiteLLMChatAdapter.complete`, repetindo apenas erros **transitórios** (`LLMServiceUnavailableError`, `LLMRateLimitError`, `LLMCommunicationError`).
- Propagar imediatamente erros **permanentes** (`LLMProviderError`, `LLMConfigurationError`, `LLMUnavailableError`), sem consumir tentativas.
- Contar cada tentativa (incluindo retries) no `RateLimiter`, adquirindo a permissão por tentativa.
- Torna o retry observável e testável injetando `sleeper`/`clock`, no mesmo padrão do `RateLimiter` e de `infrastructure/b3/retry.py`.
- Manter o comportamento atual quando as tentativas se esgotam: a exceção de domínio final segue propagando, e o lote continua tratando-a como hoje.
- **Sem** mudança no fluxo do lote, na GUI ou na configuração (`config.json`); os parâmetros de retry ficam como defaults no adaptador.

## Capabilities

### New Capabilities

<!-- nenhuma -->

### Modified Capabilities

- `llm-provider`: novo requisito de retry de erros transitórios no adaptador liteLLM, com classificação transitório/permanente, backoff com jitter, limite de tentativas e contagem no rate limiter.

## Impact

- `src/flowscope/infrastructure/llm/adapter.py`: loop de retry em `complete` e pontos de injeção de relógio/sono.
- `tests/test_infrastructure/test_llm/test_adapter.py`: novos testes de retry; ajuste dos testes de mapeamento transiente que hoje assumem uma única chamada.
- Nenhuma mudança em `flowscope/application/documentos/*`, `flowscope/presentation/gui/*`, `factory.py` ou `config.json`.
