## Purpose

Define the test coverage requirements for the presentation layer components introduced in the `refactor-loading-architecture` change, ensuring that orchestration logic, presenter formatting, and button state management are verified automatically.

## Requirements

### Requirement: Controller orchestration logic tested

O sistema DEVE ter testes unitários para `FlowScopeController.on_index_clicked()` e `on_load_data()` que verifiquem: (a) a sequência correta de chamadas ao presenter, (b) criação e gerenciamento de fases do ProgressReporter, (c) tratamento de erros (PortfolioNotFoundError, exceções genéricas), (d) proteção do OperationGuard (segundo clique ignorado).

#### Scenario: on_index_clicked chama presenter na ordem correta

- **WHEN** `on_index_clicked("IBOV")` é chamado com guard livre
- **THEN** o presenter DEVE receber `on_operation_started()`, `on_portfolio_loaded()`, `on_result()`, e `on_operation_finished()` nesta ordem

#### Scenario: on_index_clicked ignora segundo clique

- **WHEN** `on_index_clicked("IBOV")` está em execução e um segundo `on_index_clicked("IFIX")` é chamado
- **THEN** o segundo clique DEVE ser ignorado (guard.acquire retorna False, presenter não recebe chamadas)

#### Scenario: on_index_clicked trata exceção com on_error

- **WHEN** `LoadIndexPortfolioUseCase.execute()` lança uma exceção
- **THEN** o presenter DEVE receber `on_error()` e `on_operation_finished()`

### Requirement: Progress callback wrapping testado

O método `_make_progress_cb()` DEVE ter teste que verifique: (a) advance é chamado quando `failed=False`, (b) fail é chamado quando `failed=True`.

#### Scenario: _make_progress_cb chama advance no sucesso

- **WHEN** o callback gerado é invocado com `("detail", False)`
- **THEN** `reporter.advance(1, "detail")` DEVE ser chamado

#### Scenario: _make_progress_cb chama fail no erro

- **WHEN** o callback gerado é invocado com `("detail", True)`
- **THEN** `reporter.fail(1, "detail")` DEVE ser chamado

### Requirement: Presenter com interface destacável

O `FlowScopePresenter` DEVE depender de um protocolo `GUIView` em vez da classe concreta `FlowScopeGUI`, permitindo que seus métodos sejam testados com mocks.

#### Scenario: Presenter testado com mock de GUIView

- **WHEN** `on_operation_started()` é chamado com um mock de GUIView
- **THEN** O mock DEVE registrar chamadas para `disable_all_buttons()` e `set_wait_cursor()`

#### Scenario: on_result formata dados corretamente

- **WHEN** `on_result(result, tickers, ref_date)` é chamado
- **THEN** O mock DEVE registrar chamadas para `set_tickers()`, `set_counter()`, `config(state=NORMAL)` no copy button, e `set_status()`

### Requirement: Button state management testado

Os métodos `_disable_all_buttons()` e `_restore_all_buttons()` do `FlowScopeGUI` DEVEM ter testes que verifiquem: (a) snapshot de estados é salvo, (b) todos os botões são desabilitados, (c) estados são restaurados corretamente.

#### Scenario: disable salva estados e desabilita

- **WHEN** `_disable_all_buttons()` é chamado
- **THEN** todos os botões DEVEM estar com state=DISABLED e o dict `_button_states` DEVE conter os estados anteriores

#### Scenario: restore retorna ao estado anterior

- **WHEN** `_restore_all_buttons()` é chamado após `_disable_all_buttons()`
- **THEN** cada botão DEVE retornar ao state que tinha antes do disable

### Requirement: Cobertura mínima nos novos componentes da application layer

O `LoadIndexPortfolioUseCase` DEVE ter teste que verifique o repasse do `progress_callback` para o repositório. O `OperationGuard` DEVE ter teste para a propriedade `is_busy`.

#### Scenario: LoadIndexPortfolioUseCase repassa progress_callback

- **WHEN** `execute("IBOV", progress_callback=cb)` é chamado
- **THEN** O repositório mock DEVE receber o mesmo `cb` como parâmetro

#### Scenario: OperationGuard.is_busy reflete estado

- **WHEN** guard está adquirido
- **THEN** `is_busy` DEVE retornar True
- **WHEN** guard é liberado
- **THEN** `is_busy` DEVE retornar False
