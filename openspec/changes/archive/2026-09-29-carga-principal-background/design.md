## Context

Ver `proposal.md - Why`. Hoje `controller_data.py` executa `LoadIndexPortfolioUseCase.execute` e `AnalyzeTickersUseCase.execute` dentro de `with self._guard.acquire()`, de forma síncrona na thread do Tk, alimentando um `ProgressReporter` cujo `on_update` chama `presenter.on_progress` (que toca widgets). Ao final, `presenter.on_result` renderiza os gráficos e `_iniciar_analise_fundamental` encadeia o job fundamentalista. A fatia A entregou o `BackgroundManager` com token por job e política `latest_wins` (com descarte por `key`).

Nenhum dos dois casos de uso aceita token de cancelamento; `DataRepository.get_index_tickers`/`fetch_trades` e o `IndicatorEngine` não observam interrupção. A spec `process-cancellation` hoje exclui explicitamente a carga principal do botão de interromper.

## Goals / Non-Goals

**Goals:**
- Eliminar o processamento não-UI da thread do Tk na carga principal.
- Tornar a carga principal cancelável e substituível sem travar a interface.
- Preservar rotulagem de fases, pesos do `ProgressReporter`, mensagens e estado de botões/cursor.
- Testar submissão, eventos, supersede e cancelamento da carga com presenter fake headless, sem acrescentar testes UI-gated de processamento.

**Non-Goals:**
- Migrar as varreduras de catálogo (fatia C).
- Redesenhar o `ProgressReporter` ou a renderização dos gráficos.
- Cancelamento fino dentro do motor de indicadores (ver Decisão 4).
- Adicionar testes `@needs_display` para o processamento da carga; UI só para o wiring do botão de interromper.

## Decisions

### Decisão 1: Um job de carga com política `latest_wins` e `key` de dedup

**Escolha**: o controller submete um trabalho ao manager no grupo `"carga"` com política `latest_wins` e `key` derivada de `(índice ou "load", ref_date, período, amostragem)`. Requisição de mesma `key` ativa é descartada; requisição distinta cancela e substitui a anterior.

**Alternativas**: manter `OperationGuard` bloqueando toda operação concorrente; política `serialize`.

**Razão**: satisfaz as duas decisões tomadas — reentrada ignorada e nova operação com supersede — usando o mecanismo genérico da fatia A, sem lógica de concorrência na UI.

### Decisão 2: `ProgressReporter` permanece no worker; só o callback final é marshaled

**Escolha**: o trabalho cria o `ProgressReporter` e suas fases no worker; o `on_update` publica um evento `Progresso`. O callback registrado na thread do Tk chama `presenter.on_progress`. O estado de fase/peso fica no worker, que é onde as fases são disparadas.

**Alternativas**: mover o `ProgressReporter` para a thread do Tk e enviar eventos de fase; reimplementar a barra no manager.

**Razão**: o `ProgressReporter` só faz aritmética de progresso e não toca widgets; mantê-lo no worker preserva a lógica de pesos já testada. O evento transporta `(current, total, label)`, o mesmo contrato de `on_progress`.

### Decisão 3: Renderização e encadeamento fundamentalista na thread do Tk

**Escolha**: o resultado do job é entregue por evento; o handler executa `presenter.on_portfolio_loaded`, `presenter.on_result` e `_iniciar_analise_fundamental`, exatamente como hoje, porém fora do caminho síncrono.

**Alternativas**: renderizar no worker (proibido pela afinidade do Tk).

**Razão**: a fronteira de thread-safety permanece a mesma; muda apenas quem dispara a renderização.

### Decisão 4: Cancelamento cooperativo até os laços de I/O; motor com callback

