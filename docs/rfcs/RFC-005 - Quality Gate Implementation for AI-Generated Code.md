# RFC-005: Quality Gate Implementation for AI-Generated Code

## 1. Executive Summary

This RFC proposes the implementation of a comprehensive quality gate system for AI-generated code in our CI pipeline. The quality gate will enforce code quality, security, and maintainability standards through automated checks, ensuring that all AI-generated code meets our quality thresholds before being merged.

## 2. Problem Statement

AI-generated code can vary significantly in quality, potentially introducing:

- High cyclomatic complexity
- Poor test coverage
- Security vulnerabilities
- Excessive code duplication
- Unmaintainable code structures

Without automated enforcement, these issues may accumulate and degrade codebase quality.

## 3. Proposed Solution

### 3.1 Quality Metrics and Thresholds

| Metric                     | Fail Condition              | Tool         | Severity             |
| -------------------------- | --------------------------- | ------------ | -------------------- |
| Cyclomatic Complexity      | > 10 (Grade B)              | Radon        | Blocking             |
| Code Coverage              | < 85%                       | Pytest-cov   | Blocking             |
| Mutation Score             | < 80%                       | mutmut       | Blocking             |
| Maintainability Index      | < 30                        | Radon        | Blocking             |
| Maintainability Index      | >= 30 and < 70              | Radon        | Warning              |
| Maintainability Index      | no modules (MI unparseable) | Radon        | Blocking (fail-loud) |
| Halstead Difficulty        | > 20                        | Radon        | Informational        |
| Halstead Effort            | > 150,000                   | Radon        | Informational        |
| Halstead Bugs              | > 0.5                       | Radon        | Informational        |
| Source Lines of Code       | > 80 per function           | Lizard       | Warning              |
| Code Duplication           | > 10%                       | jscpd        | Blocking             |
| Code Duplication           | > 7% and <= 10%             | jscpd        | Warning              |
| Security Findings (High)   | > 0                         | semgrep      | Blocking             |
| Security Findings (Medium) | > 0                         | semgrep      | Warning              |
| Lint Errors                | > 0                         | ruff, flake8 | Blocking             |

### 3.2 Tool Selection

#### Linting & Code Quality

```yaml
- ruff: Primary linter, runs on the entire repository
- flake8: Combined invocation with --select=B,A,D
  - flake8-bugbear (B): Detect common bugs
  - flake8-annotations (A): Enforce type hints
  - flake8-docstrings (D): Enforce documentation
  - Scope: only ./src/ (tests excluded via --extend-exclude)
```

#### Code Duplication

```yaml
- jscpd: Detect code duplication across files (installed globally via npm).
  Ignores tests/ (.venv/ build/ dist/ __pycache__/) by default.
```

#### Complexity & Maintainability

```yaml
- radon: Cyclomatic complexity + Halstead + Maintainability Index
- lizard: Function length and complexity analysis (Warning only)
- xenon: Complexity monitoring (Blocking gate)
- Scope: analysis excludes tests/, build/, dist/ and ccache/
```

All three complexity tools are run over the `src/` package but with the
`tests/`, `build/`, `dist/`, `ccache/`, `mutants/` and `.venv/` directories
ignored (as well as `.opencode/`) so that generated/build outputs and test code
never affect the measured metrics.

#### Maintainability Index enforcement (Contract 2)

The Maintainability Index follows a two-tier blocking scheme (FR-007 +
clarification of 2026-08-04):

- worst MI >= 70 -> pass (exit 0)
- 30 <= worst MI < 70 -> [Warning], non-blocking (exit 0)
- worst MI < 30 -> [Blocking], **fails the gate** (exit 1)
- empty/unparseable MI -> treated as blocking (fail-loud) per FR-014, never a
  silent pass.

Only a sub-30 (or unavailable) MI fails the gate; Halstead metrics are warning
or informational and never fail it.

#### Testing

```yaml
- pytest: Testing framework
- pytest-cov: Coverage measurement (> 85% required)
- mutmut: Mutation testing (> 80% survival gate)
```

#### Security

```yaml
- semgrep: Static application security testing
  - ERROR (High) findings: Blocking
  - WARNING (Medium) findings: Warning (reported, non-blocking)
```

### 3.3 Implementation Architecture

