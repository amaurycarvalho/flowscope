## Why

O controle do cursor de espera (hourglass/"watch") está espalhado entre o presenter, que mantém um contador `_operacoes_ativas`, e a view, que mantém um snapshot `_cursor_states`, com caminhos que chamam `_set/_clear_wait_cursor` diretamente. Isso permite que a ampulheta vaze — às vezes de forma intermitente, dependendo da posição do ponteiro — e que o cursor do grid de colunas congeladas da tabela de Fundamentos fique dessincronizado do grid dos demais campos.

## What Changes

- Centralizar a **política** de estado ocupado no presenter como uma única máquina de estado `IDLE <-> BUSY`, com contagem de referência e um context manager `busy()` que garante entrada/saída balanceadas mesmo em exceção.
- Eliminar os caminhos diretos de cursor (`controller.on_ticker_edit`, `actions._copy_chart`) que hoje furam o contador do presenter.
- Garantir que todo `on_fundamental_started` tenha exatamente um `on_fundamental_finished`, inclusive quando `job.iniciar()` ou `on_progress` falham após o incremento.
- Estender a resiliência já existente no job fundamentalista ao job de documentos: watchdog de inatividade/liveness e tratamento por mensagem que nunca impede `on_operation_finished`.
- Na view, normalizar o snapshot para ignorar cursores transitórios geridos pelo Tk (`hresize` em separadores de coluna, `sb_*` em sashes de PanedWindow) e reafirmar o cursor enquanto ocupado em `<Motion>`, neutralizando o `ttk::treeview::Motion`/`State(userConfCursor)` que ressuscita a ampulheta em um único grid.
- Cobrir a sincronização entre os dois `Treeview` da tabela de Fundamentos com teste de GUI e um teste de cobertura que enumere as abas/sub-abas construídas.

## Capabilities

### New Capabilities

<!-- Nenhuma nova capability. -->

### Modified Capabilities

- `loading-state-management`: o requisito "Cursor de espera durante processamento" passa a exigir uma única autoridade de estado ocupado com transições balanceadas por contagem de referência, normalização de cursores transitórios do Tk, reafirmação do cursor durante a operação e restauração garantida em todos os caminhos de operação (incluindo falha ao iniciar/publicar o job e aquisição de documentos travada).

## Impact

- `src/flowscope/presentation/gui/presenter.py` — máquina de estado `IDLE/BUSY` e context manager `busy()`.
- `src/flowscope/presentation/gui/app_status.py` — snapshot normalizado, reafirmação em `<Motion>` e verificação de repouso.
- `src/flowscope/presentation/gui/controller.py` / `app_actions.py` — remoção das chamadas diretas `_set/_clear_wait_cursor`; uso do contexto do presenter.
- `src/flowscope/presentation/gui/controller_fundamental.py` — garantia de `on_fundamental_finished` em falhas de início/publicação.
- `src/flowscope/presentation/gui/documentos_job.py` / `app_actions.py` — watchdog e tratamento por mensagem do job de documentos.
- Testes: `tests/test_presentation/test_presenter.py`, `test_controller.py`, `test_button_state.py`, `test_fundamental_table.py`.
- Sem alterações de domínio, aplicação, dependências externas ou formato de mensagens dos jobs.
