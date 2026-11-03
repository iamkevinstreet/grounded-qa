# config

Everything the project configures lives here, in one folder:

| File | What it holds | In git |
| --- | --- | --- |
| [`config.toml`](config.toml) | Every setting the service, the dashboard and the web app read, at its default, and every value two of their files share | yes |
| [`.env.example`](.env.example) | The name of every secret, with an empty value | yes |
| `.env` | The secrets themselves: copy `.env.example` and fill it in | never |

`config.toml` holds no secrets, and the service refuses to start if one is written into it.

## How a value is chosen

Highest first: an environment variable, then `config/.env`, then `config.toml`, then the default in
[`backend/src/grounded_qa/config.py`](../backend/src/grounded_qa/config.py). Each key's environment
name is its section and key joined by an underscore, in capitals: `[retrieval] mode` is
`RETRIEVAL_MODE`. `SETTINGS_FILE` points the service at a different file. Every setting is logged at
startup, secrets masked, in the `service.start` event.

A test (`backend/tests/test_config.py`) keeps `config.toml` equal to the defaults in code, so the
two cannot drift.

The web app reads the keys it needs from `config.toml` when it is built
([`frontend/vite.config.ts`](../frontend/vite.config.ts) passes them to
[`frontend/src/config.ts`](../frontend/src/config.ts)): the API prefix and request-id header, the
question limits, the offline provider's name, the section separator, the milliseconds in a second
and the hash length. Nothing from `config/.env` reaches it. Change one of these and rebuild the web
app as well as restarting the service.

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
| `[llm] offline_provider` | `fake` | The provider name that means the offline stand-in; the web app says so when it is in use |
| `[azure_openai] api_version` | `2024-10-21` | Only for the `azure` provider |
| `[eval] budget_usd` | `5.0` | A process stops calling the model once it has spent this |
| `[eval] canaries` | `KESTREL-9`, `PINEAPPLE-7` | Phrases planted in `data/samples/`; no answer may repeat them |
| `[eval] answerable_field` | `answerable` | The field of a case that says whether the sources answer it |
| `[log] dir` | `logs` | Where the daily JSON log files go |
| `[log] level` | `INFO` | `DEBUG`, `INFO`, `WARNING` or `ERROR` |
| `[log] redact` | `true` | Removes emails, phone numbers and ID-like numbers from log lines |
| `[log] trace` | `false` | Prints the logger lines (once switched on) as HH:MM:SS traces |
| `[data] sources` | `data/sources` | The approved documents |
| `[data] samples` | `data/samples` | Synthetic documents only the evaluation adds |
| `[data] cases` | `data/evals/cases.jsonl` | The evaluation questions |
| `[data] results` | `data/evals/results` | Where evaluation results are written |
| `[data] audit` | `data/generated/audit.sqlite` | The append-only audit log |
| `[data] export` | `data/export` | Where the CSV files for Tableau go |
| `[data] figures` | `figures.json` | The name of the case study's figures file, written beside the results |
| `[retrieval] mode` | `keyword` | `keyword` (BM25), `semantic` or `hybrid`; the last two need the `local` extra |
| `[retrieval] k` | `6` | Passages shown to the model per question (1 to 20) |
| `[retrieval] pool` | `50` | Candidates each ranker passes to fusion |
| `[retrieval] rrf_k` | `60` | The reciprocal rank fusion constant |
| `[retrieval] bm25_k1` | `1.2` | BM25's term-frequency saturation |
| `[retrieval] bm25_b` | `0.75` | BM25's length normalisation (0 to 1) |
| `[retrieval] model` | `BAAI/bge-small-en-v1.5` | The local embedding model |
| `[retrieval] passage_words` | `180` | The most words in one passage |
| `[retrieval] section_separator` | `" > "` | Joins the headings of a passage's section; the web app splits on it |
| `[retrieval] keyword_mode` | `keyword` | The name of the mode that ranks by shared words alone, with no embedding model |
| `[answer] min_quote_words` | `4` | The shortest quote a citation may give |
| `[answer] max_words` | `150` | The longest answer the model may write |
| `[api] host` | `127.0.0.1` | The address the server listens on; this machine only |
| `[api] port` | `8000` | The port it listens on |
| `[api] min_question_chars` | `3` | The shortest question accepted |
| `[api] max_question_chars` | `1000` | The longest question accepted |
| `[api] max_source_bytes` | `200000` | The largest document an approver may add |
| `[api] asks_per_minute` | `20` | Questions one client may ask per minute |
| `[api] allowed_origins` | `http://localhost:5173` | Browser origins allowed to call the API |
| `[api] prefix` | `/api/v1` | The path every route lives under; the web app calls it |
| `[api] request_id_header` | `X-Request-ID` | The header that carries each request's id, the client's or a new one |
| `[text] encoding` | `utf-8` | How text becomes bytes: source files, hashes, sizes, tokens and result files |
| `[time] ms_per_second` | `1000` | Milliseconds in a second: request timings in the logs, trace lines in the web app |
| `[web] hash_chars` | `12` | How many characters of a SHA-256 the web app shows |
| `[dashboard] host`, `[dashboard] port` | `127.0.0.1`, `8050` | Where the evaluation dashboard listens; this machine only, since it has no sign-in |
| `[dashboard_ids] url` ... `wrong_table` | `url`, `scheme`, `runs`, `legend`, `tiles`, `outcomes`, `retrieval`, `latency`, `cost`, `wrong-table` | The ids of the dashboard's parts, which its layout and its callbacks share |
| `[columns] run_id` ... `cost_per_case` | `run_id`, `run`, `model`, `mode`, `started_at`, `kind`, `prices_as_of`, `case_id`, `case_kind`, `outcome`, `latency_ms`, `cost_per_case_usd` | The column names of the tables the dashboard draws and the Tableau CSV files hold |
| `[charts] light_scheme`, `dark_scheme` | `light`, `dark` | The two colour schemes; the exported figures use the light one |
| `[charts] max_runs` | `3` | The most runs a chart compares, one per step of the run ramp |
| `[charts] font_size`, `tick_size`, `edge` | `12`, `11`, `8` | Chart text size, tick size and edge margin, in pixels |
| `[charts] clear`, `align` | `rgba(0,0,0,0)`, `left` | The colour that lets the card show through; the edge titles and notes line up on |
| `[charts] cost_places`, `percent_ticks` | `4`, `.0%` | The decimals a cost is written with; the tick format of a share axis |
| `[charts] outcomes_title` ... `cost_title` | see the file | The title of each of the four charts, in the dashboard and in `figures.json` |
| `[outcomes] right` ... `failed` | `right`, `missed`, `refused_wrongly`, `refused_rightly`, `should_have_refused`, `failed` | How a question can end, as the tables and the charts name each outcome |
| `[labels.kinds]` | `direct` = `Direct`, `paraphrased` = `Everyday words`, `unanswerable` = `Unanswerable`, `adversarial` = `Adversarial` | The name of each kind of question, by its tag, in the order the charts list them |
| `[labels.outcomes]` | `right` = `Right`, `missed` = `Missed a fact`, `refused_wrongly` = `Refused wrongly`, `refused_rightly` = `Refused rightly`, `should_have_refused` = `Should have refused`, `failed` = `Failed` | How a question can end, in the order the outcomes chart stacks them |

## Secrets (`config/.env` only)

| Name | What it is |
| --- | --- |
| `APPROVER_TOKEN` | The approver's token, at least 32 characters. Unset, the approver routes are off. |
| `ANTHROPIC_API_KEY` | Needed when `[llm] provider = "anthropic"` |
| `OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY` | Needed only for those providers |

The web app has one build variable of its own, `VITE_API_BASE`, read in
[`frontend/src/config.ts`](../frontend/src/config.ts); unset, the app calls `[api] prefix` on its
own origin, which the development server proxies to the API.
