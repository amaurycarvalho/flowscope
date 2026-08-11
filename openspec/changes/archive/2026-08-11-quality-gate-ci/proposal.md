## Why

A RFC-005 definiu um quality gate abrangente (lint, complexidade, duplicacao, cobertura, mutacao, seguranca) para codigo gerado por IA, mas ele nunca foi implementado. Alem disso, o workflow de release (`release.yml`) publica binarios para 3 plataformas sem nenhuma validacao previa de qualidade — o build acontece as cegas, independente do estado do codigo. Implementar o gate e acopla-lo ao pipeline de release garante que nenhum binario seja distribuido sem passar pelas verificacoes definidas na RFC.

## What Changes

- **ci.yml**: Reescrever como workflow reutilizavel (`workflow_call`) com 3 jobs encadeados (lint → test → quality-gate), usando Python 3.12 e 3.13, conforme especificado na RFC-005
- **release.yml**: Adicionar job `ci` que invoca o workflow reutilizavel `ci.yml` antes do build; jobs `build` e `release` passam a depender de `ci`
- **Makefile**: Transformacao completa com 30+ targets: `venv`, `install-quality-tools`, `quality-gate`, `complexity`, `duplication`, `mutation-run`, `mutation-check`, `mutation-stats`, `mutation-results`, `security`, `security-all`, `security-changed`
- **pyproject.toml**: Adicionar dependencias `dev` (ruff, flake8, flake8-bugbear, flake8-annotations, flake8-docstrings, pytest-cov) e `quality` (radon, xenon, lizard, mutmut, semgrep); configurar `[tool.ruff]`, `[tool.pytest.ini_options]`, `[tool.mutmut]`, `[tool.coverage]`
- **Novos scripts**: `scripts/quality_gate.py`, `scripts/complexity_metrics.py`, `scripts/check-mutation-score.py`
- **RFC-005**: Corrigir secao 4.2: redefinir target `build` do Makefile para PyInstaller (nao wheel); remover mencões a `build-wheel.yml` (nao sera criado)
- **`.gitignore`**: Adicionar entradas para `mutants/` e `.mutmut-cache`

## Capabilities

### New Capabilities

- `ci-quality-gate`: Infraestrutura de CI reutilizavel com quality gate completo (lint, complexidade, duplicacao, cobertura, mutacao, seguranca) executando em Python 3.12 e 3.13, exposta via `workflow_call` para ser invocada por outros workflows
- `release-quality-gate`: Workflow de release com gate obrigatorio — `ci.yml` deve passar antes que builds de plataforma e publicacao de release sejam iniciados

### Modified Capabilities

- `engineering-standards`: Expandir o quality gate de `make lint test` (ruff + pytest) para o conjunto completo de verificacoes da RFC-005 (complexidade, duplicacao, cobertura minima 85%, mutacao minima 80%, seguranca semgrep), refletindo os novos thresholds e ferramentas

## Impact

- **`.github/workflows/ci.yml`**: Reescrita completa (workflow reutilizavel, 3 jobs, Python 3.12/3.13)
- **`.github/workflows/release.yml`**: Novo job `ci` + dependencia nos jobs `build`/`release`
- **`Makefile`**: ~30 novos targets de qualidade; target `build` mantido como PyInstaller
- **`pyproject.toml`**: Grupos `dev` e `quality` expandidos, novas secoes `[tool.*]`
- **`scripts/`**: 3 novos scripts Python
- **`docs/rfcs/RFC-005*.md`**: Correcoes pontuais (Makefile build + remocao build-wheel.yml)
- **`docs/adrs/ADR-003.md`**: Novo ADR documentando a decisao arquitetonica
