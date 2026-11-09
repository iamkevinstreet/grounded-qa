# Changelog

## Unreleased

- **Dependency updates land by themselves.** Dependabot groups each week's updates into one pull
  request per kind (Actions, the backend, the frontend), and the new `dependency-updates` workflow
  lands them every weekday: it applies the oldest open one to `main` as an ordinary commit, refreshes
  the dates in the headers it changes, runs the whole of CI on that commit, and moves `main` to it only
  when every check passes. One whose checks fail is labelled "needs a person" and waits. CI can now
  be called for a given commit, which is how the workflow checks one before it lands.

## v0.4.1, Nov 9, 2026

- **Markers name the right quotes.** The model is told to number its citations one per quote, in
  the order it lists them, but sometimes numbers passages instead: two quotes from one passage both
  `[1]`, a quote from the next passage `[2]`, which as a quote number points at the second quote of
  the first passage. The judge found it on Nov 9: 5 of 80 live answers numbered their markers that
  way, and 2 showed a claim's source as the wrong passage. Before the quote check, markers that use
  exactly one number per passage are now rewritten to name every quote of their passage (`[1]`
  becomes `[1, 2]`, `[2]` becomes `[3]`), unless the claims fit the quotes their numbers name
  better. Each answer records whether it was rewritten (`realigned`, also on the `verify` span),
  and the evaluation scores `markers_matched` and `realigned` for every answered case.
- **Prompt 2026-11-09:** the rule on numbering says one number per quote, even for two quotes from
  one passage.
- **A case's time is the answer's alone** (utils v0.6.2). The evaluation used to stop its clock
  after scoring, so with the judge on, each case's time included the judge's call: the Nov 9 run
  file's medians were 4.3 s (keyword) and 3.8 s (hybrid), where the answers' own spans show 2.9 s
  and 2.3 s. That run is not published, since the case study's speed chart would have shown the
  answers slower than they were.
- **Judge, measured with the reference of v0.4.0** (Nov 9, run 42559425011): agreement 92.5%
  (keyword, 37 of 40) and 95.0% (hybrid, 38 of 40), up from 80% and 77.5%. Every disagreement is
  the judge stricter than the fixed check, and each is real: `sick-mom` hedges yet holds the
  checked words; `spouses-share-birth-leave` misdescribes the source's example;
  `staffing-agency-primary` adds a step the passages do not state; and the two marker answers above.
  The judge cost $0.16 a mode, about $0.004 a case, beside $0.47 and $0.46 for the answers.
- 144 backend tests.

## v0.4.0, Nov 7, 2026

- **A model judge beside the fixed checks:** with `[eval] judge` on, each answered case is also
  graded 0, 1 or 2 by `[llm] judge_model` against the case's evidence, using the workbench's judge,
  and the run reports `judge_score`, `judge_correct` (a full grade) and `judge_agrees`, how often the
  judge and the fixed check say the same. The fixed check looks for one accepted phrasing of each
  fact, so it can miss a right answer worded another way; the agreement rate says how often that
  matters. A refusal is not judged, since it is wrong to both. The judge runs on an adapter of its
  own, so the answers' cost stays theirs, and an offline run skips it. The live workflow turns it
  on by default (`judge`). Four tests cover the grading and its cost, what the judge reads, the
  cases left alone and the offline skip.
- **What the judge reads:** each part of a full answer, one for each group of the case's evidence,
  with the group's spans as alternatives (any one meets the part), and the whole text of every
  passage the answer cites, once, headed by every number that cites it. Two judged runs on Nov 8
  shaped this. The first gave the judge only the evidence quotes, and it marked 39 of 40 right
  answers partial for true detail drawn from their own cited passages (agreement 2.5% in both
  modes). The second gave it the cited passages, and agreement rose to 80% (keyword) and 77.5%
  (hybrid), but the judge's reasons trace 13 of its 17 disagreements to two faults in that
  reference: a passage cited as [1] and [2] carried only [1], so [2] read as a passage not given,
  and a group's alternative spans read as separate facts to give. The other 4 are what a judge is
  for: the sick-mom answers, in both modes, contain the words the fixed check looks for but never
  say plainly that the leave is available, and two answers add a claim their cited passages do
  not state. The fixed checks of both runs stand; the judge's figures wait for a run with this
  reference.
- **What the judge costs:** each judged case records `judge_cost_usd`, what the judge spent on it,
  apart from the answer's own `cost_usd`, and the judge stops at `[eval] judge_budget_usd` (2.0),
  a budget of its own, so a judged run spends at most the two budgets together. Until now the
  judge's spend showed only in the spans files, and the judge drew on a second copy of
  `[eval] budget_usd`. In the Nov 8 rerun it spent $0.2456 (keyword) and $0.2449 (hybrid), 41 calls
  each, about $0.006 a call, beside the answers' $0.4709 and $0.4740.