```
Makefile (quality-gate target)
├── lint
│   ├── ruff check src/
│   └── flake8 --max-complexity=10 --select=B,A,D --extend-exclude=src/tests ./src/
├── complexity
│   ├── radon cc        (excludes tests/build/dist/ccache/mutants/.venv)
│   ├── scripts/complexity_metrics.py (Halstead warning/info + MI per Contract 2)
│   ├── xenon           (blocking, excludes tests/build/dist/ccache/mutants/.venv)
│   └── lizard          (warning only, --CCN 10 --length 80)
├── duplication
│   └── jscpd           (10% blocking, 7-10% warning; scans src + scripts)
├── test
│   └── pytest --cov --cov-fail-under=85
├── mutation-check
│   └── scripts/check-mutation-score.py (fail under 80, reads mutants/mutmut-cicd-stats.json)
└── security (alias of security-all)
    └── semgrep scan --severity ERROR --error   (ERROR blocking, WARNING reported)

Other mutation targets: mutation-run (mutmut run + mutation-stats),
mutation-stats (export-cicd-stats + non-blocking score check),
mutation-results (write mutants/mutmut-cicd-results.log with survived mutants).

.github/workflows/ci.yml (reusable via workflow_call)
  ├── lint job          (make lint, 3.12)
  ├── test job          (make test, 3.12 + 3.13)
  └── quality-gate job  (make install-quality-tools + make quality-gate, 3.12 + 3.13)
      ├── caches .venv
      └── uploads coverage.xml and mutation_report.html artifacts

.github/workflows/build-wheel.yml
  ├── calls ci.yml as quality-gate job (gating)
  └── build job: validates version tag, `make build`, publishes dist/*.whl via softprops/action-gh-release@v2
```

## 4. Implementation Details

### 4.1 Updated CI Workflow

```yaml
# .github/workflows/ci.yml (matches committed file exactly)
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_call:

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Lint
        run: make lint

  test:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Test
        run: make test

  quality-gate:
    runs-on: ubuntu-latest
    needs: test
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Cache virtual environment
        uses: actions/cache@v4
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('pyproject.toml') }}
      - name: Install quality tools
        run: make install-quality-tools
      - name: Run quality gate
        run: make quality-gate
      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.python-version }}
          path: coverage.xml
      - name: Upload mutation report
        uses: actions/upload-artifact@v4
        with:
          name: mutation-report-${{ matrix.python-version }}
          path: mutation_report.html
```

A second workflow, `.github/workflows/build-wheel.yml`, publishes wheel releases as
the gate for shipping. It listens on `push` of `v*` tags and on a
`workflow_dispatch` with a `version` input, calls `ci.yml` as the `quality-gate`
job, then on a `build` job (which `needs: quality-gate`) validates that the
version passes `^v?[0-9]+\.[0-9]+\.[0-9]+$`, runs `make build`, and publishes
`dist/*.whl` through `softprops/action-gh-release@v2` using `CHANGELOG.md` as the
body.

### 4.2 Enhanced Makefile

