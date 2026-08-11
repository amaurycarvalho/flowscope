## Purpose

Define engineering standards and quality gates that apply to all code changes in FlowScope, ensuring consistency, reliability, and maintainability across the project.

## Requirements

### Requirement: Quality gate obrigatório em toda alteração

Toda alteração de código DEVE ser finalizada com a execução do quality gate completo definido na RFC-005: (1) lint limpo sem erros nem warnings (ruff + flake8), (2) todos os testes existentes executando com sucesso com cobertura mínima de 85%, (3) complexidade dentro dos thresholds (CC <= 10, MI >= 30), (4) duplicação de código abaixo de 10%, e (5) nenhuma vulnerabilidade de segurança de severidade ERROR detectada pelo semgrep.

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

#### Scenario: Cobertura abaixo de 85% bloqueia finalização
- **GIVEN** uma alteração de código que reduz a cobertura de testes para abaixo de 85%
- **WHEN** a tarefa é finalizada
- **THEN** isso DEVE ser considerado uma violação do engineering standard
- **AND** testes adicionais DEVEM ser escritos para restaurar a cobertura mínima

#### Scenario: Complexidade excessiva bloqueia finalização
- **GIVEN** uma alteração que introduz função com cyclomatic complexity > 10 ou Maintainability Index < 30
- **WHEN** a tarefa é finalizada
- **THEN** isso DEVE ser considerado uma violação do engineering standard
- **AND** o código DEVE ser refatorado para reduzir a complexidade

#### Scenario: Duplicação excessiva bloqueia finalização
- **GIVEN** uma alteração que introduz duplicação de código acima de 10%
- **WHEN** a tarefa é finalizada
- **THEN** isso DEVE ser considerado uma violação do engineering standard
- **AND** o código duplicado DEVE ser extraído para funções ou módulos compartilhados

#### Scenario: Vulnerabilidade de segurança bloqueia finalização
- **GIVEN** uma alteração que introduz vulnerabilidade detectada pelo semgrep com severidade ERROR
- **WHEN** a tarefa é finalizada
- **THEN** isso DEVE ser considerado uma violação do engineering standard
- **AND** a vulnerabilidade DEVE ser corrigida antes do commit

#### Scenario: Quality gate completo permite finalização
- **GIVEN** uma alteração de código sem erros de lint
- **AND** todos os testes existentes executam com sucesso com cobertura >= 85%
- **AND** complexidade dentro dos thresholds (CC <= 10, MI >= 30)
- **AND** duplicação abaixo de 10%
- **AND** semgrep reporta zero findings ERROR
- **WHEN** a tarefa é finalizada
- **THEN** o quality gate DEVE ser considerado cumprido

### Requirement: Comando de verificação

O comando `make quality-gate` DEVE ser usado como quality gate padrão, executando respectivamente lint (ruff + flake8), verificação de complexidade (radon + xenon + lizard), verificação de duplicação (jscpd), testes com cobertura (pytest --cov-fail-under=85), verificação de mutação (mutmut, threshold 80%), e verificação de segurança (semgrep), conforme definido no Makefile do projeto e na RFC-005.

#### Scenario: Execução do quality gate completo
- **WHEN** o usuário executa `make quality-gate` no diretório raiz do projeto
- **THEN** o lint DEVE rodar com ruff e flake8 e retornar sem violações
- **AND** a complexidade DEVE ser verificada com radon, xenon e lizard
- **AND** a duplicação DEVE ser verificada com jscpd
- **AND** os testes DEVEM ser executados com pytest e cobertura >= 85%
- **AND** a mutação DEVE ser verificada com score >= 80%
- **AND** a segurança DEVE ser verificada com semgrep sem findings ERROR
