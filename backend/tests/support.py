########################################################################
#                                                                      #
#                       backend/tests/support.py                       #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-11-03

The helpers and values tests share: where the repository's data is,
an approver token, two small sources, helpers that build and write
sources with true hashes, and the made-up runs and cases the dashboard
tests draw. Fixtures live in conftest.py.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

# Third-party
from kds.args import required
from kds.logs import get_logger

# Local
from grounded_qa.core import sources
from grounded_qa.core.sources import Source

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)

########################################################################
#                                                                      #
#                           Local constants                            #
#                                                                      #
########################################################################
# log.debug("Points at the repository root, two folders above this one")
REPO = Path(__file__).resolve().parents[2]
# log.debug("Sets a token long enough for the approver check")
TOKEN = "approver-token-for-tests-only-00000000"
# log.debug("Sets the text of a small FMLA source")
LEAVE_BODY = (
    "The FMLA provides job-protected leave.\n\n"
    "## Using leave\n\n"
    "Eligible employees may take up to 12 workweeks of leave in a 12-month period.\n\n"
    "## Pay\n\n"
    "FMLA is job-protected, unpaid leave. Employees may use paid leave at the same time.\n"
)
# log.debug("Sets the text of a small overtime source")
OVERTIME_BODY = (
    "## Requirements\n\n"
    "Covered employees must receive overtime pay for hours worked over 40 in a workweek.\n\n"
    "The overtime requirement may not be waived by agreement between the employer and employees.\n"
)
# log.debug("Sets the passage a made-up run's citations quote")
LEAVE_PASSAGE = "Eligible employees may take up to 12 workweeks of leave in a 12-month period."
# log.debug("Sets a passage that holds no evidence for any made-up question")
PAY_PASSAGE = "FMLA is job-protected, unpaid leave. Employees may use paid leave at the same time."
# log.debug("Sets the service's saved answer when it answered")
ANSWERED_OUTPUT: dict[str, Any] = {
    "question": "How many weeks of leave can an eligible employee take?",
    "answer": "Up to 12 workweeks in a 12-month period. [1]",
    "outcome": "answered",
    "citations": [
        {
            "n": 1,
            "passage_id": "leave#1",
            "doc_id": "leave",
            "title": "Test source leave",
            "section": "Using leave",
            "url": "https://example.com/leave",
            "revised": "January 2026",
            "quote": "up to 12 workweeks of leave in a 12-month period",
            "passage": LEAVE_PASSAGE,
            "spans": [[27, 76]],
        }
    ],
    "dropped": 0,
    "retrieved": [{"passage_id": "leave#1", "doc_id": "leave", "score": 0.5}],
    "model": "test-model",
    "prompt_version": "2026-10-29",
    "mode": "keyword",
    "request_id": "t:q-direct",
}
# log.debug("Sets the service's saved answer when it refused")
REFUSED_OUTPUT: dict[str, Any] = {
    **ANSWERED_OUTPUT,
    "question": "Can I take leave to care for my mother-in-law?",
    "answer": "The passages do not cover this question.",
    "outcome": "not_covered",
    "citations": [],
    "retrieved": [],
    "request_id": "t:q-everyday",
}
# log.debug("Sets a live run of three questions: one right, one refused wrongly, one rightly")
RUN: dict[str, Any] = {
    "name": "t",
    "model": "test-model",
    "provider": "anthropic",
    "started_at": "2026-10-15T00:00:00+00:00",
    "finished_at": "2026-10-15T00:00:01+00:00",
    "prices_as_of": "2026-10-15",
    "cases": 3,
    "failures": 0,
    "summary": {
        "correct": 0.5,
        "answered": 0.5,
        "abstained_correctly": 1.0,
        "citation_precision": 1.0,
        "recall_at_k": 0.5,
        "mrr": 0.5,
        "dropped": 0.0,
        "forbidden_hit": 0.0,
        "latency_p50_ms": 10,
        "latency_p95_ms": 12,
        "cost_total_usd": 0.003,
        "cost_per_case_usd": 0.001,
        "failure_rate": 0.0,
    },
    "results": [
        {
            "case_id": "q-direct",
            "tags": ["fmla", "direct"],
            "ok": True,
            "scores": {
                "forbidden_hit": 0.0,
                "dropped": 0,
                "answered": 1.0,
                "correct": 1.0,
                "recall_at_k": 1.0,
                "mrr": 1.0,
                "citation_precision": 1.0,
            },
            "output": ANSWERED_OUTPUT,
            "error": None,
            "latency_ms": 10,
            "cost_usd": 0.001,
            "calls": 1,
        },
        {
            "case_id": "q-everyday",
            "tags": ["fmla", "paraphrased"],
            "ok": True,
            "scores": {
                "forbidden_hit": 0.0,
                "dropped": 0,
                "answered": 0.0,
                "correct": 0.0,
                "recall_at_k": 0.0,
                "mrr": 0.0,
            },
            "output": REFUSED_OUTPUT,
            "error": None,
            "latency_ms": 12,
            "cost_usd": 0.001,
            "calls": 1,
        },
        {
            "case_id": "q-unanswerable",
            "tags": ["unanswerable"],
            "ok": True,
            "scores": {"forbidden_hit": 0.0, "dropped": 0, "abstained_correctly": 1.0},
            "output": {**REFUSED_OUTPUT, "request_id": "t:q-unanswerable"},
            "error": None,
            "latency_ms": 8,
            "cost_usd": 0.001,
            "calls": 1,
        },
    ],
}
# log.debug("Sets the cases behind the made-up runs, with the evidence their answers must cite")
CASES: list[dict[str, Any]] = [
    {
        "id": "q-direct",
        "input": {"question": ANSWERED_OUTPUT["question"]},
        "expected": {
            "answerable": True,
            "facts": [["12 workweeks"]],
            "evidence": [[{"doc": "leave", "text": "up to 12 workweeks of leave"}]],
            "forbidden": [],
        },
        "tags": ["fmla", "direct"],
    },
    {
        "id": "q-everyday",
        "input": {"question": REFUSED_OUTPUT["question"]},
        "expected": {
            "answerable": True,
            "facts": [["12 workweeks"]],
            "evidence": [[{"doc": "leave", "text": "up to 12 workweeks of leave"}]],
            "forbidden": [],
        },
        "tags": ["fmla", "paraphrased"],
    },
    {
        "id": "q-unanswerable",
        "input": {"question": "Does the law cover my state?"},
        "expected": {"answerable": False, "facts": [], "evidence": [], "forbidden": []},
        "tags": ["unanswerable"],
    },
]


