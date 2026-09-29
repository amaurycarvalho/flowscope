## Context

Ver `proposal.md - Why`. Hoje o background é orquestrado por classes `*_job.py` e threads inline, cada uma com thread + `queue.Queue` + drenagem via `self.after` + watchdog de 120s (`time.monotonic`) + guardas de geração. O `FlowScopePresenter` (`presentation/gui/presenter.py`) é a autoridade única de estado ocupado (`_operacoes_ativas`), botão de interromper (`_jobs_cancelaveis`) e cursor, com um `CancellationToken` compartilhado e um contador de token quebrado em cenários de substituição.

Restrições relevantes:
- `layer-boundaries`: `presentation` só pode importar `application` e `domain` (exceto composition root). O componente novo não pode importar `infrastructure`.
- Orçamento de testes de UI (`layer-boundaries`): testes de apresentação cobrem wiring, estado de widget, empty-state e ciclo de thread/queue.
- `process-cancellation` descreve o token reiniciado por operação e a interrupção conjunta de jobs sobrepostos.

## Goals / Non-Goals

**Goals:**
- Um único componente de gestão de jobs com políticas de agendamento e token por job.
- Preservar integralmente o comportamento observável dos quatro jobs existentes.
- Ser a base sobre a qual a carga principal e as varreduras de catálogo migrarão nas fatias seguintes.
- Concentrar os testes de processamento em módulos headless (sem `DISPLAY`/Tk) e reduzir os testes de UI ao orçamento de `layer-boundaries`.

**Non-Goals:**
- Migrar a carga principal ou leituras de catálogo nesta fatia (fatias B e C).
- Adotar `concurrent.futures`/asyncio ou reescrever a política de cancelamento do presenter (o token por job convive com a spec atual; a carga principal entra no conjunto só na fatia B).
- Mudar a interface da aplicação: o manager recebe callables, não conhece casos de uso específicos.
- Aumentar o número de testes UI-gated (`@needs_display`); o processamento é testado headless.

## Decisions

### Decisão 1: Componente na camada de apresentação

**Escolha**: novo pacote `src/flowscope/presentation/gui/background/`.

**Alternativas**: mover para `application`; criar um módulo em `presentation/` fora de `gui`.

**Razão**: afinidade de thread do Tk (`after`) e marshaling de eventos são concerns de adaper, e o manager coordena o `FlowScopePresenter`, que já vive em `presentation`. Colocá-lo em `application` introduziria dependência de agendamento de UI na camada de aplicação. Não importa `infrastructure`, preservando `layer-boundaries`.

### Decisão 2: Trabalho descrito por callable + `JobContext`

**Escolha**: `submit(work, *, group, policy, cancelavel, callbacks)` onde `work` é `Callable[[JobContext], None]`. `JobContext` publica `progress(...)`, `emit(tipo, payload)`, `resultado(...)`, `erro(...)` e expõe `token`/`cancelled`.

**Alternativas**: manter classes `*_job.py` e o manager apenas iniciar threads; usar herança de uma classe base `Job`.

**Razão**: o `JobContext` é o único ponto de contato do worker com o sistema e proíbe acesso a widgets por construção. As classes atuais viram funções de trabalho + configuração de política, eliminando a coreografia duplicada. Herança acoplaria os jobs ao manager e dificultaria testá-los isoladamente.

### Decisão 3: Políticas e grupos

**Escolha**: `group` identifica o domínio de exclusão (ex.: `"fundamental"`, `"documentos"`, `"resumos"`, `"revisao"`); `policy` define o comportamento entre jobs do mesmo grupo:
- `latest_wins`: cancela o job ativo do grupo e descarta suas mensagens tardias (substitui as guardas de geração atuais). Com `key`, uma requisição de mesma chave de um job ativo é descartada, distinguindo reentrada do mesmo acionamento de uma nova operação.
- `serialize`: mantém uma fila FIFO por grupo; novas requisições aguardam e são descartadas se forem idênticas (`key`) ou se o job ativo as tornou obsoletas.
- `parallel`: sem exclusão.

**Alternativas**: um único lock global; políticas fixas por tipo; `concurrent.futures.ThreadPoolExecutor` como scheduler.

**Razão**: os fluxos têm semânticas distintas — fundamentos/carga substituem, resumos serializam, versão/chat/preview são independentes. `ThreadPoolExecutor` não expressa "cancela o anterior do mesmo grupo" sem reimplementar essa camada; threads dedicadas por grupo são mais simples e previsíveis.

### Decisão 4: Token de cancelamento por job

**Escolha**: o manager cria um `CancellationToken` (já existente em `application/cancellation.py`) por job. `cancel(job_id)`, `cancel_group(group)` e `cancel_all()`.

**Alternativas**: manter o token único do presenter e limpá-lo a cada operação.

