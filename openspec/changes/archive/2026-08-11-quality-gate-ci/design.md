## Context

Atualmente o projeto FlowScope possui:
- **ci.yml**: Workflow simples com um unico job (`lint_and_test`) que roda `make lint test` em Python 3.10, disparado apenas por push/PR em `main`
- **release.yml**: Workflow que faz build PyInstaller para 3 plataformas e publica release no GitHub, sem nenhuma validacao de qualidade previa
- **Makefile**: 5 targets basicos (`install`, `build`, `test`, `lint`, `clean`)
- **RFC-005**: Documento de design que especifica um quality gate abrangente com 10+ metricas, mas nunca foi implementado

A RFC-005 define o modelo arquitetonico desejado: um `ci.yml` reutilizavel com jobs de lint, test e quality-gate, e workflows de release que invocam esse gate antes de buildar. Nenhum `build-wheel.yml` deve ser criado — o foco e o `release.yml` existente.

## Goals / Non-Goals

**Goals:**
- Transformar `ci.yml` em workflow reutilizavel (`workflow_call`) com 3 jobs encadeados (lint → test → quality-gate)
- Adicionar gate obrigatorio em `release.yml` — o workflow `ci.yml` deve passar antes do build
- Implementar todos os targets de qualidade do Makefile especificados na RFC-005
- Manter `make build` como PyInstaller (sem alterar comportamento existente)
- Criar scripts Python auxiliares (`quality_gate.py`, `complexity_metrics.py`, `check-mutation-score.py`)
- Adicionar dependencias e configuracoes de ferramentas no `pyproject.toml`
- Documentar a decisao arquitetonica via ADR-003

**Non-Goals:**
- Criar `build-wheel.yml` (explicitamente excluido)
- Alterar o comportamento de build de binarios (PyInstaller permanece inalterado)
- Migrar tests de `tests/` para `src/tests/` (a RFC-005 assume esse path, mas a realidade e `tests/`)
- Implementar wheel publishing (`python -m build`)
- Phase gradual — o gate e blocking desde o dia 1

## Decisions

### D1: ci.yml como workflow reutilizavel via workflow_call

**Decisao:** Adicionar `workflow_call` ao trigger `on` do `ci.yml` para que outros workflows (release.yml, futuros workflows) possam invoca-lo como job.

**Alternativa considerada:** Duplicar os passos de qualidade inline no `release.yml`.
**Rejeitada porque:** Duplicacao de ~40 linhas de config de CI; alteracoes no gate precisariam ser replicadas em N lugares. workflow_call e o mecanismo canonico do GitHub Actions para reuso.

**Consequencias:** `ci.yml` precisa expor outputs ou artifacts se workflows consumidores precisarem deles (atualmente nao necessario — o gate e binario: pass/fail).

### D2: 3 jobs encadeados (lint → test → quality-gate)

**Decisao:** Separar o pipeline em 3 jobs distintos com `needs`, em vez de um job monolitico.

**Alternativa considerada:** Job unico com todos os passos sequenciais.
**Rejeitada porque:** Jobs separados permitem: (a) paralelismo onde possivel (test e quality-gate rodam matrix 3.12/3.13 em paralelo), (b) falha rapida — lint falha em 30s sem esperar test de 2min, (c) visibilidade — cada job tem seu proprio log e status no GitHub UI.

```
lint (3.12, ~30s)
  │
  ▼
test (3.12 + 3.13, ~2min)
  │
  ▼
quality-gate (3.12 + 3.13, ~5min)
```

### D3: Python 3.12 no lint, 3.12 + 3.13 no test/quality-gate

**Decisao:** Lint roda apenas em 3.12 (resultado independe da versao), test e quality-gate rodam em matrix 3.12 e 3.13.

**Alternativa considerada:** Manter Python 3.10 em toda a matrix.
**Rejeitada porque:** A RFC-005 especifica 3.12/3.13. O projeto ja suporta >=3.10; testar nas versoes mais recentes garante compatibilidade futura. O `release.yml` continua usando 3.10 para build PyInstaller (estabilidade de binario).

**Consequencias:** O `pyproject.toml` ja declara `requires-python = ">=3.10"`, o que e compativel.

### D4: Cache de .venv no job quality-gate

**Decisao:** Usar `actions/cache@v4` com key baseada em `pyproject.toml` hash + Python version.

**Justificativa:** `make install-quality-tools` instala ~15 dependencias Python + jscpd via npm. Sem cache, cada run demora ~3min so em instalacao. O cache reduz para ~20s.

### D5: Makefile — expansao completa conforme RFC-005

**Decisao:** Adicionar todos os targets da RFC-005 mantendo `build` como PyInstaller.

**Targets novos:**
- `venv`: Cria virtualenv
- `install-quality-tools`: Instala deps quality + jscpd global
- `quality-gate`: Orchestrator (lint + complexity + duplication + test + mutation-check + security)
- `complexity`: radon cc + complexity_metrics.py + xenon + lizard
- `duplication`: jscpd com thresholds 10% (blocking) e 7% (warning)
- `mutation-run`, `mutation-check`, `mutation-stats`, `mutation-results`
- `security`, `security-all`, `security-changed`