########################################################################
#                                                                      #
#                             Test helpers                             #
#                                                                      #
########################################################################
# log.debug("Defines a helper that builds a source with a true hash")
def make_source(source_id: str | None = None, body: str | None = None, **fields: Any) -> Source:
    """Returns a valid Source; `fields` override the front matter.

    Args:
        source_id: The source's id. Required.
        body: The source's text. Required.
        **fields: Front-matter fields to set instead of the defaults.

    Returns:
        The source, its SHA-256 taken from `body`.
    """
    # log.debug("Takes the source id, which the caller must give")
    source_id = required(source_id=source_id)
    # log.debug("Takes the body, which the caller must give")
    body = required(body=body)
    # log.debug("Returns the source with defaults for every field")
    return Source(
        **{
            "id": source_id,
            "title": f"Test source {source_id}",
            "publisher": "Test publisher",
            "source": f"https://example.com/{source_id}",
            "revised": "January 2026",
            "retrieved": "2026-10-29",
            "license": "Public domain",
            "sha256": sources.digest(body),
            "body": body,
        }
        | fields
    )


# log.debug("Defines a helper that writes a source file")
def write_source(folder: Path | None = None, source: Source | None = None) -> Path:
    """Writes `source` as a document in `folder`; returns its path.

    Args:
        folder: The folder to write into, made if missing. Required.
        source: The source to write. Required.

    Returns:
        The document's path.
    """
    # log.debug("Takes the folder, which the caller must give")
    folder = required(folder=folder)
    # log.debug("Takes the source, which the caller must give")
    source = required(source=source)
    # log.debug("Creates the folder")
    folder.mkdir(parents=True, exist_ok=True)
    # log.debug("Names the file for the id")
    path = folder / f"{source.id}.md"
    # log.debug("Writes the document")
    path.write_text(sources.render(source), encoding="utf-8")
    # log.debug("Returns the path")
    return path


# log.debug("Defines a results folder holding the one run")
def one_run(tmp_path: Path | None = None) -> Path:
    """Writes RUN as the only run, and returns the results folder.

    Args:
        tmp_path: The test's temporary folder. Required.

    Returns:
        The results folder.
    """
    # log.debug("Takes the test's folder, which the caller must give")
    tmp_path = required(tmp_path=tmp_path)
    # log.debug("Makes the results folder")
    results = tmp_path / "results"
    # log.debug("Creates it")
    results.mkdir()
    # log.debug("Writes the run")
    (results / "t-1.json").write_text(json.dumps(RUN), encoding="utf-8")
    # log.debug("Returns the folder")
    return results


# log.debug("Defines a results folder holding two runs an hour apart")
def two_runs(tmp_path: Path | None = None) -> Path:
    """Writes RUN and a later hybrid run: more answered, dearer.

    The later run, an hour after, answers the everyday-words question
    rightly, citing one passage that holds evidence and one that does
    not.

    Args:
        tmp_path: The test's temporary folder. Required.

    Returns:
        The results folder, holding both runs.
    """
    # log.debug("Takes the test's folder, which the caller must give")
    tmp_path = required(tmp_path=tmp_path)
    # log.debug("Copies the run")
    later = copy.deepcopy(RUN)
    # log.debug("Starts it an hour later")
    later["started_at"] = "2026-10-15T01:00:00+00:00"
    # log.debug("Gives it every answerable question right and a higher cost")
    later["summary"] = {
        **RUN["summary"],
        "correct": 1.0,
        "answered": 1.0,
        "citation_precision": 0.75,
        "cost_per_case_usd": 0.002,
    }
    # log.debug("Answers the everyday-words question, with two citations")
    later["results"][1]["scores"] = {**RUN["results"][0]["scores"], "citation_precision": 0.5}
    # log.debug("Cites the evidence passage and one that holds none")
    later["results"][1]["output"] = {
        **ANSWERED_OUTPUT,
        "citations": [
            ANSWERED_OUTPUT["citations"][0],
            {
                **ANSWERED_OUTPUT["citations"][0],
                "n": 2,
                "passage_id": "leave#2",
                "passage": PAY_PASSAGE,
            },
        ],
    }
    # log.debug("Retrieves in hybrid mode")
    for case in later["results"]:
        # log.debug("Marks one answer")
        case["output"] = {**case["output"], "mode": "hybrid"}
    # log.debug("Makes the results folder")
    results = tmp_path / "results"
    # log.debug("Creates it")
    results.mkdir()
    # log.debug("Writes the earlier run, with its cost")
    (results / "t-1.json").write_text(
        json.dumps({**RUN, "summary": {**RUN["summary"], "cost_per_case_usd": 0.0015}}),
        encoding="utf-8",
    )
    # log.debug("Writes the later run")
    (results / "t-2.json").write_text(json.dumps(later), encoding="utf-8")
    # log.debug("Returns the folder")
    return results


# log.debug("Defines the cases file behind the made-up runs")
def write_cases(tmp_path: Path | None = None) -> Path:
    """Writes CASES as a cases file, and returns its path.

    Args:
        tmp_path: The test's temporary folder. Required.

    Returns:
        The cases file.
    """
    # log.debug("Takes the test's folder, which the caller must give")
    tmp_path = required(tmp_path=tmp_path)
    # log.debug("Names the file")
    path = tmp_path / "cases.jsonl"
    # log.debug("Writes one case per line")
    path.write_text("".join(json.dumps(case) + "\n" for case in CASES), encoding="utf-8")
    # log.debug("Returns the path")
    return path


# log.debug("Defines a live run of questions that are all right")
def write_run(
    results: Path | None = None,
    name: str | None = None,
    started: str | None = None,
    latencies_ms: list[int] | None = None,
    cost: float | None = None,
) -> None:
    """Writes a run with the given times and one cost per question.

    Args:
        results: The results folder, made if need be. Required.
        name: The run file's name, without .json. Required.
        started: When the run started, as an ISO time. Required.
        latencies_ms: Each question's time, in milliseconds. Required.
        cost: Every question's cost, in dollars. Required.
    """
    # log.debug("Takes the results folder, which the caller must give")
    results = required(results=results)
    # log.debug("Takes the run's name, which the caller must give")
    name = required(name=name)
    # log.debug("Takes the start time, which the caller must give")
    started = required(started=started)
    # log.debug("Takes the times, which the caller must give")
    latencies_ms = required(latencies_ms=latencies_ms)
    # log.debug("Takes the cost, which the caller must give")
    cost = required(cost=cost)
    # log.debug("Copies the run")
    run = copy.deepcopy(RUN)
    # log.debug("Sets its start")
    run["started_at"] = started
    # log.debug("Takes the first question, which was right, as the pattern")
    base = run["results"][0]
    # log.debug("Makes one question per time")
    run["results"] = [
        {**copy.deepcopy(base), "case_id": f"q-{i:03d}", "latency_ms": ms, "cost_usd": cost}
        for i, ms in enumerate(latencies_ms)
    ]
    # log.debug("Counts the questions")
    run["cases"] = len(latencies_ms)
    # log.debug("Writes the summary to match")
    run["summary"] = {
        **RUN["summary"],
        "correct": 1.0,
        "answered": 1.0,
        "latency_p50_ms": sorted(latencies_ms)[len(latencies_ms) // 2],
        "cost_per_case_usd": cost,
    }
    # log.debug("Makes the results folder if it is not there yet")
    results.mkdir(exist_ok=True)
    # log.debug("Writes the run")
    (results / f"{name}.json").write_text(json.dumps(run), encoding="utf-8")