**Razão**: com supersede cancelável (decisão já tomada para a carga principal), o token único deixa de expressar corretamente "cancele o job antigo mas não o novo". O token por job é pré-requisito da fatia B e não altera a spec atual, que já fala em interromper jobs sobrepostos.

### Decisão 5: Pump único na thread do Tk

**Escolha**: um único `after` periódico drena as filas de todos os jobs, aplica o watchdog e despacha eventos aos callbacks. Encapsulado em `background/pump.py`, iniciado pelo manager e parado quando não há jobs ativos.

**Alternativas**: manter um laço `after` por job (como hoje).

**Razão**: elimina a possibilidade de esquecer a drenagem (a origem do bug documentado em `documentos-resumo-lote-persistente`) e garante que o cancelamento finalize a UI mesmo com o worker vivo. Um único pump reduz overhead e centraliza o watchdog.

### Decisão 6: Integração com o presenter por callbacks de ciclo de vida

**Escolha**: o manager emite `job_iniciado`/`job_terminado`; o wiring em `app_wiring.py` registra callbacks que chamam `presenter.enter()`/`exit()` e `presenter.job_cancelavel_iniciado()/finalizado()`.

**Alternativas**: o manager chama o presenter diretamente; o presenter observa o manager.

**Razão**: mantém o manager genérico (não conhece o presenter) e o presenter como autoridade única de estado. O contador de jobs do presenter passa a ser alimentado por eventos, corrigindo naturalmente substituição/cancelamento/falha.

### Decisão 7: `OperationGuard` mantido

**Escolha**: manter `OperationGuard` como guarda de UI contra reentrada do mesmo clique; a exclusão entre requisições passa a ser responsabilidade das políticas do manager.

**Razão**: já há evidência de que o guard evita cliques duplicados enquanto a operação corre; removê-lo ampliaria o escopo desta refatoração. A convivência é segura porque as políticas são idempotentes a chamadas repetidas.

### Decisão 8: Estratégia de teste — processamento headless, UI no mínimo

**Escolha**: os testes do manager (submit, políticas, token, pump, watchdog), das funções de trabalho e da orquestração dos mixins DEVEM ser headless — sem `DISPLAY`, sem `tk.Tk`. Ficam sob `@needs_display` apenas os comportamentos que só existem na presença do Tk: wiring de callback/botão, estado visual do widget, empty-state e o marshaling real do pump até o widget. Lógica pura hoje residente em módulos de apresentação (ex.: `TestPreview` de `document_preview`, que é `application`) DEVE migrar para `tests/test_application`/`tests/test_domain`.

**Alternativas**: manter os testes de coreografia dentro dos testes de painel; testar o manager através de uma janela Tk real.

**Razão**: o critério de `layer-boundaries` para o orçamento de UI é exatamente "wiring, estado de widget, empty-state e ciclo de thread/queue". O ciclo de thread/queue não precisa de display, então testá-lo via Tk é custo desnecessário. Centralizar no manager elimina a duplicação da coreografia e torna a maior parte dos testes de processamento triviais de rodar headless. Um guardrail de contagem de `@needs_display` impede regressão silenciosa.

## Risks / Trade-offs

- **[Risco]** O pump único pode se tornar ponto de acoplamento e regressão para todos os jobs → **Mitigação**: portar job a job com os testes existentes (`test_fundamental_job`, `test_resumos_job`, `test_cancelamento_integracao`) rodando a cada passo e sem alterar comportamento visível.
- **[Risco]** `serialize` com fila pode reter trabalho obsoleto (ex.: resumos de um ticker que mudou) → **Mitigação**: `key` por grupo permite descartar requisições duplicadas/obsoletas; a fatia define a chave por caso.
- **[Risco]** Callbacks de ciclo de vida e a contabilidade do presenter podem desincronizar em substituição → **Mitigação**: teste dedicado de ciclo de vida equilibrado em substituição/cancelamento; o `exit()` já é idempotente.
- **[Trade-off]** Mais um nível de indireção entre UI e jobs → **Benefício**: coreografia única testável e base para mover a carga principal sem repetir o padrão.

## Migration Plan

1. Criar o pacote `background/` e o teste de ciclo de vida thread/queue, sem integrar ainda.
2. Portar `FundamentalJob` (tem geração e watchdog mais complexos) e validar com `test_fundamental_job` + `test_cancelamento_integracao`.
3. Portar `DocumentosJob`, `NoticiasJob`, `ResumosPendentesJob` e as threads inline (preview, chat, config LLM, versão).
4. Remover das classes de job a thread/fila/watchdog; manter em cada módulo apenas a função de trabalho e sua configuração de política.
5. Migrar os testes de processamento para módulos headless e mover a lógica pura para as camadas internas; registrar a contagem baseline de testes `@needs_display` e não permitir aumento.
6. Rodar a suíte de apresentação e a checagem de fronteiras; rollback = reverter o commit (refatoração sem migração de dados).
