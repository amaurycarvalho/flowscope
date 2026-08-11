.PHONY: venv install build test lint clean install-quality-tools quality-gate complexity duplication mutation-run mutation-check mutation-results mutation-stats security security-all security-changed

VENV = .venv

ifeq ($(OS),Windows_NT)
	PYTHON = $(VENV)/Scripts/python
	PIP = $(VENV)/Scripts/pip
	ACTIVATE = $(VENV)/Scripts/activate
	PYTHON_CMD = python
	BIN = $(VENV)/Scripts
else
	PYTHON = $(VENV)/bin/python3
	PIP = $(VENV)/bin/pip
	ACTIVATE = $(VENV)/bin/activate
	PYTHON_CMD = python3
	BIN = $(VENV)/bin
endif

$(ACTIVATE): pyproject.toml
	$(PYTHON_CMD) -m venv $(VENV)
	$(PYTHON) -m pip install -q --upgrade pip
	touch $(ACTIVATE)

venv: $(ACTIVATE)

install: $(ACTIVATE)
	$(PIP) install -q -e .
	$(PIP) install -q -e ".[dev]"

install-quality-tools: $(ACTIVATE)
	$(PIP) install -q -e ".[dev,quality]"
	npm install -g jscpd@4.0.1
	mkdir -p mutants/

quality-gate: $(ACTIVATE)
	$(MAKE) lint
	$(MAKE) complexity
	$(MAKE) duplication
	$(MAKE) test
	$(MAKE) security
	$(MAKE) mutation-check

build: $(ACTIVATE)
	$(PIP) install -q pyinstaller
	$(PYTHON) -m PyInstaller flowscope.spec

test: $(ACTIVATE)
	$(PYTHON) -m pytest --tb=short --cov --cov-report=xml:coverage.xml --cov-report=term-missing --cov-fail-under=85

lint: $(ACTIVATE)
	$(BIN)/ruff check src/
	$(BIN)/flake8 --max-complexity=10 --select=B,A,D --extend-exclude=tests ./src/

complexity: $(ACTIVATE)
	@echo "Checking complexity metrics..."
	@$(BIN)/radon cc -a -nb -i "tests,build,dist,ccache,mutants,.venv,.opencode" -s src/
	@$(PYTHON) scripts/complexity_metrics.py || exit 1
	@$(BIN)/xenon --max-absolute=B --max-modules=B --max-average=B --ignore "tests,build,dist,ccache,mutants,.venv,.opencode" src/ || exit 1
	@$(BIN)/lizard --CCN 10 --length 80 --warnings_only -x "./tests/*" -x "./build/*" -x "./dist/*" -x "./ccache/*" -x "./mutants/*" -x "./.venv/*" -x "./.opencode/*" -x "./src/tests/*" src/ || true

duplication: $(ACTIVATE)
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

mutation-run: $(ACTIVATE)
	@echo "Running mutation tests..."
	@$(BIN)/mutmut run
	@$(MAKE) mutation-stats

mutation-stats: $(ACTIVATE)
	@echo "Exporting mutation stats..."
	@$(BIN)/mutmut export-cicd-stats
	@$(PYTHON) scripts/check-mutation-score.py || exit 0

mutation-check: $(ACTIVATE)
	@echo "Checking mutation tests..."
	@$(PYTHON) scripts/check-mutation-score.py

mutation-results: $(ACTIVATE)
	@echo "Generating mutation tests results..."
	@echo "--------------Mutation tests results--------------" > mutants/mutmut-cicd-results.log
	@$(PYTHON) scripts/check-mutation-score.py >> mutants/mutmut-cicd-results.log || exit 0
	@echo "--------------Mutation tests logs-----------------" >> mutants/mutmut-cicd-results.log
	@$(BIN)/mutmut results | grep "survived" | cut -d':' -f1 | while read -r mutant; do \
		$(BIN)/mutmut show "$$mutant" >> mutants/mutmut-cicd-results.log; \
	done || exit 0
	@echo "Mutation tests results saved to mutants/mutmut-cicd-results.log"
	@echo "Lines count: $$(wc -l < mutants/mutmut-cicd-results.log)"
	@echo "\n============ SUMMARY ============="
	@echo "\n--- START (first 9 lines) ---"
	@head -n 9 mutants/mutmut-cicd-results.log
	@echo "\n--- END (last 10 lines) ---"
	@tail -n 10 mutants/mutmut-cicd-results.log
	@echo "===================================="

security: security-all

security-changed: $(ACTIVATE)
	@echo "Running security checks on changed files..."
	@$(BIN)/semgrep ci --oss-only --quiet --config auto --include "src/"

security-all: $(ACTIVATE)
	@echo "Running security checks..."
	@$(BIN)/semgrep scan --oss-only --quiet --config auto --severity ERROR --error src/
	@echo "Medium-severity findings (non-blocking):"
	@$(BIN)/semgrep scan --oss-only --quiet --config auto --severity WARNING --json src/ 2>/dev/null | $(PYTHON) -c "import json,sys; d=json.load(sys.stdin); n=len(d.get('results',[])); print(f'  {n} medium finding(s)')" || true

clean:
	rm -rf $(VENV) build/ dist/ __pycache__/ *.spec mutants/
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete
