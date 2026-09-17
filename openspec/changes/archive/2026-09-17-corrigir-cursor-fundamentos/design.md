## Context

Ver `proposal.md - Why`. O presenter mantém `_operacoes_ativas` (`presenter.py:97`) e só restaura botões e cursor quando ele chega a zero (`presenter.py:113-118` e `190-197`). Cada job fundamentalista incrementa o contador em `on_fundamental_started` (`controller_fundamental.py:50`) e deveria decrementar em `on_fundamental_finished`, chamado apenas por `_drenar_fundamental` (`controller_fundamental.py:73-77`).

Quando um job é substituído, `self._fundamental_job` passa a apontar para o novo (`controller_fundamental.py:49`) e o callback pendente do job antigo cai no early-return `job is not self._fundamental_job` (`controller_fundamental.py:71-72`), sem chamar `on_fundamental_finished`. O contador nunca retorna a zero. Gatilhos: (a) duplo clique em "Atualizar fundamentos", pois o disparo manual não desabilita botões; (b) F5/Enter durante a análise, que é `bind_all` e ignora botões desabilitados (`app_layout.py:228`), enquanto o `OperationGuard` já foi liberado no `finally` da carga; (c) uma exceção ao tratar uma mensagem do job (ex.: renderização da tabela em `on_tab_changed`, chamado por `on_fundamental_result`) escapa do callback `after` de `_drenar_fundamental`, interrompe o reagendamento e nunca chama `on_fundamental_finished`.

## Goals / Non-Goals

**Goals:**
- Garantir que todo `on_fundamental_started` tenha exatamente um `on_fundamental_finished`, inclusive para jobs substituídos.
- Impedir o reinício manual da análise a partir do botão "Atualizar fundamentos" enquanto houver job ativo, e desabilitar os controles no disparo manual.
- Cobrir a regressão com testes.

**Non-Goals:**
- Cancelar efetivamente a thread do job substituído (ela termina sozinha; as mensagens são descartadas por geração).
- Alterar o `OperationGuard` ou tornar a carga histórica assíncrona.
- Mudar a API de domínio/aplicação ou o formato das mensagens do `FundamentalJob`.

## Decisions

### 1. Balancear o job substituído no controller

Em `_iniciar_analise_fundamental`, capturar `job_anterior = self._fundamental_job`; após criar e atribuir o novo job, chamar `on_fundamental_started()` e, se `job_anterior is not None`, chamar `on_fundamental_finished()`.

A ordem "started antes de finished" evita que o contador passe por zero no instante da substituição (o que restauraria botões/cursor e os desabilitaria logo em seguida, causando piscada). O callback pendente do job antigo continua inofensivo, pois `_fundamental_job` já aponta para o novo.

- **Alternativa descartada**: decrementar no early-return de `_drenar_fundamental` ao detectar job substituído. O callback do job antigo pode disparar tarde (após o job novo concluir e após uma operação futura iniciar), decrementando o contador de uma operação que não é dele.
- **Alternativa descartada**: trocar o contador por um conjunto de tokens de job no presenter. Mais invasivo e altera a API/testes do presenter sem ganho para o bug.

### 2. Desabilitar controles no início de qualquer análise fundamentalista

`on_fundamental_started` passa a chamar `disable_all_buttons()` (já idempotente, `app_status.py:86`). Na carga histórica é no-op (controles já desabilitados); no disparo manual, desabilita o botão "Atualizar fundamentos" e demais controles, restaurando-os em `on_fundamental_finished`.

- **Alternativa descartada**: desabilitar apenas no controller do disparo manual — duplicaria lógica e deixaria outros caminhos descobertos.

### 3. Bloquear novo disparo manual enquanto houver job ativo

`on_atualizar_fundamentos` retorna cedo se `self._fundamental_job is not None`. O bloqueio fica apenas nesse caminho manual (o mesmo controle citado na spec); a carga por F5/período continua permitida e, se ocorrer, substitui o job antigo com o balanceamento do item 1 (dados novos exigem recomputação).

- **Alternativa descartada**: bloquear em `_iniciar_analise_fundamental` — impediria a recomputação após uma nova carga, deixando fundamentos obsoletos.

