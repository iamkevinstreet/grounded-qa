# backend

The service and the evaluation, in Python 3.12: the `grounded_qa` package in `src/`, its tests,
and its locked dependencies. Run everything from the repository root (`make` targets do), where
`config/config.toml`, `config/.env` and `data/` are found.

## Run it

```sh
uv sync --project backend --locked             # the locked environment, hashes checked
uv run --project backend python -m grounded_qa.api   # the API on http://127.0.0.1:8000
uv sync --project backend --locked --extra local     # adds the local embedding model
```

With the default `[llm] provider = "fake"`, the offline stand-in answers: no key, no network. Set a
provider and its key (see [config/README.md](../config/README.md)) for real answers.

## The package

| Path | What it holds |
| --- | --- |
| `src/grounded_qa/config.py` | The one place settings are read: `AppSettings`, and `SETTINGS`, loaded once, for the values modules take from the config |
| `src/grounded_qa/core/` | The logic, free of HTTP: sources, the guard, passages, retrieval, the prompt, the quote check, the answerer, the library and the audit log |
| `src/grounded_qa/api/` | The FastAPI app: routes, the approver check, rate and size limits, headers, request ids |
| `src/grounded_qa/evals/` | The scorers and `python -m grounded_qa.evals.run answers\|retrieval` |
| `tests/` | 109 tests, offline; `support.py` holds shared helpers, `conftest.py` the fixtures |

The core depends on interfaces, not libraries: the answerer takes anything that can `search`, and
the retriever takes any `Embedder`, so tests pass small stand-ins and the real choice is made once,
from settings.

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
make audit-backend   # pip-audit over the locked dependencies
```
