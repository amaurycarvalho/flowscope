## 1. Balanceamento do job fundamentalista substituído

- [x] 1.1 Em `_iniciar_analise_fundamental` (`src/flowscope/presentation/gui/controller_fundamental.py`), capturar o job anterior antes de criar o novo, atribuir `self._fundamental_job` ao novo, chamar `on_fundamental_started()` e, se havia job anterior, chamar `on_fundamental_finished()`; verificar com teste que, após o job novo concluir, `_operacoes_ativas == 0`
- [x] 1.2 Confirmar que o callback pendente do job antigo continua caindo no early-return (`job is not self._fundamental_job`) sem decrementar o contador de uma operação futura; verificar com teste que a chamada de `_drenar_fundamental` para o job substituído não altera a contagem

## 2. Guarda e desabilitação no disparo manual

- [x] 2.1 Fazer `on_fundamental_started` (`src/flowscope/presentation/gui/presenter.py`) chamar `disable_all_buttons()` (idempotente) e verificar com teste que os controles são desabilitados no início da análise
- [x] 2.2 Fazer `on_atualizar_fundamentos` (`controller_fundamental.py`) retornar cedo quando `self._fundamental_job is not None` e verificar com teste que um novo job não é iniciado enquanto um está ativo
- [x] 2.3 Confirmar que a carga histórica (F5/Enter/período) continua podendo substituir um job ativo e que o balanceamento do item 1 mantém `_operacoes_ativas` consistente; verificar com teste de integração do controller com presenter real

## 3. Testes de regressão

- [x] 3.1 Adicionar teste em `tests/test_presentation/test_fundamental_job.py` cobrindo substituição de job: `on_fundamental_finished` é chamado para o substituído e, ao final do novo, `clear_wait_cursor`/`restore_all_buttons` são chamados
- [x] 3.2 Adicionar teste em `tests/test_presentation/test_presenter.py` verificando que `on_fundamental_started` desabilita controles e que a sequência started/finished mantém a invariante de contagem
- [x] 3.3 Adicionar teste de GUI (marcado com skip sem `DISPLAY`) verificando que o cursor do `Treeview` da tabela de Fundamentos volta ao valor original após o fluxo de substituição, seguindo o padrão de `tests/test_presentation/test_button_state.py`

## 4. Resiliência da drenagem do job fundamentalista

- [x] 4.1 Tratar exceções por mensagem em `_consumir_fila` (`controller_fundamental.py`), registrando no log via `LogEntry` e encerrando o job em mensagens terminais (`resultado`/`erro`), de modo que `on_fundamental_finished` sempre seja chamado; verificar com teste que um erro ao tratar o resultado ainda zera `_operacoes_ativas` e restaura o cursor
- [x] 4.2 Garantir que um erro ao tratar uma mensagem de progresso seja registrado e não interrompa o esvaziamento da fila; verificar com teste que o resultado seguinte ainda é processado
- [x] 4.3 Adicionar os cenários de falha ao delta de `loading-state-management` e atualizar `design.md`
- [x] 4.4 Envolver a chamada de `_consumir_fila` em `_drenar_fundamental` com guarda de exceção, garantindo encerramento do job mesmo em falhas fora do tratamento por mensagem; verificar com teste que a drenagem encerra o job
- [x] 4.5 Registrar no log exceções não tratadas em callbacks do Tk sobrescrevendo `report_callback_exception` em `FlowScopeGUI`, para diagnóstico da falha de renderização
- [x] 4.6 Remover o `on_operation_finished()` redundante do ramo `PortfolioNotFoundError` de `on_index_clicked`, que decrementava o contador duas vezes; verificar com teste que o erro de carteira não zera indevidamente o contador
- [x] 4.7 Adicionar watchdog de inatividade/liveness ao job fundamentalista (`_job_travado`): encerra o job e restaura cursor/controles quando a thread morre sem mensagem terminal ou fica mais de 120s sem progresso, registrando aviso no log; verificar com testes que ambos os casos encerram o job

## 5. Verificação final

- [x] 5.1 Rodar `make lint` e confirmar que `ruff` e `flake8` passam sem erros
- [x] 5.2 Rodar a suíte de testes (`make test` ou `pytest`) e confirmar que passa sem regressões
- [x] 5.3 Rodar `openspec validate "corrigir-cursor-fundamentos"` e confirmar que retorna `valid: true`
