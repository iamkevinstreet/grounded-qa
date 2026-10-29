# config

[`settings.toml`](settings.toml) lists every setting the service reads, at its default. It holds no
secrets: those go in `.env` (copy [`.env.example`](../.env.example)), and the service refuses to
start if a secret is written here.

## How a value is chosen

Highest first: an environment variable, then `.env`, then this file, then the default in
[`backend/grounded_qa/config.py`](../backend/grounded_qa/config.py). Each key's environment name is
its section and key joined by an underscore, in capitals: `[retrieval] mode` is `RETRIEVAL_MODE`.
`SETTINGS_FILE` points the service at a different file. Every setting is logged at startup, secrets
masked, in the `service.start` event.

A test (`backend/tests/test_config.py`) keeps this file equal to the defaults in code, so the two
cannot drift.

## Every setting

| Setting | Default | What it does |
| --- | --- | --- |
| `[llm] provider` | `fake` | `anthropic`, `openai`, `azure`, or `fake`, the offline stand-in |
| `[llm] model` | `claude-sonnet-5-5` | The model that drafts answers |
| `[llm] judge_model` | `claude-sonnet-5-5` | Unused here: answers are scored by fixed checks |
| `[llm] embedding_model` | `text-embedding-3-small` | Unused here: embeddings run locally |
| `[llm] max_tokens` | `2048` | The most tokens one draft may use |
| `[llm] temperature` | `0.0` | 0 keeps answers repeatable |
| `[llm] max_retries` | `3` | Retries for failures that can succeed later |
| `[llm] timeout_s` | `60.0` | How long one model call may take |
| `[azure_openai] api_version` | `2024-10-21` | Only for the `azure` provider |
| `[eval] budget_usd` | `5.0` | A process stops calling the model once it has spent this |
| `[eval] canaries` | `KESTREL-9`, `PINEAPPLE-7` | Phrases planted in `data/samples/`; no answer may repeat them |
| `[log] dir` | `logs` | Where the daily JSON log files go |
| `[log] level` | `INFO` | `DEBUG`, `INFO`, `WARNING` or `ERROR` |
| `[log] redact` | `true` | Removes emails, phone numbers and ID-like numbers from log lines |
| `[log] trace` | `false` | Prints the logger lines (once switched on) as HH:MM:SS traces |
| `[data] sources` | `data/sources` | The approved documents |
| `[data] samples` | `data/samples` | Synthetic documents only the evaluation adds |
| `[data] cases` | `data/evals/cases.jsonl` | The evaluation questions |
| `[data] results` | `data/evals/results` | Where evaluation results are written |
| `[data] audit` | `data/generated/audit.sqlite` | The append-only audit log |
| `[retrieval] mode` | `keyword` | `keyword` (BM25), `semantic` or `hybrid`; the last two need the `local` extra |
| `[retrieval] k` | `6` | Passages shown to the model per question (1 to 20) |
| `[retrieval] pool` | `50` | Candidates each ranker passes to fusion |
| `[retrieval] rrf_k` | `60` | The reciprocal rank fusion constant |
| `[retrieval] bm25_k1` | `1.2` | BM25's term-frequency saturation |
| `[retrieval] bm25_b` | `0.75` | BM25's length normalisation (0 to 1) |
| `[retrieval] model` | `BAAI/bge-small-en-v1.5` | The local embedding model |
| `[retrieval] passage_words` | `180` | The most words in one passage |
| `[answer] min_quote_words` | `4` | The shortest quote a citation may give |
| `[answer] max_words` | `150` | The longest answer the model may write |
| `[api] host` | `127.0.0.1` | The address the server listens on; this machine only |
| `[api] port` | `8000` | The port it listens on |
| `[api] min_question_chars` | `3` | The shortest question accepted |
| `[api] max_question_chars` | `1000` | The longest question accepted |
| `[api] max_source_bytes` | `200000` | The largest document an approver may add |
| `[api] asks_per_minute` | `20` | Questions one client may ask per minute |
| `[api] allowed_origins` | `http://localhost:5173` | Browser origins allowed to call the API |

## Secrets (`.env` only)

| Name | What it is |
| --- | --- |
| `APPROVER_TOKEN` | The approver's token, at least 32 characters. Unset, the approver routes are off. |
| `ANTHROPIC_API_KEY` | Needed when `[llm] provider = "anthropic"` |
| `OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY` | Needed only for those providers |

The frontend has one setting of its own, `VITE_API_BASE`, read in
[`frontend/src/config.ts`](../frontend/src/config.ts); it defaults to `/api/v1`, which the
development server proxies to the API.
