## REMOVED Requirements

### Requirement: Controller orchestration logic tested

**Reason**: A orquestração da carga deixa de rodar de forma síncrona na thread do Tk. O `ProgressReporter` e suas fases migram para o worker, o `OperationGuard` é estreitado ao setup síncrono e a segunda requisição de carga passa a substituir a anterior (supersede) em vez de ser ignorada. O requisito antigo descrevia o modelo síncrono.

**Migration**: Substituído por "Orquestração da carga testada headless", que cobre submissão por eventos, supersede/reentrada e tratamento de erro sem exigir interface gráfica.

## ADDED Requirements

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