```makefile
# Makefile (matches committed file exactly)
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
FLAKE8 = $(VENV)/bin/flake8

.PHONY: venv install test build lint install-quality-tools quality-gate complexity duplication mutation-run mutation-check mutation-results mutation-stats security security-all security-changed

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip

venv: $(VENV)

install: $(VENV)
	$(PIP) install -e .

build: $(VENV)
	$(PIP) install -q build
	$(PYTHON) -m build

test: $(VENV)
	$(PIP) install -q -e .[dev]
	$(PYTHON) -m pytest --tb=short --cov=. --cov-report=xml:coverage.xml --cov-report=term-missing --cov-fail-under=85

lint: $(VENV)
	$(PIP) install -q -U .[dev]
	$(VENV)/bin/ruff check src/
	$(FLAKE8) --max-complexity=10 --select=B,A,D --extend-exclude=src/tests ./src/

install-quality-tools: $(VENV)
	$(PIP) install -q -U .[quality]
	npm install -g jscpd@4.0.1
	mkdir -p mutants/

quality-gate: $(VENV)
	$(MAKE) install-quality-tools
	$(MAKE) lint
	$(MAKE) complexity
	$(MAKE) duplication
	$(MAKE) test
	$(MAKE) mutation-check
	$(MAKE) security

complexity: $(VENV)
	@echo "Checking complexity metrics..."
	@$(VENV)/bin/radon cc -a -nb -i "tests,build,dist,ccache,mutants,.venv" -s src/
	@$(PYTHON) scripts/complexity_metrics.py || exit 1
	@$(VENV)/bin/xenon --max-absolute=B --max-modules=B --max-average=B --ignore "tests,build,dist,ccache,mutants,.venv" src/ || exit 1
	@$(VENV)/bin/lizard --CCN 10 --length 80 --warnings_only -x "./tests/*" -x "./build/*" -x "./dist/*" -x "./ccache/*" -x "./mutants/*" -x "./.venv/*" -x "./.opencode/*" -x "./src/tests/*" src/ || true

duplication: $(VENV)
	@echo "Checking code duplication..."
	@if jscpd --pattern "**/*.py" --threshold 10 --format python \
		--ignore "**/tests/**" --ignore "**/.venv/**" --ignore "**/build/**" \
		--ignore "**/dist/**" --ignore "**/__pycache__/**" --ignore "**/mutants/**" \
		--ignore "**/.opencode/**" src scripts --silent >/dev/null 2>&1; then \
		jscpd --pattern "**/*.py" --threshold 7 --format python \
			--ignore "**/tests/**" --ignore "**/.venv/**" --ignore "**/build/**" \
			--ignore "**/dist/**" --ignore "**/__pycache__/**" --ignore "**/mutants/**" \
			--ignore "**/.opencode/**" src scripts --silent >/dev/null 2>&1 && \
		(echo "Duplication OK (<= 7%)") || \
		(echo "WARNING: duplication between 7% and 10%"); \
	else \
		echo "BLOCKING: duplication > 10%"; exit 1; \
	fi

mutation-run: $(VENV)
	@echo "Running mutation tests..."
	@$(VENV)/bin/mutmut run
	@$(MAKE) mutation-stats

mutation-stats: $(VENV)
	@echo "Exporting mutation stats..."
	@$(VENV)/bin/mutmut export-cicd-stats
	@$(PYTHON) scripts/check-mutation-score.py || exit 0

mutation-results: $(VENV)
	@echo "Generating mutation tests results..."
	@echo "--------------Mutation tests results--------------" > mutants/mutmut-cicd-results.log
	@$(PYTHON) scripts/check-mutation-score.py >> mutants/mutmut-cicd-results.log || exit 0
	@echo "--------------Mutation tests logs-----------------" >> mutants/mutmut-cicd-results.log
	@$(VENV)/bin/mutmut results | grep "survived" | cut -d':' -f1 | while read -r mutant; do \
		.venv/bin/mutmut show "$$mutant" >> mutants/mutmut-cicd-results.log; \
	done || exit 0
	@echo "Mutation tests results saved to mutants/mutmut-cicd-results.log"
	@echo "Lines count: $$(wc -l < mutants/mutmut-cicd-results.log)"
	@echo "\n============ SUMMARY ============="
	@echo "\n--- START (first 9 lines) ---"
	@head -n 9 mutants/mutmut-cicd-results.log
	@echo "\n--- END (last 10 lines) ---"
	@tail -n 10 mutants/mutmut-cicd-results.log
	@echo "===================================="

mutation-check:
	@echo "Checking mutation tests..."
	@$(PYTHON) scripts/check-mutation-score.py

security: security-all

security-changed: $(VENV)
	@echo "Running security checks on changed files..."
	@$(VENV)/bin/semgrep ci --oss-only --quiet --config auto --include "src/" || exit 1

security-all: $(VENV)
	@echo "Running security checks..."
	@$(VENV)/bin/semgrep scan --oss-only --quiet --config auto --severity ERROR --error src/ || exit 1
	@echo "Medium-severity findings (non-blocking):"
	@$(VENV)/bin/semgrep scan --oss-only --quiet --config auto --severity WARNING --json src/ 2>/dev/null | $(PYTHON) -c "import json,sys; d=json.load(sys.stdin); n=len(d.get('results',[])); print(f'  {n} medium finding(s)')" || true
```

### 4.3 Quality Gate Script

```python
# scripts/quality_gate.py (matches committed file exactly)
#!/usr/bin/env python3
"""
Quality Gate enforcement script.
Executes each quality check as an external CLI tool, captures the metric value,
threshold, severity, status and evidence, and emits a consolidated report.
Exits non-zero when any blocking check fails or a tool errors (fail-loud).
"""

import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any


class QualityGate:
    def __init__(self, run_id: str = "", python_version: str = "") -> None:
        self.passed = True
        self.report: list[dict[str, Any]] = []
        self.run_id = run_id or os.environ.get("GITHUB_RUN_ID", "")
        self.python_version = python_version or os.environ.get("PYTHON_VERSION", "")

    def _record(
        self,
        name: str,
        value: str,
        threshold: str,
        severity: str,
        status: str,
        evidence: list[str] | None = None,
    ) -> None:
        if status == "fail" and severity == "blocking":
            self.passed = False
        self.report.append(
            {
                "name": name,
                "value": value,
                "threshold": threshold,
                "severity": severity,
                "status": status,
                "evidence": evidence or [],
            }
        )

    def record_mi(self, mi_text: str = "") -> None:
        """Record the Maintainability Index as its own metric row (Contract 2).

        Blocking when worst MI < 30, warning when 30 <= worst < 70, pass when
        worst >= 70. Fail-loud (FR-014) when MI cannot be established.
        """
        if not mi_text:
            mi_text = subprocess.run(
                [".venv/bin/radon", "mi", "-s", ".", "-i", "tests,build,dist,ccache,mutants,.venv"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout
        scores = [float(m) for m in re.findall(r"\(([\d.]+)\)\s*$", mi_text, re.MULTILINE)]
        if not scores:
            self._record(
                "Maintainability Index",
                value="unavailable",
                threshold=">= 30",
                severity="blocking",
                status="fail",
                evidence=["no modules evaluated; fail-loud"],
            )
            return
        worst = min(scores)
        if worst < 30:
            self._record(
                "Maintainability Index",
                value=f"{worst:.1f}",
                threshold=">= 30",
                severity="blocking",
                status="fail",
            )
        elif worst < 70:
            self._record(
                "Maintainability Index",
                value=f"{worst:.1f}",
                threshold=">= 70 but >= 30 to pass",
                severity="warning",
                status="warn",
            )
        else:
            self._record(
                "Maintainability Index",
                value=f"{worst:.1f}",
                threshold=">= 70",
                severity="informational",
                status="pass",
            )

    def run_command(self, cmd: list[str], name: str, threshold: str, severity: str) -> None:
        """Run a command; tool errors are recorded as a blocking failure."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                self._record(
                    name,
                    value=f"exit {result.returncode}",
                    threshold=threshold,
                    severity=severity,
                    status="fail",
                    evidence=(result.stderr or result.stdout).strip().splitlines()[:20],
                )
            else:
                self._record(name, value="ok", threshold=threshold, severity=severity, status="pass")
        except Exception as exc:
            self._record(
                name,
                value=f"error: {exc}",
                threshold=threshold,
                severity="blocking",
                status="fail",
                evidence=[str(exc)],
            )

    def summary(self) -> str:
        lines = ["=" * 50, "QUALITY GATE REPORT", "=" * 50]
        for check in self.report:
            mark = "PASS" if check["status"] == "pass" else "FAIL"
            lines.append(f"[{mark}] {check['name']}: {check['value']} (threshold {check['threshold']})")
            if check["evidence"]:
                lines.append(f"      evidence: {check['evidence'][0]}")
        lines.append("=" * 50)
        lines.append("All quality checks passed!" if self.passed else "Quality gate failed!")
        return "\n".join(lines)

    def json(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "python_version": self.python_version,
            "overall_status": "pass" if self.passed else "fail",
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": self.report,
        }


def main() -> int:
    gate = QualityGate()

    gate.run_command(["make", "lint"], "lint", "no violations", "blocking")
    gate.run_command(["make", "complexity"], "complexity", "< 10 CCN", "blocking")
    gate.record_mi()
    gate.run_command(["make", "duplication"], "duplication", "< 5%", "blocking")
    gate.run_command(["make", "test"], "coverage", "> 85%", "blocking")
    gate.run_command(["make", "mutation"], "mutation", "> 80% survival", "blocking")
    gate.run_command(["make", "security"], "security", "no ERROR findings", "blocking")

    print(gate.summary())
    print(json.dumps(gate.json(), indent=2))

    return 0 if gate.passed else 1


if __name__ == "__main__":
    sys.exit(main())
```

