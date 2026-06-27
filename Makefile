.PHONY: install build test clean

VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

install: $(VENV)/bin/activate
$(VENV)/bin/activate: pyproject.toml
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .
	$(PIP) install -e ".[dev]"
	touch $(VENV)/bin/activate

build: $(VENV)/bin/activate
	$(PIP) install pyinstaller
	$(PYTHON) -m PyInstaller flowscope.spec

test: $(VENV)/bin/activate
	$(PYTHON) -m pytest tests/ -v

clean:
	rm -rf $(VENV) build/ dist/ __pycache__/ *.spec
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete
