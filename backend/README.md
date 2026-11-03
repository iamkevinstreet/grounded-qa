# backend

The service, the evaluation and the evaluation dashboard, in Python 3.12: the `grounded_qa`
package in `src/`, its tests, and its locked dependencies. Run everything from the repository root
(`make` targets do), where `config/config.toml`, `config/.env` and `data/` are found.

## Run it

```sh
uv sync --project backend --locked --all-extras      # the locked environment, hashes checked
uv run --project backend python -m grounded_qa.api   # the API on http://127.0.0.1:8000
uv run --project backend python -m grounded_qa.dashboard   # the dashboard on http://127.0.0.1:8050
```

The `local` extra adds the local embedding model for semantic and hybrid retrieval; the `dashboard`
extra adds Dash, Plotly and pandas for the dashboard, the figures and the Tableau files.
`uv sync --project backend --locked` alone installs neither.

With the default `[llm] provider = "fake"`, the offline stand-in answers: no key, no network. Set a
provider and its key (see [config/README.md](../config/README.md)) for real answers.

## The package

| Path | What it holds |
| --- | --- |
| `src/grounded_qa/config.py` | The one place settings are read: `AppSettings`, and `SETTINGS`, loaded once, for the values modules take from the config |
| `src/grounded_qa/core/` | The logic, free of HTTP: sources, the guard, passages, retrieval, the prompt, the quote check, the answerer, the library and the audit log |
| `src/grounded_qa/api/` | The FastAPI app: routes, the approver check, rate and size limits, headers, request ids |
| `src/grounded_qa/evals/` | The scorers and `python -m grounded_qa.evals.run answers\|retrieval`; `shares.py`, how a number and a share are written, by the same rules as the case study; `export.py` and `index.py`, the Tableau CSV files and the index the case study reads |
| `src/grounded_qa/dashboard/` | The Dash dashboard and the Plotly figures the case study draws: `data.py` and `rows.py` read the run files into the tables the dashboard and the export share; `views.py` picks what the page shows; `theme.py`, `outcome_charts.py`, `retrieval_charts.py`, `run_charts.py` and `tiles.py` draw it; `layout.py`, `page.py` and `app.py` lay out and serve the page; `export.py` writes the figures |
| `tests/` | 125 tests, offline; `support.py` holds shared helpers, `conftest.py` the fixtures |

The core depends on interfaces, not libraries: the answerer takes anything that can `search`, and
the retriever takes any `Embedder`, so tests pass small stand-ins and the real choice is made once,
from settings.

## Commands

| Command | What it does |
| --- | --- |
| `python -m grounded_qa.api` | Serves the API |
| `python -m grounded_qa.evals.run answers --mode <mode> --name <name>` | Answers and scores every case; offline with the fake provider, live otherwise |
| `python -m grounded_qa.evals.run retrieval --modes <modes>` | Scores retrieval alone, with no model |
| `python -m grounded_qa.dashboard` | Serves the dashboard; `--export-figures` writes the case study's figures instead |
| `python -m grounded_qa.evals.export` | Writes the three Tableau CSV files |
| `python -m grounded_qa.evals.index` | Writes the index of committed live results |

Run them as `uv run --project backend --no-sync python -m ...`, or through the Makefile:
`make dashboard` serves the dashboard and `make publish` writes the figures, the CSV files and the
index after a live run.

## The API

Interactive docs are off on purpose (they would need a looser content security policy); the schema
is at `GET /api/v1/openapi.json`.

| Route | Who | What |
| --- | --- | --- |
| `GET /api/v1/health` | anyone | Version, sources, passages, mode, provider, whether approver routes are on |
| `POST /api/v1/ask` | anyone | `{"question": "..."}` in; a checked answer or an abstention out |
| `GET /api/v1/sources` | anyone | Every approved source's provenance |
| `GET /api/v1/sources/{id}` | anyone | One source with its full text |
| `POST /api/v1/admin/sources` | approver | Add a source; checked, guarded, stored, audited, indexed |
| `DELETE /api/v1/admin/sources/{id}` | approver | Remove a source; audited |
| `GET /api/v1/admin/audit` | approver | The latest changes, newest first |

Approver routes take `Authorization: Bearer <APPROVER_TOKEN>`. Every response carries
`X-Request-ID`, which a client may also send (letters, digits, `-` and `_`, up to 64).

## Conventions

- The package uses the src layout, so the tests import the installed package (`uv sync` installs
  it in editable mode), never the folder beside them.
- Each module opens with a box holding its path and a doc block (author, dates, what it is for),
  then its imports, the values it takes from the config, its own constants and its logic, each
  under a banner. A value two modules share lives in `config/config.toml` and is read through
  `SETTINGS`; code the tests run with other settings takes them as a parameter.
- Every function shows its whole contract: each parameter has a type and a default, those it
  cannot do without are taken with `required()` from `kds.args`, and its doc block lists every
  argument and what comes back.
- Every statement has a commented logger line above it. `kds-standards trace on backend` turns
  them on in a working copy; `trace off` before committing.
- Lint and format: ruff (`backend/pyproject.toml`); types: mypy in strict mode, tests included.
- Tests never call a model or the network, write only to `tmp_path`, and run from an empty folder
  so no `config/.env` can leak in.

```sh
make check-backend   # ruff, format, mypy, kds-standards
make test-backend    # pytest -W error
make eval            # the offline evaluation
make dashboard       # the evaluation dashboard on http://127.0.0.1:8050
make publish         # the figures, the Tableau CSV files and the index, after a live run
make audit-backend   # pip-audit over the locked dependencies
```
