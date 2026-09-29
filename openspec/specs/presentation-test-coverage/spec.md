## Purpose

Define the test coverage requirements for the presentation layer components introduced in the `refactor-loading-architecture` change, ensuring that orchestration logic, presenter formatting, and button state management are verified automatically.

## Requirements

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

### Requirement: Orquestração da carga testada headless

O sistema DEVE ter testes headless (sem `DISPLAY` e sem `tk.Tk`) para `FlowScopeController.on_index_clicked()` e `on_load_data()` e para a submissão da carga de portfólio de `on_ticker_edit()` que verifiquem: (a) a submissão do trabalho ao manager no grupo de carga; (b) a sequência de chamadas ao presenter ao consumir os eventos (`on_operation_started()`, `on_portfolio_loaded()`, `on_result()`, `on_operation_finished()`); (c) o tratamento de erros (`PortfolioNotFoundError` e exceções genéricas); (d) a distinção entre reentrada do mesmo acionamento (ignorada por `key`) e nova operação de carga (supersede). O gerenciamento de fases do `ProgressReporter` DEVE ser verificado no worker, não na thread do Tk.

#### Scenario: on_index_clicked submete a carga ao manager

- **WHEN** `on_index_clicked("IBOV")` é chamado com guard livre
- **THEN** o trabalho DEVE ser submetido ao grupo de carga e o resultado, ao ser consumido por evento, DEVE passar pelo presenter na ordem `on_operation_started()`, `on_portfolio_loaded()`, `on_result()`, `on_operation_finished()`

#### Scenario: Requisição idêntica é ignorada

- **WHEN** uma carga está ativa e o mesmo acionamento é repetido com a mesma `key`
- **THEN** a nova submissão DEVE ser descartada, sem reiniciar o job ativo

#### Scenario: Nova operação de carga substitui a anterior

- **WHEN** uma carga está ativa e um acionamento distinto (outro índice, período ou amostragem) é feito
- **THEN** a carga anterior DEVE ser cancelada e a nova DEVE assumir, sem que a interface seja restaurada entre as duas

#### Scenario: on_index_clicked trata exceção com on_error

- **WHEN** `LoadIndexPortfolioUseCase.execute()` lança uma exceção
- **THEN** o presenter DEVE receber `on_error()` e `on_operation_finished()`

#### Scenario: Fases do progresso testadas no worker

- **WHEN** o trabalho de carga executa
- **THEN** a criação e o avanço das fases do `ProgressReporter` DEVEM ser verificados no worker, sem interface gráfica

### Requirement: Processamento verificado sem interface gráfica

O processamento dos fluxos de apresentação — submissão e ciclo de vida de jobs, orquestração da carga, leitura de catálogo/séries, cancelamento e supersede — DEVE ser verificado por testes headless, sem `DISPLAY` e sem instanciar Tk. Ficam sob teste de UI apenas wiring, estado de widget/botão, empty-state e o marshaling real de eventos até o widget.

#### Scenario: Teste de processamento não exige display

- **WHEN** um teste cobre submissão de job, política de agendamento, cancelamento, supersede ou leitura de catálogo/séries
- **THEN** ele DEVE rodar sem a variável de ambiente `DISPLAY` e sem criar uma janela Tk

#### Scenario: Teste de UI limitado ao que só existe com Tk

- **WHEN** um teste exige interface gráfica
- **THEN** ele DEVE verificar apenas wiring de callback, estado visual/empty-state ou o marshaling de eventos até o widget

#### Scenario: Lógica de aplicação testada na camada de aplicação

- **WHEN** um teste cobre lógica pura de `application`/`domain` (ex.: extração de texto de documento)
- **THEN** ele DEVE residir em `tests/test_application`/`tests/test_domain` e NÃO DEVE estar sob `tests/test_presentation`
