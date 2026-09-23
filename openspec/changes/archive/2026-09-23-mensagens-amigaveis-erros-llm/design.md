## Context

Ver `proposal.md - Why`. O estado atual que molda o desenho:

- O adaptador traduz exceções do liteLLM para o domínio em `_mapear_excecao()` (`src/flowscope/infrastructure/llm/adapter.py:43-49`), percorrendo `_MAPEAMENTO_EXCECOES` (`adapter.py:24-31`) e caindo em `LLMProviderError(str(exc))` no final. Não há entrada para `ServiceUnavailableError` nem `InternalServerError`; como ambos herdam de `APIError`, são absorvidos pela entrada `("APIError", LLMProviderError)`.
- Os dois pontos que exibem a falha usam `str(exc)` cru: `ResumosActionsMixin._interromper_resumos()` (`src/flowscope/presentation/gui/app_resumos_actions.py:160-172`, `f"{arquivo.nome}: {exc}"`) e `LLMConfigDialog._verificar_teste()` (`src/flowscope/presentation/gui/llm/config_dialog.py:267-283`, `_status_var.set(mensagem)`).
- Os registros de log usam o erro original e devem permanecer: `app_resumos_actions.py:166-171` (`logger.error(..., exc, exc_info=exc)`) e `config_dialog.py:257-265` (`_registrar_falha`, com tipo e mensagem do erro, sem a chave de API).
- A hierarquia de domínio atual (`src/flowscope/domain/llm/exceptions.py`) tem cinco tipos e a GUI importa apenas `LLMError` (`config_dialog.py:16`, `document_summary.py:17`); ela não deve depender do liteLLM.
- O liteLLM imprime um banner de depuração (`Give Feedback / Get Help`, `LiteLLM.Info`) na saída padrão ao mapear uma exceção do provedor, controlado pelo flag global `litellm.suppress_debug_info` (padrão `False`; o Router e o proxy do próprio liteLLM o ligam). Verificado empiricamente: com o flag ligado, o banner deixa de ser impresso.

## Goals / Non-Goals

**Goals:**
- Distinguir sobrecarga/5xx do provedor da demais falhas de provedor, para que a interface oriente "tente novamente" quando for o caso.
- Traduzir cada categoria de erro de LLM em uma mensagem curta em português, exibida nas duas telas.
- Manter `str(exc)` e os registros de log inalterados.

**Non-Goals:**
- Alterar o caminho não-estrito `DocumentSummaryService.gerar()` nem a mensagem de pré-visualização "Resumo indisponível.".
- Alterar a persistência, o fluxo do lote (fases/progresso) ou o desfecho de sucesso.
- Acrescentar código HTTP ou dica técnica na mensagem exibida.
- Introduzir retry/backoff automático.

## Decisions

### 1. Novo subtipo `LLMServiceUnavailableError` mapeado antes de `APIError`

Acrescenta-se `("ServiceUnavailableError", LLMServiceUnavailableError)` e `("InternalServerError", LLMServiceUnavailableError)` a `_MAPEAMENTO_EXCECOES`, acima de `("APIError", LLMProviderError)`. As subclasses entram em `exceptions.py` e são exportadas em `domain/llm/__init__.py`.

- **Por quê:** o 503 "high demand" precisa ser reconhecido como transitório; sem tipo próprio, a apresentação não o distingue de autenticação/requisição inválida. A busca por `getattr(litellm, nome, None)` já tolera versões sem a classe.
- **Alternativas:** humanizar apenas os cinco tipos existentes (rejeitado: o 503 continuaria genérico, sem orientar nova tentativa); anexar `status_code`/`retryable` ao `LLMProviderError` (rejeitado: contrato menos explícito e mais fácil de ignorar que um subtipo).
- **Não-goal associado:** `str(LLMServiceUnavailableError)` continua sendo a mensagem técnica do liteLLM, preservando o log.

