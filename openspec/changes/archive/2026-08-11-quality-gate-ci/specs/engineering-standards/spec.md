## MODIFIED Requirements

### Requirement: Quality gate obrigatorio em toda alteracao

Toda alteracao de codigo DEVE ser finalizada com a execucao do quality gate completo definido na RFC-005: (1) lint limpo sem erros nem warnings (ruff + flake8), (2) todos os testes existentes executando com sucesso com cobertura minima de 85%, (3) complexidade dentro dos thresholds (CC <= 10, MI >= 30), (4) duplicacao de codigo abaixo de 10%, e (5) nenhuma vulnerabilidade de seguranca de severidade ERROR detectada pelo semgrep.

#### Scenario: Lint falha bloqueia finalizacao
- **GIVEN** uma alteracao de codigo com erro de lint (ex: import nao utilizado, formato incorreto)
- **WHEN** a tarefa e finalizada sem corrigir o erro
- **THEN** isso DEVE ser considerado uma violacao do engineering standard
- **AND** a correcao DEVE ser aplicada antes do commit

#### Scenario: Teste falhando bloqueia finalizacao
- **GIVEN** uma alteracao de codigo com um teste existente falhando
- **WHEN** a tarefa e finalizada sem corrigir a falha
- **THEN** isso DEVE ser considerado uma violacao do engineering standard
- **AND** a correcao DEVE ser aplicada antes do commit

#### Scenario: Cobertura abaixo de 85% bloqueia finalizacao
- **GIVEN** uma alteracao de codigo que reduz a cobertura de testes para abaixo de 85%
- **WHEN** a tarefa e finalizada
- **THEN** isso DEVE ser considerado uma violacao do engineering standard
- **AND** testes adicionais DEVEM ser escritos para restaurar a cobertura minima

#### Scenario: Complexidade excessiva bloqueia finalizacao
- **GIVEN** uma alteracao que introduz funcao com cyclomatic complexity > 10 ou Maintainability Index < 30
- **WHEN** a tarefa e finalizada
- **THEN** isso DEVE ser considerado uma violacao do engineering standard
- **AND** o codigo DEVE ser refatorado para reduzir a complexidade

#### Scenario: Duplicacao excessiva bloqueia finalizacao
- **GIVEN** uma alteracao que introduz duplicacao de codigo acima de 10%
- **WHEN** a tarefa e finalizada
- **THEN** isso DEVE ser considerado uma violacao do engineering standard
- **AND** o codigo duplicado DEVE ser extraido para funcoes ou modulos compartilhados

#### Scenario: Vulnerabilidade de seguranca bloqueia finalizacao
- **GIVEN** uma alteracao que introduz vulnerabilidade detectada pelo semgrep com severidade ERROR
- **WHEN** a tarefa e finalizada
- **THEN** isso DEVE ser considerado uma violacao do engineering standard
- **AND** a vulnerabilidade DEVE ser corrigida antes do commit

#### Scenario: Quality gate completo permite finalizacao
- **GIVEN** uma alteracao de codigo sem erros de lint
- **AND** todos os testes existentes executam com sucesso com cobertura >= 85%
- **AND** complexidade dentro dos thresholds (CC <= 10, MI >= 30)
- **AND** duplicacao abaixo de 10%
- **AND** semgrep reporta zero findings ERROR
- **WHEN** a tarefa e finalizada
- **THEN** o quality gate DEVE ser considerado cumprido

### Requirement: Comando de verificacao

O comando `make quality-gate` DEVE ser usado como quality gate padrao, executando respectivamente lint (ruff + flake8), verificacao de complexidade (radon + xenon + lizard), verificacao de duplicacao (jscpd), testes com cobertura (pytest --cov-fail-under=85), verificacao de mutacao (mutmut, threshold 80%), e verificacao de seguranca (semgrep), conforme definido no Makefile do projeto e na RFC-005.

#### Scenario: Execucao do quality gate completo
- **WHEN** o usuario executa `make quality-gate` no diretorio raiz do projeto
- **THEN** o lint DEVE rodar com ruff e flake8 e retornar sem violacoes
- **AND** a complexidade DEVE ser verificada com radon, xenon e lizard
- **AND** a duplicacao DEVE ser verificada com jscpd
- **AND** os testes DEVM ser executados com pytest e cobertura >= 85%
- **AND** a mutacao DEVE ser verificada com score >= 80%
- **AND** a seguranca DEVE ser verificada com semgrep sem findings ERROR
