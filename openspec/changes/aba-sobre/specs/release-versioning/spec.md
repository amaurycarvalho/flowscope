## Purpose

Expõe a data de lançamento da versão corrente do FlowScope e garante que o fluxo de release a mantenha atualizada junto da versão.

## ADDED Requirements

### Requirement: Constante de data de lançamento

O pacote `flowscope` DEVE expor `__release_date__` em `src/flowscope/__init__.py`, no formato ISO `YYYY-MM-DD`, correspondente à data do lançamento da `__version__` corrente.

#### Scenario: Constante disponível

- **WHEN** o módulo `flowscope` é importado
- **THEN** `__release_date__` DEVE estar disponível no formato ISO `YYYY-MM-DD`

#### Scenario: Data da versão corrente

- **WHEN** `__version__` é "1.1.0"
- **THEN** `__release_date__` DEVE ser "2026-09-18"

### Requirement: Atualização coordenada da data de lançamento

O fluxo de release DEVE atualizar `__release_date__` junto de `__version__`, de modo que a data corresponda ao lançamento corrente e permaneça consistente com o cabeçalho de release do `CHANGELOG.md`.

#### Scenario: Nova versão atualiza a data

- **WHEN** o fluxo de release define uma nova versão
- **THEN** `__release_date__` DEVE ser atualizada para a data do lançamento

#### Scenario: Consistência com o changelog

- **WHEN** a versão e a data são verificadas
- **THEN** elas DEVEM ser consistentes com o cabeçalho de release correspondente no `CHANGELOG.md`
