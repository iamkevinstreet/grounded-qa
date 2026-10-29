# Changelog

## Unreleased

- **Repository:** the shared packages move to utils v0.3.0, whose checker also limits a
  repository's published docs to README.md files, CHANGELOG.md and SECURITY.md, and checks that
  every link in them resolves.
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
