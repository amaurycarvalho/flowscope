## Why

Quando uma análise fundamentalista em background é substituída por outra antes de concluir (duplo clique em "Atualizar fundamentos" ou F5 durante a análise), o contador de operações ativas do presenter nunca volta a zero. O cursor "watch" (ampulheta) e os botões desabilitados ficam presos indefinidamente — sintoma visível sobre a tabela da sub-aba "Fundamentos" após a carga terminar.

## What Changes

- Compensar o ciclo de vida do job fundamentalista substituído: todo `on_fundamental_started` deve ter exatamente um `on_fundamental_finished` correspondente, mesmo quando um novo job assume o lugar do anterior.
- Impedir que a análise fundamentalista manual (botão "Atualizar fundamentos") deixe os controles habilitados: os botões passam a ser desabilitados já no início da análise, e um novo disparo é bloqueado enquanto um job estiver ativo.
- Cobrir a regressão com testes de controller/presenter e um teste de GUI (quando houver display) verificando que o cursor do `Treeview` da tabela de Fundamentos volta ao valor original.

## Capabilities

### New Capabilities

<!-- Nenhuma nova capability. -->

### Modified Capabilities

- `loading-state-management`: o requisito de cursor de espera e de controles desabilitados durante a análise fundamentalista passa a exigir restauração garantida mesmo quando um job fundamentalista é substituído por outro, e a desabilitação de controles também no disparo manual da análise.

## Impact

- `src/flowscope/presentation/gui/controller_fundamental.py` — balanceamento do job substituído e bloqueio de novo disparo.
- `src/flowscope/presentation/gui/presenter.py` — invariante de contagem de operações ativas (se necessário).
- `src/flowscope/presentation/gui/app_status.py` / `app_tab_actions.py` / `app_actions.py` — desabilitação de controles no início da análise manual.
- Testes: `tests/test_presentation/test_fundamental_job.py`, `tests/test_presentation/test_presenter.py`, `tests/test_presentation/test_button_state.py`.
- Sem alterações de domínio, aplicação ou dependências externas.