**Escolha**: adicionar `cancel_token: CancellationToken | None` a `LoadIndexPortfolioUseCase.execute` e `AnalyzeTickersUseCase.execute`; repassá-lo a `DataRepository.get_index_tickers`/`fetch_trades` (infrastructure pode importar application) e verificar entre fases no caso de uso. Para o `IndicatorEngine` (domain, que não pode importar application), aceitar um `Callable[[], bool]` opcional de cancelamento, adaptado pelo caso de uso. Quando o token dispara no meio, o worker descarta o resultado parcial.

**Alternativas**: dar o token de application ao domain; não cancelar o motor.

**Razão**: respeita `layer-boundaries` (domain sem importar application) e cobre o custo dominante (rede/download). O motor roda majoritariamente sobre dados já baixados e é interrompível no granularidade de ticker via callback.

### Decisão 5: `OperationGuard` mantido, estreitado ao setup síncrono

**Escolha**: manter `OperationGuard` envolvendo apenas o trecho síncrono do controller que monta e submete o job, não toda a duração do job. A exclusão de longa duração passa a ser do manager.

**Alternativas**: manter o guard por toda a operação (impediria o supersede); remover o guard.

**Razão**: atende à decisão de manter o guard como proteção de reentrada sem conflitar com o supersede. O guard impede chamadas reentrantes do mesmo handler durante a montagem da requisição.

### Decisão 6: `on_ticker_edit` usa o mesmo grupo de carga

**Escolha**: a carga de portfólio IDIV em `on_ticker_edit` é submetida ao grupo `"carga"` com `latest_wins`.

**Razão**: unifica a semântica de substituição/cancelamento com a carga principal e remove a última chamada de rede síncrona da thread do Tk.

### Decisão 7: Estratégia de teste — controller headless, UI só no wiring

**Escolha**: os testes da carga principal usam um presenter fake e um manager fake/síncrono, sem `tk.Tk`. Cobrem submissão, `key`/supersede, tokens e descarte de resultado por eventos. O único teste UI-gated admitido é o wiring do botão de interromper (visibilidade na barra de status), conforme o orçamento de `layer-boundaries`.

**Alternativas**: testar a carga através da janela Tk (o que os testes atuais de `test_controller.py` evitam com `MagicMock`).

**Razão**: a lógica migra do caminho síncrono para a orquestração de eventos, que é testável headless; exigir Tk aqui inflaria a suíte sem cobrir comportamento novo. Mantém o baseline de `@needs_display` da fatia A sem aumento.

## Risks / Trade-offs

- **[Risco]** O `ProgressReporter` no worker publicar eventos em rajada e inundar a fila → **Mitigação**: o `ProgressReporter` já aplica *throttle* de atualização; o pump drena por tick.
- **[Risco]** Cancelamento durante a escrita de cache/índice deixar estado parcial → **Mitigação**: preservar as garantias atuais dos adaptadores (índice gravado por item) e descartar apenas o resultado em memória.
- **[Risco]** Motor de indicadores não interrompível no meio de uma execução longa → **Trade-off** aceito; verificar a cada ticker e documentar o limite.
- **[Risco]** Contabilidade de estado ocupado durante supersede reiniciar o cursor → **Mitigação**: eventos `job_iniciado/job_terminado` equilibrados e teste de substituição sem restauração intermediária.

## Migration Plan

1. Adicionar `cancel_token` aos dois casos de uso e aos métodos do `DataRepository`, com testes de application/infrastructure para a interrupção.
2. Adicionar o callback de cancelamento opcional ao `IndicatorEngine` e adaptá-lo no caso de uso.
3. Converter `on_load_data`/`on_index_clicked`/`on_ticker_edit` em submissão de trabalho + eventos; mover a montagem do `ProgressReporter` para o worker.
4. Ajustar as specs `process-cancellation` e `loading-state-management` (deltas deste change).
5. Migrar os testes da carga para headless (presenter fake) e confirmar que a contagem de `@needs_display` não aumentou em relação ao baseline da fatia A.
6. Validar com os testes de controller, cancelamento e integração; rollback = reverter o commit (sem migração de dados).
