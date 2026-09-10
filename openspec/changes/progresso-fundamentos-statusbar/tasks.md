## 1. Mensagem do job com progresso

- [x] 1.1 Incluir `current`/`total` na mensagem `MENSAGEM_PROGRESSO` do `FundamentalJob` (contador interno e `total = len(tickers)`); verificar com teste que a fila contém as mensagens com `current` crescente e `total` correto
- [x] 1.2 Garantir compatibilidade: o consumo deve tolerar mensagens no formato antigo sem `current`/`total`; verificar com teste que uma mensagem antiga não quebra o controller

## 2. Controller: consumir progresso e estado inicial

- [x] 2.1 Em `_drenar_fundamental`, repassar `current`/`total` ao presenter ao receber progresso; verificar com teste que `on_fundamental_progress` é chamado com os valores
- [x] 2.2 Em `_iniciar_analise_fundamental`, emitir um estado inicial `0/N` (`on_progress`) ao iniciar o job; verificar com teste que a barra é inicializada em 0
- [x] 2.3 Em `on_operation_finished`, limpar a barra apenas quando `_operacoes_ativas == 0`, para não escondê-la durante a fase fundamental; verificar com teste que a barra não é limpa com operação fundamental ativa

## 3. Presenter e marcador de status

- [x] 3.1 Alterar `on_fundamental_progress` para chamar `set_progress(current, total, label)` com o marcador `•` no lugar do `ℹ`; verificar com teste que `set_progress` é chamado com o rótulo esperado
- [x] 3.2 Manter os ícones de desfecho `✓`/`⚠`; verificar com teste que as mensagens de desfecho não mudam

## 4. Cursor de espera em todos os widgets

- [x] 4.1 Fazer `_set_wait_cursor`/`_clear_wait_cursor` percorrerem a árvore de widgets, guardando e restaurando o cursor de cada um (com guarda de reentrância e tolerância a `tk.TclError`); verificar com teste que um widget com cursor próprio (`hand2`) vira `watch` durante a operação e volta a `hand2` depois

## 5. Verificação final

- [x] 5.1 Atualizar os testes afetados (`test_fundamental_job.py`, `test_controller.py`, `test_presenter.py`, `test_button_state.py`) e rodar lint e a suíte completa; verificar que passam sem erros
- [x] 5.2 Rodar `openspec validate "progresso-fundamentos-statusbar"`; verificar que retorna `valid: true` sem erros

## 6. Controles desabilitados durante a fundamental

- [x] 6.1 Fazer `on_operation_finished`/`on_fundamental_finished` restaurarem os controles apenas quando `_operacoes_ativas == 0` e tornar `_disable_all_buttons` idempotente; verificar com teste que os controles seguem desabilitados durante a análise e voltam ao estado original ao final, inclusive em operação sobreposta
- [x] 6.2 Rodar lint, a suíte completa e `openspec validate "progresso-fundamentos-statusbar"`; verificar que passam sem erros
