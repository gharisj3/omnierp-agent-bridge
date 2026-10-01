PYTHON ?= python

.PHONY: setup test lint demo
setup:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

demo:
	$(PYTHON) -m scripts.demo
