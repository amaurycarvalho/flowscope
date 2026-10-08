## Context

Ver `proposal.md` - Why. O adaptador `LiteLLMChatAdapter.complete` já é o único ponto por onde passam todas as chamadas de LLM (chat RAG e resumo de documentos) e já traduz as exceções do liteLLM para a hierarquia de domínio. O `RateLimiter` e o `executar_com_retry` de `infrastructure/b3/retry.py` estabelecem o padrão do projeto de injetar relógio/sono para tornar retry testável sem esperas reais.

## Goals / Non-Goals

**Goals:**

- Absorver indisponibilidades transitórias do provedor dentro de uma única chamada de completion, sem que o chamador precise saber de retries.
- Manter a classificação transitório/permanente no domínio (`flowscope.domain.llm`), sem acoplar a apresentação ou a aplicação ao liteLLM.
- Preservar exatamente o comportamento atual do chamador quando as tentativas se esgotam.

**Non-Goals:**

- Alterar o fluxo do lote (`lote.py`, `resumos_job.py`, `app_resumos_actions.py`) ou a política de aborto.
- Expor tentativas/backoff em `config.json` ou na GUI.
- Honrar `Retry-After` do provedor (fica para um change futuro).
- Retry de erros permanentes ou de parsing da resposta.

## Decisions

### Retry no adaptador, não no lote nem em wrapper externo

Retry centralizado em `complete` cobre todos os consumidores de uma vez e mantém a porta `LLMPort` como contrato único. Alternativas descartadas: retry no job de lote (não cobre o chat RAG e espalha política) e decorator em volta de `LLMPort` (mais uma camada de composição sem ganho sobre o adapter).

### Classificar por tipo de domínio, não por status HTTP

O adapter já mapeia a exceção do liteLLM para o domínio; o retry decide pela exceção **de domínio** resultante. Transitórios: `LLMServiceUnavailableError`, `LLMRateLimitError`, `LLMCommunicationError`. Os demais propagam na hora. Isso evita reintroduzir dependência de código de status do liteLLM e reaproveita o mapeamento existente.

### Backoff exponencial com jitter, limites como defaults no adaptador

Tupla de esperas padrão no estilo de `b3/retry.py` (ex.: `(0, 1, 3)` s ⇒ até 3 tentativas), com jitter para evitar sincronização entre chamadas. Alternativas: `num_retries` do liteLLM (acopla à biblioteca e não distingue permanente de transitório) e espera fixa (pior sob sobrecarga). Sem superfície de configuração nova.

### `acquire()` por tentativa

O `RateLimiter` passa a ser adquirido antes de **cada** tentativa física, para que retries respeitem o RPM. Alternativa descartada: adquirir uma vez por chamada lógica, que subestimaria a carga real no provedor.

### Injeção de `sleeper`/`jitter` para testes

O construtor aceita `sleeper` e uma fonte de jitter (ou usa `random` internamente com injeção) para os testes rodarem com relógio falso, como já ocorre no `RateLimiter`.

## Risks / Trade-offs

- [Retry multiplica latência e custo em picos longos] → Limite baixo de tentativas + backoff crescente; ao esgotar, o comportamento é o de hoje e o lote segue podendo abortar.
- [Retry interage com o rate limiter e pode alongar a espera] → `acquire()` por tentativa respeita o RPM; o backoff é somado à espera de cota, não a substitui.
- [Testes existentes de mapeamento transiente assumem uma única chamada] → Injetar esperas nulas/relógio falso nos testes e adicionar testes específicos de contagem de tentativas.
- [Jitter torna asserções de tempo instáveis] → Injetar a fonte de jitter para determinismo nos testes.
