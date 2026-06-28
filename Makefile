.PHONY: install build test clean

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
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -e .
	$(PIP) install -e ".[dev]"
	touch $(ACTIVATE)

build: $(ACTIVATE)
	$(PIP) install pyinstaller
	$(PYTHON) -m PyInstaller flowscope.spec

test: $(ACTIVATE)
	$(PYTHON) -m pytest tests/ -v

clean:
	rm -rf $(VENV) build/ dist/ __pycache__/ *.spec
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete
