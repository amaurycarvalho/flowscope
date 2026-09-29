## ADDED Requirements

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
