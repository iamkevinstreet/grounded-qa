"""Run the grounded Q&A evaluation.

    python -m grounded_qa.evals.run --cases grounded_qa/evals/cases/sample.jsonl --fake
    python -m grounded_qa.evals.run --cases ... --mode keyword     # compare retrieval configurations

Scores per case: abstention correctness, retrieval recall at k, citation precision, keyword hit. The runner adds
latency and cost. A model judge can be added for answer quality once a hand-graded sample exists (see kds.evals.judge).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from kds.evals.case import EvalCase, load_cases
from kds.evals.runner import run_eval
from kds.llm.adapter import ModelAdapter
from kds.llm.fake import FakeProvider

from grounded_qa.answer import Result, answer_question
from grounded_qa.ingest import build_index
from grounded_qa.retrieve import Retriever

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
RESULTS_DIR = HERE / "results"


def fake_responder_for(cases: list[EvalCase], sections):
    """Offline stand-in: cites the gold section when the question is answerable, abstains otherwise,
    and makes one deliberate unsupported citation so the abstention check is exercised."""
    by_q = {c.input["question"]: c for c in cases}
    by_id = {s.id: s for s in sections}

    def respond(messages):
        text = messages[-1].content
        for q, c in by_q.items():
            if q in text:
                if not c.expected["answerable"]:
                    return json.dumps({"abstain": True, "answer": "", "citations": []})
                sid = c.expected["gold_sections"][0]
                sec = by_id[sid]
                quote = sec.text.split(".")[0] + "."
                if "false-premise" in c.tags:
                    quote = "a quote that is not in the passage"
                return json.dumps(
                    {"abstain": False, "answer": quote, "citations": [{"section_id": sid, "quote": quote}]}
                )
        return json.dumps({"abstain": True, "answer": "", "citations": []})

    return respond


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--sources", type=Path, default=PROJECT / "data" / "sources")
    ap.add_argument("--name", default="grounded-qa")
    ap.add_argument("--mode", default="hybrid", choices=["hybrid", "keyword", "semantic"])
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--fake", action="store_true")
    args = ap.parse_args()

    cases = load_cases(args.cases)
    index_path = PROJECT / "data" / "generated" / "index.json"
    if args.fake:
        provider = FakeProvider()
        adapter = ModelAdapter(provider, model="fake-model")
        sections = build_index(args.sources, index_path, embed=adapter.embed)
        provider._responder = fake_responder_for(cases, sections)
    else:
        adapter = ModelAdapter()
        sections = build_index(args.sources, index_path, embed=adapter.embed)
    retriever = Retriever(sections, embed=adapter.embed)

    def system_fn(case: EvalCase) -> Result:
        return answer_question(adapter, retriever, case.input["question"], k=args.k, mode=args.mode)

    def scorer_fn(case: EvalCase, r: Result) -> dict:
        exp = case.expected
        gold = set(exp.get("gold_sections") or [])
        retrieved = set(r.passages)
        cited = {c.section_id for c in r.answer.citations}
        abstained = r.answer.abstain
        correct_abstain = abstained == (not exp["answerable"])
        keyword_ok = (
            bool(exp.get("must_contain")) and exp["must_contain"].casefold() in r.answer.answer.casefold()
        )
        return {
            "abstention_correct": correct_abstain,
            "false_refusal": abstained and exp["answerable"],
            "unsupported_answer": (not abstained) and (not exp["answerable"]),
            "retrieval_recall_at_k": (len(gold & retrieved) / len(gold)) if gold else 1.0,
            "citation_precision": (len(cited & gold) / len(cited))
            if cited
            else (1.0 if not exp["answerable"] else 0.0),
            "keyword_hit": keyword_ok if exp["answerable"] else True,
            "forced_abstain": r.forced_abstain,
        }

    run = run_eval(
        name=f"{args.name}-{args.mode}",
        cases=cases,
        adapter=adapter,
        system_fn=system_fn,
        scorer_fn=scorer_fn,
        out_dir=RESULTS_DIR,
    )
    print((RESULTS_DIR / f"{args.name}-{args.mode}-latest.md").read_text())
    print(f"spent ${adapter.spent_usd:.4f}; failures {run.failures}/{run.cases}")


if __name__ == "__main__":
    main()
