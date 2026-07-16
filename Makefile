.PHONY: install build test lint clean

VENV = .venv

ifeq ($(OS),Windows_NT)
	PYTHON = $(VENV)/Scripts/python
	PIP = $(VENV)/Scripts/pip
	ACTIVATE = $(VENV)/Scripts/activate
	PYTHON_CMD = python
else
	PYTHON = $(VENV)/bin/python3
	PIP = $(VENV)/bin/pip
	ACTIVATE = $(VENV)/bin/activate
	PYTHON_CMD = python3
endif

install: $(ACTIVATE)

$(ACTIVATE): pyproject.toml
	$(PYTHON_CMD) -m venv $(VENV)
	$(PYTHON) -m pip install -q --upgrade pip
	$(PIP) install -q -e .
	$(PIP) install -q -e ".[dev]"
	touch $(ACTIVATE)

build: $(ACTIVATE)
	$(PIP) install -q pyinstaller
	$(PYTHON) -m PyInstaller flowscope.spec

test: $(ACTIVATE)
	$(PIP) install -q pytest
	$(PYTHON) -m pytest tests/ -v --tb=short

lint: $(VENV)
	$(PIP) install -q ruff
	$(VENV)/bin/ruff check .

clean:
	rm -rf $(VENV) build/ dist/ __pycache__/ *.spec
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete
