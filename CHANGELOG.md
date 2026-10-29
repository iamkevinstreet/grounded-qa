# Changelog

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