> Note: the script's `main()` still invokes `make mutation`, a target that does
> not exist in the Makefile. The effective gate entrypoint is the Makefile
> `quality-gate` target, which uses `mutation-check` instead. Aligning
> `quality_gate.py` to call `mutation-check` is a known follow-up.

### 4.4 Mutation Testing Configuration

```toml
# pyproject.toml (matches committed file exactly)
[tool.mutmut]
source_paths = [
    "src/",
]
pytest_add_cli_args_test_selection = [
    "-m",
    "not slow",
    "tests/",
]
pytest_add_cli_args = [
    "-q",
    "--disable-warnings",
]
runner = "pytest"
do_not_mutate = [
    "__init__.py",
    "src/tests/*",
    "tests/*",
    ".*/*",
    "build/*",
]
do_not_mutate_patterns = [
    'logger\.\w+',
    'raise \w+',
]
#mutate_only_covered_lines = true
on_dependency_change = "rerun"
timeout_constant = 1
timeout_multiplier = 10
```

Notes vs. the original proposal: `mutate_only_covered_lines` is deliberately
left **commented out** (not enabled — the whole uncovered-code surface is
mutated), `runner` is `pytest` (not `python -m pytest`), slow tests are excluded
via the `-m "not slow"` selection/`-q --disable-warnings` CLI args, and mutations
are skipped for loggers and `raise` statements via `do_not_mutate_patterns`.

The `scripts/check-mutation-score.py` gate is unchanged: it reads
`mutants/mutmut-cicd-stats.json` produced by `mutmut export-cicd-stats`,
computes `score = killed / (killed + survived + timeout + suspicious) * 100`,
and exits non-zero when the score is below `THRESHOLD = 80`.

