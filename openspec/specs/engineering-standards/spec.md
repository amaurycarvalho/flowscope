## Purpose

Define engineering standards and quality gates that apply to all code changes in FlowScope, ensuring consistency, reliability, and maintainability across the project.

## Requirements

### Requirement: Verificação mínima automática por alteração

Toda alteração de código DEVE ser finalizada com a execução automática de, no mínimo: (1) o lint limpo sem erros nem warnings (`make lint`), (2) a verificação de complexidade dentro dos thresholds (`make complexity`, CC <= 10 e MI >= 30) e (3) os testes relacionados ou impactados pela mudança. A suíte de testes completa e o quality gate completo NÃO DEVEM ser executados automaticamente em toda alteração.

#### Scenario: Lint automático em toda alteração
- **GIVEN** uma alteração de código
- **WHEN** a implementação é concluída
- **THEN** `make lint` DEVE ser executado automaticamente
- **AND** erros de lint DEVEM ser corrigidos antes de finalizar

#### Scenario: Complexidade automática em toda alteração
- **GIVEN** uma alteração de código
- **WHEN** a implementação é concluída
- **THEN** `make complexity` DEVE ser executado automaticamente (CC <= 10, MI >= 30)

#### Scenario: Testes relacionados ou impactados são automáticos
- **GIVEN** uma alteração de código
- **WHEN** a implementação é concluída
- **THEN** os testes relacionados ou impactados pela mudança DEVEM ser executados automaticamente
- **AND** falhas nesses testes DEVEM ser corrigidas antes de finalizar

#### Scenario: Suíte completa não é executada por padrão
- **GIVEN** uma alteração localizada
- **WHEN** a implementação é concluída
- **THEN** a suíte de testes completa NÃO DEVE ser executada automaticamente
- **AND** o quality gate completo NÃO DEVE ser executado automaticamente

### Requirement: Quality gate completo apenas quando estritamente necessário

A suíte de testes completa e o quality gate completo (`make test`, `make quality-gate`) DEVEM ser executados apenas quando estritamente necessário — tipicamente mudanças amplas: refatorações transversais, alterações de contrato compartilhado, mudanças de dependências/empacotamento, de infraestrutura de CI ou de cobertura. Incluir essa execução como task de uma change DEVE requerer autorização explícita do usuário. Quando a motivação for apenas precaução ("nice to have"), a execução DEVE figurar como task manual do usuário, e NÃO como task executada pelo agente.

#### Scenario: Mudança ampla exige autorização para entrar nas tasks
- **GIVEN** uma change que altera contratos compartilhados ou infraestrutura
- **WHEN** o agente propõe incluir a execução do quality gate completo como task
- **THEN** a inclusão DEVE depender de autorização explícita do usuário
- **AND** sem autorização a task NÃO DEVE ser incluída nem executada automaticamente

#### Scenario: Execução por precaução é task manual do usuário
- **GIVEN** uma mudança localizada em que rodar o gate completo seria apenas precaução ("nice to have")
- **WHEN** as tasks da change são montadas
- **THEN** a execução DEVE figurar como task manual do usuário, marcada para execução humana
- **AND** o agente NÃO DEVE executá-la automaticamente

#### Scenario: Quality gate completo executado sob demanda
- **GIVEN** autorização explícita (ou CI) para a mudança ampla
- **WHEN** `make quality-gate` é executado no diretório raiz
- **THEN** lint, complexidade, duplicação, testes com cobertura >= 85%, mutação >= 80% e segurança sem findings ERROR DEVEM ser verificados
- **AND** os thresholds de bloqueio DEVEM ser respeitados

### Requirement: Validação OpenSpec em português (não-strict)

Por decisão de documentação em língua nativa, as specs do projeto DEVEM ser escritas em português, usando "DEVE" como termo normativo em vez de SHALL/MUST. O warning de RFC 2119 do OpenSpec ("should contain SHALL or MUST") DEVE ser ignorado nesse projeto, e a validação de changes DEVE ser considerada satisfatória quando executada sem `--strict`.

#### Scenario: Specs em português com "DEVE"
- **GIVEN** uma spec do projeto redigida em português e usando "DEVE" como termo normativo
- **WHEN** a spec é validada com OpenSpec
- **THEN** o warning "should contain SHALL or MUST" NÃO DEVE ser tratado como falha
- **AND** a validação sem `--strict` DEVE ser considerada suficiente

#### Scenario: Validação com --strict reporta apenas o warning RFC 2119
- **GIVEN** uma change cujo único apontamento é o warning RFC 2119 por usar "DEVE"
- **WHEN** a change é validada com `openspec validate --strict`
- **THEN** o resultado DEVE ser aceito como equivalente à validação não-strict
- **AND** nenhuma reescrita para SHALL/MUST DEVE ser exigida

### Requirement: Referências de caminho portáveis

O código, os testes, os scripts e a documentação DEVEM referenciar arquivos do projeto por caminhos relativos à raiz do repositório, ou resolvidos a partir de `__file__`/configuração em tempo de execução. Caminhos absolutos específicos da máquina NÃO DEVEM ser embutidos em referências a arquivos do projeto. Ferramentas de desenvolvimento e agentes que acessam os arquivos do projeto DEVEM usar caminhos relativos à raiz do repositório.

#### Scenario: Código referencia arquivo do projeto por caminho relativo
- **WHEN** um módulo, teste ou script referencia um arquivo do projeto
- **THEN** a referência DEVE ser relativa à raiz do repositório ou derivada de `__file__`/configuração, sem embutir caminho absoluto da máquina

#### Scenario: Caminho absoluto específico da máquina é rejeitado
- **WHEN** uma referência a arquivo do projeto contém um caminho absoluto específico da máquina
- **THEN** isso DEVE ser considerado uma violação do engineering standard
- **AND** a referência DEVE ser convertida para caminho relativo à raiz

#### Scenario: Ferramenta ou agente acessa arquivos do projeto
- **WHEN** uma ferramenta de desenvolvimento ou um agente acessa arquivos do projeto
- **THEN** ela DEVE usar caminhos relativos à raiz do repositório