**Target build mantido como PyInstaller:**
```makefile
build: $(ACTIVATE)
	$(PIP) install -q pyinstaller
	$(PYTHON) -m PyInstaller flowscope.spec
```

### D6: Scripts Python como entry points de metricas

**Decisao:** Criar 3 scripts em `scripts/` conforme RFC-005:

| Script | Funcao | Chamado por |
|--------|--------|-------------|
| `quality_gate.py` | Orquestrador que executa cada check, coleta metricas, emite relatorio JSON | `make quality-gate` |
| `complexity_metrics.py` | Calcula Maintainability Index e Halstead via radon; implementa Contract 2 (MI < 30 blocking, 30-70 warning, >= 70 pass) | `make complexity` |
| `check-mutation-score.py` | Le `mutants/mutmut-cicd-stats.json`, calcula score = killed/(killed+survived+timeout+suspicious)*100, falha se < 80 | `make mutation-check` |

### D7: release.yml — job ci como gate

**Decisao:** Adicionar job `ci` que invoca o workflow reutilizavel, e fazer `build` e `release` dependerem dele.

```yaml
jobs:
  ci:
    uses: ./.github/workflows/ci.yml

  build:
    needs: ci
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    # ... (inalterado)

  release:
    needs: build
    # ... (inalterado)
```

**Alternativa considerada:** Fazer cada job da matrix de build depender de ci (redundante).
**Rejeitada porque:** `needs: ci` no job `build` ja garante que todos os 3 builds so rodam apos CI passar. Nao ha beneficio em repetir a dependencia no job `release`.

### D8: pyproject.toml — grupos dev e quality separados

**Decisao:** Manter `dev` com dependencias minimas para desenvolvimento local (ruff, flake8, pytest, pytest-cov) e criar grupo `quality` com ferramentas pesadas (radon, xenon, lizard, mutmut, semgrep).

**Justificativa:** Desenvolvedores que so rodam lint+test localmente nao precisam instalar radon/mutmut/semgrep. O CI instala o grupo `quality` completo.

### D9: Configuracoes de ferramentas inline no pyproject.toml

**Decisao:** Configurar ruff, pytest, mutmut, e coverage diretamente no `pyproject.toml` em vez de arquivos separados (.ruff.toml, .coveragerc, setup.cfg).

**Justificativa:** Centralizacao. pyproject.toml ja e o arquivo canonico de configuracao Python (PEP 621). Todas as ferramentas escolhidas suportam `[tool.*]`.

### D10: jscpd via npm global, nao pip

**Decisao:** Instalar jscpd com `npm install -g jscpd@4.0.1` no target `install-quality-tools`, nao como dependencia Python.

**Justificativa:** jscpd e uma ferramenta Node.js sem distribuicao Python. A instalacao global via npm e a unica forma viavel. No CI (ubuntu-latest), Node.js ja esta disponivel.

## Risks / Trade-offs

| Risk | Mitigacao |
|------|-----------|
| **Falhas em massa no primeiro run** — O codigo atual pode falhar em complexidade, duplicacao, cobertura < 85% ou mutacao < 80% | Correcoes devem ser aplicadas como parte da implementacao. O gate e blocking desde o dia 1. |
| **Tempo de CI** — quality-gate completo (lint + test + complexity + duplication + mutation + security) pode levar 8-10min | Cache de .venv reduz instalacao. Jobs separados permitem falha rapida. Mutation testing e o passo mais lento. |
| **jscpd indisponivel no Windows/macOS** — `npm install -g` pode falhar em runners Windows | jscpd so roda no job quality-gate (ubuntu-latest). Builds de plataforma no release.yml nao executam quality-gate — apenas herdam o resultado do job `ci`. |
| **mutmut instabilidade** — Mutation testing pode ser flaky (timeouts, falsos sobreviventes) | Configuracao de timeout em `pyproject.toml`. `do_not_mutate_patterns` exclui loggers e raises. |
| **semgrep falsos positivos** — Regras OSS podem flagrar codigo legítimo como vulneravel | Severidade ERROR bloqueia, WARNING e informativo. Regras podem ser ajustadas via `.semgrep.yml` se necessario. |
| **Drift entre Makefile local e CI** — Makefile contem caminhos com `.venv/bin/` que so funcionam apos `make venv` | CI sempre roda `make venv` ou `make $(VENV)` como dependency. Localmente, desenvolvedor segue o mesmo fluxo. |

## Open Questions

- O codigo atual passa em todas as verificacoes? Se nao, quais falhas esperar e qual o esforco para corrigi-las? (Resposta: descobriremos durante a implementacao — e parte do trabalho)
- O coverage atual esta acima de 85%? (Verificar durante implementacao)
- O lint atual (ruff) tem erros? (Provavelmente sim — o `ci.yml` atual usa `ruff check .` mas nunca foi executado com as regras estendidas flake8 B, A, D)
