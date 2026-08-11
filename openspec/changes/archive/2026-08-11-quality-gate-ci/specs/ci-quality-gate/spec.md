## ADDED Requirements

### Requirement: CI workflow reutilizavel via workflow_call

O workflow `ci.yml` DEVE ser invocavel como workflow reutilizavel por outros workflows do repositorio atraves do trigger `workflow_call`, alem dos triggers existentes `push` e `pull_request` para a branch `main`.

#### Scenario: CI executado por push na main
- **WHEN** um commit e pushed para a branch `main`
- **THEN** o workflow DEVE executar os jobs lint, test e quality-gate

#### Scenario: CI executado por pull request para main
- **WHEN** um pull request e aberto ou atualizado contra a branch `main`
- **THEN** o workflow DEVE executar os jobs lint, test e quality-gate

#### Scenario: CI invocado como workflow reutilizavel
- **WHEN** outro workflow (ex: `release.yml`) referencia `uses: ./.github/workflows/ci.yml`
- **THEN** o workflow DEVE executar os jobs lint, test e quality-gate e reportar falha se qualquer job falhar

### Requirement: Job de lint dedicado

O workflow DEVE conter um job `lint` que executa analise estatica de codigo usando ruff e flake8 em Python 3.12.

#### Scenario: Lint passa sem erros
- **WHEN** o job `lint` executa `make lint`
- **AND** nao ha violacoes de ruff nem flake8
- **THEN** o job DEVE completar com sucesso (exit 0)

#### Scenario: Lint falha com erros
- **WHEN** o job `lint` executa `make lint`
- **AND** ha violacoes de lint
- **THEN** o job DEVE falhar (exit 1)
- **AND** os jobs `test` e `quality-gate` NAO DEVEM executar

### Requirement: Job de teste com matrix Python 3.12 e 3.13

O workflow DEVE conter um job `test` que depende do job `lint` e executa `make test` em Python 3.12 e Python 3.13 via matrix strategy.

#### Scenario: Testes passam em todas as versoes
- **WHEN** o job `lint` completou com sucesso
- **AND** `make test` e executado em Python 3.12 e 3.13
- **THEN** ambos os jobs da matrix DEVEM completar com sucesso

#### Scenario: Testes falham em qualquer versao
- **WHEN** `make test` falha em Python 3.12 ou 3.13
- **THEN** o job `test` DEVE falhar
- **AND** o job `quality-gate` NAO DEVE executar

### Requirement: Job de quality gate com verificacoes completas

O workflow DEVE conter um job `quality-gate` que depende do job `test` e executa `make quality-gate` em Python 3.12 e 3.13 via matrix strategy, com cache de `.venv` baseado no hash do `pyproject.toml`.

#### Scenario: Quality gate completo passa
- **WHEN** o job `test` completou com sucesso
- **AND** `make quality-gate` e executado e todas as verificacoes passam (lint, complexidade, duplicacao, cobertura >= 85%, mutacao >= 80%, seguranca sem ERROR findings)
- **THEN** o job DEVE completar com sucesso

#### Scenario: Quality gate falha em verificacao de complexidade
- **WHEN** qualquer metrica de complexidade excede o threshold (ex: CC > 10, MI < 30)
- **THEN** `make quality-gate` DEVE retornar exit code nao-zero
- **AND** o job `quality-gate` DEVE falhar

#### Scenario: Quality gate falha em cobertura
- **WHEN** cobertura de testes e inferior a 85%
- **THEN** `make quality-gate` DEVE retornar exit code nao-zero
- **AND** o job `quality-gate` DEVE falhar

#### Scenario: Quality gate falha em seguranca
- **WHEN** semgrep encontra findings de severidade ERROR
- **THEN** `make quality-gate` DEVE retornar exit code nao-zero
- **AND** o job `quality-gate` DEVE falhar

#### Scenario: Quality gate com warnings nao bloqueia
- **WHEN** ha warnings (ex: duplicacao entre 7% e 10%, MI entre 30 e 70, WARNING findings do semgrep)
- **AND** nenhum threshold blocking e violado
- **THEN** `make quality-gate` DEVE retornar exit code zero

#### Scenario: Upload de artefatos no quality gate
- **WHEN** o job `quality-gate` executa (passando ou falhando)
- **THEN** o relatorio de cobertura (`coverage.xml`) DEVE ser uploaded como artifact nomeado `coverage-{python-version}`
- **AND** o relatorio de mutacao (`mutation_report.html`) DEVE ser uploaded como artifact nomeado `mutation-report-{python-version}`

### Requirement: Makefile com targets de qualidade

O projeto DEVE conter um Makefile com todos os targets de qualidade definidos na RFC-005, incluindo:

| Target | Descricao |
|--------|-----------|
| `venv` | Cria virtualenv |
| `install` | Instala o projeto em modo editavel |
| `install-quality-tools` | Instala dependencias do grupo `[quality]` + jscpd global via npm |
| `quality-gate` | Orchestrator: lint + complexity + duplication + test + mutation-check + security |
| `lint` | ruff check src/ + flake8 --select=B,A,D |
| `test` | pytest com --cov, --cov-report=xml, --cov-fail-under=85 |
| `complexity` | radon cc + complexity_metrics.py + xenon + lizard |
| `duplication` | jscpd com thresholds 10% (blocking) e 7% (warning) |
| `mutation-run` | mutmut run + export-cicd-stats |
| `mutation-check` | Verifica score de mutacao >= 80% |
| `mutation-stats` | Export stats + verificacao nao-bloqueante |
| `mutation-results` | Gera log de mutantes sobreviventes |
| `security` / `security-all` | semgrep scan com ERROR blocking e WARNING reportado |
| `security-changed` | semgrep ci apenas em src/ |