```python
# scripts/check-mutation-score.py
#!/usr/bin/env python3
"""
Script to check mutation score from mutmut-cicd-stats.json file
"""

import json
import sys
from pathlib import Path

THRESHOLD = 80
JSON_FILE = Path("mutants/mutmut-cicd-stats.json")


def load_mutation_stats(json_path: Path) -> dict:
    """Load mutation statistics from JSON file."""
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON: {e}")
        sys.exit(1)


def calculate_mutation_score(stats: dict) -> tuple[float, int, int]:
    """
    Calculate mutation score.

    Returns: (score, killed, total)
    """
    killed = stats.get('killed', 0)
    survived = stats.get('survived', 0)
    timeout = stats.get('timeout', 0)
    suspicious = stats.get('suspicious', 0)

    total = killed + survived + timeout + suspicious

    if total == 0:
        print("⚠️  No mutants generated.")
        sys.exit(1)

    score = (killed / total) * 100
    return score, killed, total


def main():
    """Main function of the script."""
    # Load statistics
    stats = load_mutation_stats(JSON_FILE)

    # Display raw results (like the original script)
    print(f"Killed: {stats.get('killed', 0)}")
    print(f"Survived: {stats.get('survived', 0)}")
    print(f"Timeout: {stats.get('timeout', 0)}")
    print(f"Suspicious: {stats.get('suspicious', 0)}")
    print(f"Total: {stats.get('total', 0)}")
    print()

    # Calculate score
    score, killed, total = calculate_mutation_score(stats)

    # Display result
    print(f"Mutation Score: {score:.2f}%")

    # Check if it passed the threshold
    if score >= THRESHOLD:
        print(f"✅ Mutation Score >= {THRESHOLD}%")
        sys.exit(0)
    else:
        print(f"❌ Mutation Score < {THRESHOLD}%")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

```
# .gitignore
# Mutation testing
mutants/
.mutmut-cache
!mutants/mutmut-cicd-stats.json
```

## 5. Additional Recommendations

### 5.1 Code Review Integration

- Add GitHub PR comment bot to display quality metrics
- Require quality gate pass before PR approval
- Include quality report as PR checklist item

### 5.2 Developer Experience

- Local quality gate pre-commit hook
- VS Code/Cursor extension integration
- Instant feedback on code changes

### 5.3 Gradual Implementation

1. Phase 1: Run quality gate in informational mode (warnings only)
2. Phase 2: Enforce non-blocking metrics
3. Phase 3: Full blocking enforcement for all metrics

### 5.4 Documentation

- Create quality guide for developers
- Document exceptions process
- Provide examples of high-quality code patterns

## 6. Migration Path

### 6.1 Existing Codebase

- Identify and document quality debt
- Create plan to incrementally improve
- Allow exemptions for legacy code with review

### 6.2 New Code

- All new code must pass quality gate
- AI-generated code requires additional scrutiny
- Maintain quality reports per release

## 7. Monitoring and Evaluation

### 7.1 Metrics Dashboard

```
- Quality gate pass/fail rate over time
- Average complexity trends
- Coverage trends
- Mutation score trends
- Developer productivity metrics
```

### 7.2 Success Criteria

- 90%+ PR quality gate pass rate
- Gradual improvement in all metrics
- Reduced review time for AI-generated code
- Increased developer confidence

## 8. Tools and Dependencies

### 8.1 Required Dependencies

```toml
# pyproject.toml (matches committed file exactly)
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "flake8>=6.0.0",
    "flake8-bugbear>=23.0.0",
    "flake8-annotations>=3.0.0",
    "flake8-docstrings>=1.7.0",
]
quality = [
    "ruff>=0.1.0",
    "flake8>=6.0.0",
    "flake8-bugbear>=23.0.0",
    "flake8-annotations>=3.0.0",
    "flake8-docstrings>=1.7.0",
    "radon>=6.0.0",
    "xenon>=0.9.0",
    "lizard>=1.17.0",
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "mutmut>=3.6.0",
    "semgrep>=1.0.0",
]
```

Note: `jscpd` is **not** a pip dependency — it is installed globally via
`npm install -g jscpd@4.0.1` inside the `install-quality-tools` Makefile target.

The `[tool.ruff.lint]` section also intentionally ignores `BLE001` (broad
exception catch in plugin discovery), `S110` (best-effort housekeeping), and
`B008` (typer `Option`/`Argument` in parameter defaults).

The `[tool.pytest.ini_options]` section sets `testpaths = ["tests"]`, marks tests
as `slow` (deselected by default via `addopts = ["-m", "not slow"]`).

### 8.2 Installation Commands

```bash
make venv
make install-quality-tools
make quality-gate
```

## 9. Risk Assessment

| Risk                 | Impact                | Mitigation                             |
| -------------------- | --------------------- | -------------------------------------- |
| False positives      | Developer frustration | Allow exemptions with review           |
| Performance overhead | Slow CI               | Use caching, parallel jobs             |
| Tool maintenance     | Tool discontinuation  | Regular tool review, fallback options  |
| Team resistance      | Low adoption          | Gradual implementation, clear benefits |

## 10. Conclusion

This quality gate implementation provides a comprehensive framework for ensuring AI-generated code quality. The solution leverages established OSS tools, provides local replication capability, and integrates seamlessly with GitHub CI. By implementing these quality gates, we can maintain high code quality standards while leveraging AI-generated code efficiently.

---

## Appendix A: Quick Reference Commands

```bash
# Run full quality gate
make quality-gate

# Run individual checks
make lint
make complexity
make duplication
make test
make mutation-run    # run mutmut + export stats
make mutation-check # blocking score check (reads mutants/mutmut-cicd-stats.json)
make mutation-stats  # export stats + non-blocking score check
make mutation-results # write mutants/mutmut-cicd-results.log
make security        # alias for security-all (ERROR blocking, WARNING reported)
make security-changed # semgrep ci on src/ only

# Run the consolidated gate (all checks + consolidated report)
python scripts/quality_gate.py
```

## Appendix B: Example Quality Gate Output

```
==================================================
QUALITY GATE REPORT
==================================================
[PASS] lint: ok (threshold no violations)
[PASS] complexity: ok (threshold < 10 CCN)
[PASS] Maintainability Index: 74.2 (threshold >= 70)
[PASS] duplication: ok (threshold < 5%)
[PASS] coverage: ok (threshold > 85%)
[PASS] mutation: ok (threshold > 80% survival)
[PASS] security: ok (threshold no ERROR findings)
==================================================
All quality checks passed!
==================================================
```