- 139 backend tests. The health report and the API schema say 0.4.0.

## v0.3.1, Nov 7, 2026

- **Spans:** the Anthropic SDK no longer adds a span of its own to each model call. That span
  repeated the `chat` span's call, tokens included, so Langfuse listed every call twice, and it
  carried the account's organization and workspace ids. The workbench moves to utils v0.6.1, which
  builds the Anthropic client with the SDK's spans and trace headers off. The two spans files of
  the Nov 7 live run, on the eval-results branch, have those spans removed too.
- 135 backend tests. The health report and the API schema say 0.3.1.

## v0.3.0, Nov 7, 2026

- **An MCP server:** any MCP client, such as Claude Desktop or Claude Code, can use the library.
  Four read-only tools (`ask`, `search_sources`, `get_passage`, `list_sources`) and each approved
  source as a `source://` resource, built on the MCP Python SDK 2.3 (protocol 2026-07-28).
  `python -m grounded_qa.mcp_server` serves them over stdio, and the API serves them over
  Streamable HTTP at `/mcp`. `ask` answers exactly as the API does, and every MCP client's
  questions share `[api] asks_per_minute`. The guard holds here too: passages come only from
  sources it passed and are screened again on their way out, and a held-back source is listed by
  its count of flagged lines, never their text. Eight tests drive the server through a real MCP
  client, in process and over HTTP.
- **Spans:** each question is one `answer` span holding its `retrieval` (the passages found, by id
  and score), its `chat` call (tokens, cost, stop reason) and its `verify` check (the quotes kept,
  shown in Langfuse as a guardrail), named as the OpenTelemetry GenAI conventions name them. An MCP
  call's `tools/call` span holds the answer span, and an evaluation run gives each case an `eval`
  span with its scores. With `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in `config/.env` they
  go to Langfuse; unset, spans stay off. The live workflow sends them when those two repository
  secrets are set and commits each run's spans beside its results. Two tests check the tree.
- **The workbench:** utils v0.6.0 (spans), pinned at its new commit. New settings are in
  `config/config.toml`: `[spans]`, `[langfuse]` and `[mcp]`.
- **A question is tidied once,** in `core/text.py`, for the API and the MCP server alike.
- 135 backend tests. The health report and the API schema say 0.3.0.

## v0.2.2, Nov 5, 2026

- **Dependencies:** the web app moves to ESLint 10.14.0, eslint-plugin-jsdoc 65.4.2 and
  @types/node 26.6.6. The last two are two major versions on: the plugin's rules are the same,
  and the Node types still check `vite.config.ts`, the one file that uses them. Nothing had to
  change: lint, the types, the tests, the build and the audits pass as they were. The health
  report and the API schema say 0.2.2.

## v0.2.1, Nov 5, 2026

- **The evaluation dashboard:** `make dashboard` serves a Dash app on `127.0.0.1:8050` over the
  saved answer runs, the offline baseline among them. Pick up to three runs; the first is in focus.
  The headline tiles show its measures and how each moved against the second run; four charts show
  how each kind of question ended (stacked by outcome, a panel per run), recall at k and MRR (a bar
  per run), seconds per question (a dot per question over its run's box) and cost per question at
  list prices; the runs table and the table of every question that went wrong follow. The design
  is kevindstreet.com's, in light and dark.
- **The case study's figures:** `python -m grounded_qa.dashboard --export-figures` writes
  `data/evals/results/figures.json`, the four charts of the latest live runs as Plotly JSON, each
  trace naming its part so the site can restyle it; `python -m grounded_qa.evals.index` writes
  `index.json`, the live run files newest first and the figures, so the site fetches by name.
- **The Tableau files:** `python -m grounded_qa.evals.export` writes `data/export/runs.csv`,
  `questions.csv` and `citations.csv` from the same tables the dashboard draws, each citation
  marked against the cases' evidence by the scorer's own check. `data/README.md` says what each
  column holds and which sheets to build.
- **`make publish`** runs all three; the live workflow runs it after the answer runs and commits
  what it writes with the results. `make install` and CI sync every extra, so the dashboard's
  tests run. The new settings (the export and figures paths, the dashboard's address and ids,
  the column names, the charts' settings, the outcomes and the labels) are in `config/config.toml`.
- **The box:** every file's header box and every section banner is five lines now: a border, a
  blank walled line, the title, another blank walled line and a border. The shared packages are
  pinned to utils v0.5.0, commit `fcac0477e1caadccf1e2d7580ce648258c5a79fa`, whose checker asks for
  that form and whose `stamp` brought every file to it. The dotfiles that take `#` comments carry
  a header like the Makefile. No code changed.
- **Utils v0.5.1:** the shared packages then move to utils v0.5.1, commit
  `e57de0e97d1c41616af1a98873f6beeecc74c99f`, whose checker also reads the statements inside a
  function whose signature wraps and inside a bare `catch`. Each of them in the web app already
  had its logger line, so no code changed; the health report and the API schema say 0.2.1.

