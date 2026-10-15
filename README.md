# Grounded Q&A over approved sources, with abstention

[![ci](https://github.com/iamkevinstreet/grounded-qa/actions/workflows/ci.yml/badge.svg)](https://github.com/iamkevinstreet/grounded-qa/actions/workflows/ci.yml) [![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

An assistant that answers only from an approved set of documents and cites the passage it used. When the
documents do not cover the question, it says so. A claim without a real citation never reaches the user: the
service replaces it with the refusal and records that it did.

Case study with the evaluation plan and results: https://kevindstreet.com/projects/grounded-employment-law-qa/

## Layout

| Path | What it is |
| --- | --- |
| `ingest.py` | Splits approved documents into sections with title, heading, source and effective date |
| `retrieve.py` | Keyword (BM25) and embedding retrieval, merged by reciprocal rank fusion |
| `answer.py` | Prompt, structured answer with citations, and the abstention check |
| `api.py` | FastAPI service: `/ask`, and approver-only `/sources` for adding and removing documents |
| `evals/run.py` | Abstention correctness, retrieval recall at k, citation precision, keyword hits, speed, cost |
| `data/sources/` | The approved documents. Public-domain guidance only for the prototype |

## Run it

```sh
# offline smoke evaluation (no API calls)
python -m grounded_qa.evals.run --cases grounded_qa/evals/cases/sample.jsonl --fake

# compare retrieval configurations against the same questions
python -m grounded_qa.evals.run --cases ... --mode keyword
python -m grounded_qa.evals.run --cases ... --mode hybrid

# the service
uvicorn grounded_qa.api:app --reload
curl -s localhost:8000/ask -H 'content-type: application/json' -d '{"question": "Is planned leave paid?"}'
```

Embeddings come from the OpenAI-compatible provider. With `LLM_PROVIDER=anthropic`, retrieval falls back to
keyword only; set an OpenAI key for hybrid mode.

## Human review point

Answers are advisory and every claim links to its passage. Only an approver can change the approved sources.

## Changelog

- v0.0, Oct 13, 2026. Scaffold: ingest, hybrid retrieval, cited answers with abstention, service, evaluation.
