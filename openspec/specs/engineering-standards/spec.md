## Purpose

Define engineering standards and quality gates that apply to all code changes in FlowScope, ensuring consistency, reliability, and maintainability across the project.

## Requirements

### Requirement: Quality gate obrigatório em toda alteração

Toda alteração de código DEVE ser finalizada com (1) lint limpo sem erros nem warnings e (2) todos os testes existentes executando com sucesso, antes de qualquer commit ou finalização da tarefa.

#### Scenario: Lint falha bloqueia finalização
- **GIVEN** uma alteração de código com erro de lint (ex: import não utilizado, formato incorreto)
- **WHEN** a tarefa é finalizada sem corrigir o erro
- **THEN** isso DEVE ser considerado uma violação do engineering standard
- **AND** a correção DEVE ser aplicada antes do commit

#### Scenario: Teste falhando bloqueia finalização
- **GIVEN** uma alteração de código com um teste existente falhando
- **WHEN** a tarefa é finalizada sem corrigir a falha
- **THEN** isso DEVE ser considerado uma violação do engineering standard
- **AND** a correção DEVE ser aplicada antes do commit

#### Scenario: Lint e teste limpos permitem finalização
- **GIVEN** uma alteração de código sem erros de lint
- **AND** todos os testes existentes executam com sucesso
- **WHEN** a tarefa é finalizada
- **THEN** o quality gate DEVE ser considerado cumprido

### Requirement: Comando de verificação

O comando `make lint test` DEVE ser usado como quality gate padrão, executando respectivamente `ruff check` e `pytest` conforme definido no Makefile do projeto.

#### Scenario: Execução do quality gate
- **WHEN** o usuário executa `make lint test` no diretório raiz do projeto
- **THEN** o lint DEVE rodar com ruff e retornar "All checks passed!"
- **AND** os testes DEVM ser executados com pytest e todos passarem
