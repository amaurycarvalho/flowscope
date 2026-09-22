## 1. Autoridade de estado ocupado no presenter

- [x] 1.1 Substituir `_operacoes_ativas` por um estado `IDLE | BUSY` com contagem de referência no `FlowScopePresenter`, expondo `enter()`, `exit()` e `busy()` (context manager) — verificar com teste unitário que 0->1 chama `disable_all_buttons`/`enter_busy` uma única vez e 1->0 chama `restore_all_buttons`/`exit_busy`/`clear_progress` uma única vez.
- [x] 1.2 Garantir saída no `finally` do context manager `busy()` — verificar com teste que uma exceção dentro de `with presenter.busy():` deixa a contagem em zero e dispara `exit_busy`.
- [x] 1.3 Ajustar `on_operation_started/finished` e `on_fundamental_started/finished` para delegar ao estado único, preservando a substituição de job (started-antes-de-finished) — verificar que os testes de `test_presenter.py` e `test_controller.py` de substituição continuam passando.

## 2. Mecanismo de cursor na view

- [x] 2.1 Trocar a API pública `set_wait_cursor`/`clear_wait_cursor` por `enter_busy()`/`exit_busy()` (mantendo os métodos internos de snapshot) — verificar com teste de GUI que os widgets recebem `watch` na entrada e o cursor anterior na saída.
- [x] 2.2 Normalizar o baseline em `_set_wait_cursor` para ignorar cursores transitórios do toolkit (`hresize`, `sb_h_double_arrow`, `sb_v_double_arrow`) — verificar com teste de GUI que um `Treeview` com `cursor` capturado sobre separador restaura o cursor de repouso, e não `hresize`.
- [x] 2.3 Instalar um hook global `<Motion>` enquanto ocupado que reafirma o cursor de espera, e removê-lo na saída — verificar com teste de GUI que, com a operação ativa, mover sobre um separador de coluna e sobre um sash de `PanedWindow` mantém o cursor `watch`.
- [x] 2.4 Restaurar o baseline de forma idempotente ao sair e limpar o snapshot — verificar que `exit_busy()` repetido não altera cursores nem deixa estado residual.

## 3. Integração dos caminhos de operação

- [x] 3.1 Substituir as chamadas diretas em `controller.on_ticker_edit` (`controller.py:73,79`) por `with presenter.busy():` — verificar com teste que `set_wait_cursor`/`clear_wait_cursor` não são mais chamados diretamente e que o contexto é usado.
- [x] 3.2 Substituir as chamadas diretas em `actions._copy_chart` (`app_actions.py:240,247`) por `with presenter.busy():` — verificar com teste que o cursor é restaurado mesmo em `ClipboardError`.
- [x] 3.3 Envolver `_copy_data` (Ctrl+Shift+C) no contexto de estado ocupado — verificar com teste que a cópia de CSV restaura o cursor ao final.
- [x] 3.4 Atualizar mocks e testes que referenciam `set_wait_cursor`/`clear_wait_cursor` — verificar que a suíte `tests/test_presentation` passa sem referências à API antiga.

## 4. Balanceamento do job fundamentalista

- [x] 4.1 Garantir que `_iniciar_analise_fundamental` contabilize o término se `job.iniciar()` ou `on_progress` falharem após o incremento (`controller_fundamental.py:59-64`) — verificar com teste que uma exceção nesses pontos deixa a contagem em zero e chama `exit_busy`.
- [x] 4.2 Preservar a substituição de job e o watchdog existente sem regressão — verificar que os testes de `TestSubstituicaoJobFundamental` e `TestDrenarResiliente` continuam passando.

## 5. Resiliência do job de documentos

- [x] 5.1 Envolver o tratamento de cada mensagem em `_poll_documentos_job` em `try/except` com log, sem interromper o esvaziamento da fila (`app_actions.py:184-210`) — verificar com teste que um erro ao tratar progresso ainda encerra o job e libera o cursor.
- [x] 5.2 Adicionar watchdog de inatividade/liveness ao job de documentos, encerrando e restaurando cursor/controles quando a thread morre sem publicar término ou fica sem progresso além do limite — verificar com teste que thread morta e inatividade encerram o job com aviso no log.

## 6. Cobertura e sincronização da tabela de Fundamentos

- [x] 6.1 Adicionar teste de GUI que compara o cursor dos dois `Treeview` da tabela de Fundamentos antes, durante e após uma operação — verificar que ambos ficam `watch` durante e voltam ao original ao final, mesmo com o ponteiro sobre separador.
- [x] 6.2 Adicionar teste que enumera as abas/sub-abas construídas (`_GENERAL`, `_TICKER`) e confirma que os widgets estáticos são cobertos pelo snapshot de estado ocupado — verificar que a contagem de widgets cobertos é maior que zero e inclui os painéis de cada aba.
- [x] 6.3 Executar a suíte de testes da camada de apresentação — verificar que `pytest tests/test_presentation` passa.

## 7. Verificação final

- [x] 7.1 Executar lint e checagem de tipos do projeto (conforme Makefile/pyproject) — verificar que não há novas violações.
- [x] 7.2 Validar a change com `openspec validate centralizar-controle-cursor` — verificar que não há erros de spec.