## v0.2.0, Oct 29, 2026

The code moves to the updated code standard. What the service does, what its API answers and the
evaluation's numbers are unchanged; the health report and the API schema now say 0.2.0.

- **The src layout:** the backend package moves to `backend/src/grounded_qa`, so the tests import
  the installed package rather than the folder beside them, and a module left out of the package
  fails in the tests rather than after release.
- **One config folder:** `config/settings.toml` is now `config/config.toml`, and the secrets move
  from `.env` at the root to `config/.env`, which `config/.env.example` lists. Every value two
  files share is now a setting there too, such as the API prefix, the request-id header and the
  text encoding; `config/README.md` lists them all. The web app reads the keys it needs from the
  same file when it is built, so the question limits and the API prefix it uses cannot drift from
  the service's.
- **The file layout:** every source file opens with a box holding its path and a doc block with
  the author, the dates and what the file is for, then its imports (standard library, third-party
  and local), the values it takes from the config, its own constants and its logic, each under a
  banner. The Makefile, the stylesheets and the page the app loads into follow suit.
- **Functions show their whole contract:** every parameter has a type and a default, `None` or
  `null` where there is no natural one; a function that cannot work without a value takes it with
  `required()`, which names the missing argument the way Python does; and every function's doc
  block says what each argument is for and what comes back. ESLint now checks the TypeScript's
  doc blocks, defaults and return types. The API schema still describes each route by its summary
  alone: the Args and Returns sections are for readers of the code.
- **Shorter functions:** no function runs past 60 lines. The web app's longer components are split
  into smaller ones (the top bar, the result under the question, the question box and its examples,
  the sources table and reader, the add-source fields, the approver's token form and tools), and
  the approver's session moves to `src/approver.ts`. Every page renders exactly as before.
- **Utils:** the shared packages are pinned to utils v0.4.2, commit
  `62a38c5a3ecf667e3e227b18412abd77759c38d5`, which adds `kds-args` and checks that no function
  runs past 60 lines; ESLint checks the same in the web app. They passed through v0.3.0,
  whose checker limits a repository's published docs to README.md files, CHANGELOG.md and
  SECURITY.md, and checks that every link in them resolves.
- **Live results:** `claude-sonnet-5-5` answered 88.9% of answerable cases correctly in hybrid
  mode (86.7% in keyword mode), refused all 11 cases it should refuse, repeated no planted canary,
  and had no quote cut, for $0.47 across 56 cases. Every hybrid miss was a refusal. Citation
  precision, 82.5%, missed its 90% target; the README explains what it counts.
- **Retrieval:** measured in keyword, semantic and hybrid modes on GitHub's runner. Hybrid ranks
  the evidence in the top three for 82% of answerable questions (keyword: 69%).

## v0.1.0, Oct 29, 2026

A rebuild to one code standard, on a real corpus, with an evaluation you can repeat.

- **Corpus:** 22 U.S. Department of Labor fact sheets on FMLA leave, overtime, hours worked,
  recordkeeping, white-collar exemptions, retaliation and breaks to pump at work, copied on
  Oct 29, 2026. Each carries its source address, revision date and the SHA-256 of its text, and was
  checked byte for byte against the live page. The scaffold's one sample document is gone.
- **Answers:** the model must quote every passage it cites. A quote that is not in its passage
  removes the claim it supports; an answer left with no checked quote is withheld. Answers say when
  the sources do not cover a question.
- **Retrieval:** BM25 by default, with semantic and hybrid modes from a local embedding model
  (BAAI/bge-small-en-v1.5). The scaffold's plan to embed through the OpenAI API is dropped, so
  hybrid search needs no second provider or key.
- **Prompt injection:** an ingest guard holds back instruction-like sources; passages are fenced as
  data; the quote check limits what an injection can make the answer say.
- **Approver:** adding or removing a source needs the approver token and is written to an
  append-only audit log.
- **Web app:** React and TypeScript. Ask a question, see each citation's passage with the quote
  highlighted, browse the sources, and manage them as the approver.
- **Evaluation:** 56 cases: 35 worded like the sources, 5 paraphrased, 10 the sources do not
  answer, and 6 adversarial (false premises, injections in a source or the question, a request for
  legal advice). Eleven of the 56 should end in an abstention.
  Retrieval is scored on its own, in all three modes, with no model.
- **Repository:** strict mypy, ESLint and Stylelint, lockfiles with hashes, `pip-audit` and
  `npm audit`, CodeQL, Dependabot, Actions pinned to commit SHAs, `SECURITY.md`, and diagrams drawn
  from `docs/diagrams.toml`.

## v0.0, Oct 13, 2026

Scaffold: ingest, retrieval, cited answers with abstention, the service, and an evaluation entry
point, over one sample document.
