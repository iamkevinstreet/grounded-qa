.PHONY: install lint test smoke run clean

PY ?= .venv/bin/python

install:
	uv venv .venv && uv pip install -e ".[dev]" && $(PY) -m pre_commit install

lint:
	.venv/bin/ruff check . && .venv/bin/ruff format --check .

test:
	.venv/bin/pytest

smoke:
	$(PY) -m grounded_qa.evals.run --cases grounded_qa/evals/cases/sample.jsonl --fake

run:
	.venv/bin/uvicorn grounded_qa.api:app --reload

clean:
	rm -rf grounded_qa/data/generated grounded_qa/evals/results logs .pytest_cache .ruff_cache