#### Scenario: Target quality-gate executa todas as verificacoes
- **WHEN** `make quality-gate` e executado
- **THEN** os targets `lint`, `complexity`, `duplication`, `test`, `mutation-check` e `security` DEVEM ser executados em sequencia

#### Scenario: Target build mantido como PyInstaller
- **WHEN** `make build` e executado
- **THEN** o comando DEVE instalar pyinstaller e executar `PyInstaller flowscope.spec`

### Requirement: Scripts de qualidade em scripts/

O projeto DEVE conter tres scripts Python auxiliares no diretorio `scripts/`:

#### Scenario: quality_gate.py executa e reporta todas as metricas
- **WHEN** `python scripts/quality_gate.py` e executado
- **THEN** o script DEVE executar cada check (lint, complexity, duplication, test, mutation, security)
- **AND** DEVE emitir um relatorio consolidado com status PASS/FAIL por metrica
- **AND** DEVE retornar exit code 0 se todos passarem, 1 se algum blocking falhar

#### Scenario: complexity_metrics.py implementa Contract 2 do MI
- **WHEN** `python scripts/complexity_metrics.py` e executado
- **THEN** DEVE calcular Maintainability Index via radon
- **AND** MI < 30 DEVE falhar com exit 1 (blocking)
- **AND** 30 <= MI < 70 DEVE passar com warning (exit 0)
- **AND** MI >= 70 DEVE passar (exit 0)
- **AND** MI unparseable (sem modulos) DEVE falhar com exit 1 (fail-loud)

#### Scenario: check-mutation-score.py verifica threshold de 80%
- **WHEN** `python scripts/check-mutation-score.py` e executado
- **AND** o arquivo `mutants/mutmut-cicd-stats.json` existe
- **THEN** DEVE calcular score = killed / (killed + survived + timeout + suspicious) * 100
- **AND** score >= 80% DEVE retornar exit 0
- **AND** score < 80% DEVE retornar exit 1

### Requirement: pyproject.toml com grupos dev e quality

O `pyproject.toml` DEVE conter:

- Grupo `[project.optional-dependencies] dev` expandido com: ruff, flake8, flake8-bugbear, flake8-annotations, flake8-docstrings, pytest, pytest-cov, responses
- Grupo `[project.optional-dependencies] quality` com: ruff, flake8, flake8-bugbear, flake8-annotations, flake8-docstrings, radon, xenon, lizard, pytest, pytest-cov, mutmut, semgrep
- Secao `[tool.ruff]` ou `[tool.ruff.lint]` com ignore de BLE001, S110, B008
- Secao `[tool.pytest.ini_options]` com `testpaths = ["tests"]` e markers para `slow`
- Secao `[tool.mutmut]` com `source_paths = ["src/"]`, runner = "pytest", paths a nao mutar e padroes
- Secao `[tool.coverage.run]` e `[tool.coverage.report]`
- Secao `[tool.coverage.run]` com `source = ["src"]` e `omit` para `src/flowscope/presentation/gui/*` e `src/flowscope/icons/*` (camada GUI tkinter/matplotlib nao e coberta por testes automatizados; o gate mede a cobertura do codigo de dominio, aplicacao e infraestrutura)
- Secao `[tool.coverage.report]` com `fail_under = 85`

#### Scenario: pip install -e ".[dev]" instala ferramentas de desenvolvimento
- **WHEN** `pip install -e ".[dev]"` e executado
- **THEN** ruff, flake8 com plugins, pytest, pytest-cov e responses DEVEM ser instalados

#### Scenario: pip install -e ".[quality]" instala ferramentas de qualidade
- **WHEN** `pip install -e ".[quality]"` e executado
- **THEN** todas as ferramentas do grupo dev MAIS radon, xenon, lizard, mutmut e semgrep DEVEM ser instalados

### Requirement: RFC-005 atualizada para refletir a realidade do codigo

O documento `docs/rfcs/RFC-005*.md` DEVE ser atualizado para:
- Corrigir a secao 4.2: target `build` do Makefile DEVE ser PyInstaller (`pyinstaller flowscope.spec`), nao wheel (`python -m build`)
- Remover todas as mencoes a `build-wheel.yml` (workflow nao sera criado)

#### Scenario: Secao 4.2 do Makefile reflete build como PyInstaller
- **WHEN** a RFC-005 e lida na secao 4.2 (Enhanced Makefile)
- **THEN** o target `build` DEVE conter `pip install -q pyinstaller` e `python -m PyInstaller flowscope.spec`

#### Scenario: RFC-005 nao menciona build-wheel.yml
- **WHEN** busca-se por `build-wheel.yml` no documento
- **THEN** nao DEVE haver ocorrencias do termo