### 4. Drenagem resiliente a falhas ao tratar mensagens

`_consumir_fila` passa a tratar cada mensagem dentro de um `try/except`: a falha é registrada via `self._logger.error(LogEntry(...))` e o esvaziamento da fila continua. Quando a mensagem é terminal (`MENSAGEM_RESULTADO`/`MENSAGEM_ERRO`), mesmo com falha no tratamento o job é marcado como concluído, garantindo `on_fundamental_finished`, restauração de cursor/botões e limpeza da barra.

Isso cobre o segundo gatilho observado: uma exceção ao processar o resultado (ex.: renderização da tabela em `on_tab_changed`, chamado por `on_fundamental_result`) escapava do callback `after`, interrompia o reagendamento e deixava o cursor `watch` preso, pois `on_fundamental_finished` nunca era chamado.

Como defesa adicional, a chamada a `_consumir_fila` em `_drenar_fundamental` também fica sob `try/except` (encerra o job em falhas fora do tratamento por mensagem), e `FlowScopeGUI.report_callback_exception` passa a registrar no log do flowscope qualquer exceção não tratada em callbacks do Tk — hoje ela só ia para o `stderr` e se perdia, dificultando o diagnóstico da falha de renderização.

- **Alternativa descartada**: envolver apenas `on_fundamental_result` no presenter — não cobriria falhas em mensagens de progresso nem outros erros da drenagem.
- **Alternativa descartada**: encerrar o job em qualquer falha (inclusive de progresso) — interromperia a análise cedo; com o tratamento por mensagem, uma falha de progresso é registrada e a drenagem prossegue.

### 5. Watchdog de inatividade/liveness do job

Cada `_drenar_fundamental` verifica `_job_travado(job)`: encerra o job quando a thread morreu e a fila está vazia (morreu sem publicar mensagem terminal) ou quando passaram mais de `_LIMITE_INATIVIDADE_S` (120s) sem nenhuma mensagem de progresso. O encerramento força `on_fundamental_finished`, restaurando cursor/controles, e registra um `WARNING` com a geração do job. A referência da thread é guardada em `FundamentalJob.thread`.

Isso cobre o caso relatado de o cursor permanecer `watch` em listagens grandes (IDIV/IFIX) sem exceção registrada: uma análise que trava ou cuja thread morre silenciosamente deixa de manter a interface presa.

- **Alternativa descartada**: timeout curto por operação — encerraria análises legítimas de índices grandes; o limite é de inatividade (progresso), não de duração total.
- **Alternativa descartada**: deixar apenas o contador de operações — não distingue "análise longa" de "análise travada".

### 6. Testes

- Controller/presenter: novo job iniciado com job anterior ativo chama `on_fundamental_finished` para o substituído; ao concluir o novo, `_operacoes_ativas == 0` e `clear_wait_cursor`/`restore_all_buttons` são chamados.
- Manual: `on_atualizar_fundamentos` não inicia novo job quando já existe um ativo; `on_fundamental_started` chama `disable_all_buttons`; `PortfolioNotFoundError` em `on_index_clicked` chama `on_operation_finished` uma única vez.
- Resiliência: erro ao tratar o resultado, erro ao tratar progresso, thread morta e inatividade prolongada não impedem o encerramento do job.
- GUI (requer `DISPLAY`): cursor do `Treeview` da tabela de Fundamentos volta ao valor original após o fluxo de substituição.

## Risks / Trade-offs

- **[Piscada de cursor/botões na substituição]** → mitigado pela ordem started-antes-de-finished (item 1), que nunca deixa o contador chegar a zero.
- **[Bloqueio do botão de atualizar durante análise]** → comportamento intencional; o usuário aguarda a análise terminar. Documentado na spec.
- **[Job antigo continua consumindo rede/CPU até terminar]** → aceito; já era o comportamento atual e o cancelamento de thread fica fora de escopo.
- **[Testes de GUI dependentes de display]** → seguem o padrão existente (`pytest.mark.skipif` sem `DISPLAY`).

## Migration Plan

Sem migração de dados. Rollback = reverter a change.

## Open Questions

- Nenhuma.
