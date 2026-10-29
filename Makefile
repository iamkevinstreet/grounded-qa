########################################################################
#                               Makefile                               #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-14                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           One command for each routine task: install, run, #
#                     check, test, eval, audit, diagrams, build.       #
########################################################################
# CI runs the same targets. Run them from the repository root, where
# config/settings.toml and data/ are found.
UV := uv run --project backend --no-sync
NPM := npm --prefix frontend
# Our own packages install from git, not PyPI, so the PyPI audit leaves them out.
KDS := kds-settings kds-logs kds-llm kds-evals kds-standards kds-diagrams
AUDIT_FILE := data/generated/requirements-audit.txt

.PHONY: install run api web check check-backend check-frontend test test-backend test-frontend \
	eval eval-retrieval audit audit-backend audit-frontend diagrams build

install:  ## The backend from uv.lock and the frontend from package-lock.json
	uv sync --project backend --locked
	$(NPM) ci

run:  ## The API on :8000 and the web app on :5173 together; Ctrl-C stops both
	$(MAKE) -j2 api web

api:  ## The API alone
	$(UV) python -m grounded_qa.api

web:  ## The web app alone; it proxies /api to :8000
	$(NPM) run dev

check: check-backend check-frontend  ## Every linter, formatter, type check and the code standard

check-backend:
	$(UV) ruff check backend
	$(UV) ruff format --check backend
	cd backend && uv run --no-sync mypy src tests
	$(UV) kds-standards check .

check-frontend:
	$(NPM) run lint
	$(NPM) run format:check
	$(NPM) run typecheck

test: test-backend test-frontend  ## Every test, offline and deterministic

test-backend:
	cd backend && uv run --no-sync pytest -W error

test-frontend:
	$(NPM) test

eval:  ## The offline evaluation: the stand-in answers every case; no key, no network
	$(UV) python -m grounded_qa.evals.run answers --mode keyword --name offline-keyword
	$(UV) python -m grounded_qa.evals.run retrieval --modes keyword

eval-retrieval:  ## Retrieval in all three modes; needs the local extra
	$(UV) python -m grounded_qa.evals.run retrieval --modes keyword semantic hybrid

audit: audit-backend audit-frontend  ## Known vulnerabilities in every locked dependency

audit-backend:
	mkdir -p data/generated
	uv export --project backend --locked --all-extras --all-groups --no-emit-project \
		$(addprefix --no-emit-package ,$(KDS)) --format requirements.txt -o $(AUDIT_FILE) --quiet
	$(UV) pip-audit --strict --require-hashes --disable-pip -r $(AUDIT_FILE)

audit-frontend:
	$(NPM) audit --audit-level=moderate

diagrams:  ## Redraw docs/architecture.svg and docs/flow.svg from docs/diagrams.toml
	$(UV) kds-diagrams docs/diagrams.toml

build:  ## The production web app, in frontend/dist
	$(NPM) run build