### 2. Tradução isolada na apresentação (`presentation/gui/llm/mensagens.py`)

Uma função `mensagem_erro_llm(exc: BaseException) -> str` mapeia por `isinstance` na ordem dos subtipos de `LLMError` e devolve o texto amigável. As duas telas passam a chamá-la: no lote, `f"{arquivo.nome}: {mensagem_erro_llm(exc)}"`; no teste, `_status_var.set(mensagem_erro_llm(exc))`.

- **Por quê:** a GUI já importa só o domínio; a tradução é preocupação de apresentação e texto, não de domínio. Um único mapa evita divergência entre as duas telas.
- **Alternativas:** mudar `str(exc)` na origem (rejeitado: altera o log e o diagnóstico); colocar o texto no domínio (rejeitado: acopla domínio a idioma/UI).

### 3. Mapa de mensagens

Contrato observável das duas telas; `LLMUnavailableError` e exceções não-LLM permanecem com `str(exc)`.

| Tipo | Mensagem exibida |
|---|---|
| `LLMServiceUnavailableError` | "O serviço de I.A. está temporariamente indisponível (alta demanda). Tente novamente em instantes." |
| `LLMRateLimitError` | "Limite de uso da I.A. atingido. Aguarde um momento e tente novamente." |
| `LLMCommunicationError` | "Não foi possível conectar ao serviço de I.A. Verifique a conexão e a API URL." |
| `LLMConfigurationError` | "Configuração de I.A. inválida. Verifique o modelo e a API URL." |
| `LLMProviderError` genérico | "O provedor de I.A. retornou um erro. Consulte o log para mais detalhes." |
| `LLMUnavailableError` | mantém `str(exc)` (deps/`none`, já amigável) |
| exceção não-LLM | mantém `str(exc)` (ex.: falha curta de conversão de PDF) |

### 4. Desabilitar o banner de depuração do liteLLM no import

`_import_litellm()` passa a ligar `litellm.suppress_debug_info = True` antes de retornar o módulo, cobrindo as chamadas de teste e o resumo em lote antes de qualquer `litellm.completion`.

- **Por quê:** a função é o único funil de import do liteLLM no adaptador. O flag afeta apenas o banner de depuração do terminal; a exceção tipada e os `logger.*` permanecem iguais.
- **Alternativas:** filtrar `stdout` em volta da chamada (rejeitado: intercepta a saída global e é frágil); desligar via API pública (não há equivalente a `_turn_on_debug` para desligar).

## Risks / Trade-offs

- **[Testes que afirmam `str(exc)` na tela]** → atualizar `tests/test_presentation/test_llm_config_dialog.py::TestTestarConexao::test_falhas_exibem_motivo` para o texto amigável, mantendo `test_falha_registra_log_sem_chave` intacto.
- **[Nome próximo de `LLMUnavailableError`]** → docstrings distintos ("provedor respondeu 5xx/sobrecarga" vs. "sem provedor/deps") e o mapa de apresentação separa os textos.
- **[Classes ausentes em versões do liteLLM]** → `getattr(..., None)` já ignora nomes inexistentes, caindo no comportamento atual (`LLMProviderError`).
- **[Escopo indevido no caminho não-estrito]** → `gerar()` e a pré-visualização não são tocados; apenas os dois pontos de exibição da falha.
- **[Exceções não-LLM no lote]** → o fallback preserva `str(exc)`, útil para falhas de conversão, sem perder a mensagem curta atual.
- **[Flag global do liteLLM no processo]** → `suppress_debug_info = True` afeta qualquer uso do liteLLM no processo; é o mesmo que o Router/proxy do liteLLM já fazem e não altera exceções nem log.

## Migration Plan

- Aditivo: novo subtipo, duas entradas de mapeamento e um helper novo; sem migração de dados nem mudança de configuração.
- Rollback: remover as entradas do novo tipo e voltar as duas telas a usar `str(exc)`.
