## 1. pyproject.toml — Dependencias e configuracoes de ferramentas

- [ ] 1.1 Expandir grupo `[project.optional-dependencies] dev` com ruff, flake8, flake8-bugbear, flake8-annotations, flake8-docstrings, pytest-cov
- [ ] 1.2 Criar grupo `[project.optional-dependencies] quality` com todas as ferramentas: ruff, flake8, flake8-bugbear, flake8-annotations, flake8-docstrings, radon, xenon, lizard, pytest, pytest-cov, mutmut, semgrep
- [ ] 1.3 Adicionar `[tool.ruff.lint]` com ignore de BLE001, S110, B008
- [ ] 1.4 Adicionar `[tool.pytest.ini_options]` com `testpaths = ["tests"]`, markers para `slow` e `addopts = ["-m", "not slow"]`
- [ ] 1.5 Adicionar `[tool.mutmut]` com `source_paths`, `runner`, `do_not_mutate`, `do_not_mutate_patterns`, timeouts e pytest CLI args conforme RFC-005 secao 4.4
- [ ] 1.6 Adicionar `[tool.coverage.run]` com `source = ["src"]` e `[tool.coverage.report]` com `fail_under = 85`

## 2. .gitignore — Entradas para mutation testing

- [ ] 2.1 Adicionar `mutants/` ao `.gitignore`
- [ ] 2.2 Adicionar `.mutmut-cache` ao `.gitignore`
- [ ] 2.3 Adicionar excecao `!mutants/mutmut-cicd-stats.json` (necessario para CI ler o stats exportado)

## 3. Makefile — Transformacao completa com targets de qualidade

- [ ] 3.1 Adicionar target `venv` que cria virtualenv com `python3 -m venv $(VENV)`
- [ ] 3.2 Refatorar target `install` para usar dependencia `$(ACTIVATE)` como gate do venv
- [ ] 3.3 Adicionar target `install-quality-tools`: `pip install -e ".[quality]"` + `npm install -g jscpd@4.0.1` + `mkdir -p mutants/`
- [ ] 3.4 Adicionar target `quality-gate` (orchestrator): `lint` + `complexity` + `duplication` + `test` + `mutation-check` + `security`
- [ ] 3.5 Expandir target `lint`: `ruff check src/` + `flake8 --max-complexity=10 --select=B,A,D --extend-exclude=tests ./src/`
- [ ] 3.6 Expandir target `test`: adicionar `--cov`, `--cov-report=xml:coverage.xml`, `--cov-report=term-missing`, `--cov-fail-under=85`
- [ ] 3.7 Adicionar target `complexity`: `radon cc` + `scripts/complexity_metrics.py` + `xenon` + `lizard` com exclusoes de tests, build, dist, ccache, mutants, .venv, .opencode
- [ ] 3.8 Adicionar target `duplication`: `jscpd` com thresholds 10% (blocking, exit 1) e 7% (warning, exit 0), ignorando tests, .venv, build, dist, __pycache__, mutants, .opencode
- [ ] 3.9 Adicionar target `mutation-run`: `mutmut run` + `mutation-stats`
- [ ] 3.10 Adicionar target `mutation-stats`: `mutmut export-cicd-stats` + `scripts/check-mutation-score.py` com `|| exit 0` (nao bloqueante)
- [ ] 3.11 Adicionar target `mutation-check`: `scripts/check-mutation-score.py` (bloqueante, exit 1 se score < 80%)
- [ ] 3.12 Adicionar target `mutation-results`: gera `mutants/mutmut-cicd-results.log` com sobreviventes
- [ ] 3.13 Adicionar target `security` (alias para `security-all`)
- [ ] 3.14 Adicionar target `security-all`: `semgrep scan --severity ERROR --error` (blocking) + report de WARNING findings (non-blocking)
- [ ] 3.15 Adicionar target `security-changed`: `semgrep ci --oss-only --quiet --config auto --include "src/"`
- [ ] 3.16 Manter target `build` como PyInstaller: `pip install -q pyinstaller` + `python -m PyInstaller flowscope.spec` (inalterado)

## 4. Scripts Python — Ferramentas auxiliares de quality gate

- [ ] 4.1 Criar `scripts/quality_gate.py`: classe `QualityGate` que executa cada check via subprocess, registra metricas com severity/status/evidence, emite relatorio consolidado e JSON, retorna exit 0/1
- [ ] 4.2 Criar `scripts/complexity_metrics.py`: executa `radon mi` e `radon hal`, implementa Contract 2 (MI < 30 blocking exit 1, 30-70 warning exit 0, >= 70 pass exit 0, unparseable fail-loud exit 1), reporta Halstead como informativo
- [ ] 4.3 Criar `scripts/check-mutation-score.py`: le `mutants/mutmut-cicd-stats.json`, calcula score = killed/(killed+survived+timeout+suspicious)*100, exit 0 se >= 80%, exit 1 se < 80%

## 5. .github/workflows/ci.yml — Workflow reutilizavel com quality gate

- [ ] 5.1 Adicionar `workflow_call` ao trigger `on` alem de `push` e `pull_request`
- [ ] 5.2 Substituir job unico `lint_and_test` por job `lint` (Python 3.12, `make lint`)
- [ ] 5.3 Adicionar job `test` (Python 3.12 + 3.13 matrix, `needs: lint`, `make test`)
- [ ] 5.4 Adicionar job `quality-gate` (Python 3.12 + 3.13 matrix, `needs: test`, `make install-quality-tools` + `make quality-gate`)
- [ ] 5.5 Adicionar cache de `.venv` no job `quality-gate` com key baseada em `pyproject.toml`
- [ ] 5.6 Adicionar upload de artefatos: `coverage.xml` e `mutation_report.html` por Python version

## 6. .github/workflows/release.yml — Gate de CI antes do build

- [ ] 6.1 Adicionar job `ci` que invoca `uses: ./.github/workflows/ci.yml` (workflow_call)
- [ ] 6.2 Adicionar `needs: ci` ao job `build` existente (matrix linux, windows, macos)
- [ ] 6.3 Garantir que `permissions: contents: read` e `contents: write` no job `release` estao mantidos

## 7. docs/rfcs/RFC-005 — Correcoes no documento de design

- [ ] 7.1 Corrigir secao 4.2: substituir target `build` do Makefile para usar PyInstaller (`pip install -q pyinstaller` + `python -m PyInstaller flowscope.spec`) em vez de `python -m build`
- [ ] 7.2 Remover todas as mencoes e o diagrama de `build-wheel.yml` da secao 3.3 e secao 4.1

## 8. docs/adrs/ADR-003.md — Documento de decisao arquitetonica

- [ ] 8.1 Criar `docs/adrs/ADR-003.md` documentando a decisao de implementar o quality gate da RFC-005, com workflow `ci.yml` reutilizavel e `release.yml` gated por CI, incluindo contexto, decisoes, alternativas consideradas e consequencias

## 9. Verificacao e correcoes

- [ ] 9.1 Executar `make lint` e corrigir todos os erros de ruff e flake8 (ambos devem passar limpos)
- [ ] 9.2 Executar `make test` e garantir cobertura >= 85%; adicionar testes se necessario
- [ ] 9.3 Executar `make complexity` e corrigir violacoes (CC > 10, MI < 30, lizard warnings)
- [ ] 9.4 Executar `make duplication` e corrigir duplicacao > 10%
- [ ] 9.5 Executar `make security-all` e corrigir ERROR findings do semgrep
- [ ] 9.6 Executar `make quality-gate` e garantir que o gate completo passa com exit 0
