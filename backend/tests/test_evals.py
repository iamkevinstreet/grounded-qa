########################################################################
#                     backend/tests/test_evals.py                      #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Tests the gold cases are sound and the scorers   #
#                     and runs work end to end, offline.               #
########################################################################
"""Tests for grounded_qa.evals and data/evals/cases.jsonl."""

from __future__ import annotations

from typing import Any

from kds.evals import EvalCase, load_cases
from kds.logs import get_logger

from grounded_qa.config import AppSettings
from grounded_qa.core.chunk import Passage
from grounded_qa.core.models import Answer, Citation, Retrieved
from grounded_qa.core.retrieve import Retriever
from grounded_qa.core.sources import load_dir
from grounded_qa.core.text import normalize
from grounded_qa.evals import retrieval
from grounded_qa.evals.run import corpus, run_answers, run_retrieval
from grounded_qa.evals.score import score

from support import REPO

# Module constants
log = get_logger(__name__)
# log.debug("Lists the tags a case may carry")
TAGS = {
    "fmla",
    "flsa",
    "pump",
    "retaliation",
    "direct",
    "paraphrased",
    "unanswerable",
    "adversarial",
    "false-premise",
    "injection",
    "advice",
}
# log.debug("Sets a passage the scoring tests cite")
PASSAGE = Passage(
    id="leave#2",
    doc_id="leave",
    title="Leave",
    section="",
    text="Eligible employees may take up to 12 workweeks of leave.",
    url="https://example.com/leave",
    revised="2026",
)


# log.debug("Defines the cases every test here reads")
def _cases() -> list[EvalCase]:
    """Return the repository's gold cases."""
    # log.debug("Loads the case file")
    return load_cases(REPO / "data" / "evals" / "cases.jsonl")


# log.debug("Defines the test that every evidence span is real")
def test_every_evidence_span_is_in_its_source() -> None:
    """Each span is in the document it names, word for word."""
    # log.debug("Reads each approved source in plain form")
    texts = {s.id: normalize(s.body) for s in load_dir(REPO / "data" / "sources")}
    # log.debug("Collects every span that is missing from its document")
    missing = [
        (case.id, span["text"])
        for case in _cases()
        for group in case.expected.get("evidence", [])
        for span in group
        if normalize(span["text"]) not in texts[span["doc"]]
    ]
    # log.debug("Checks there are none")
    assert missing == []


# log.debug("Defines the test that the cases are well formed")
def test_cases_are_well_formed() -> None:
    """Answerable cases have facts and evidence; tags are known."""
    # log.debug("Reads the cases")
    cases = _cases()
    # log.debug("Checks the answerable ones have both")
    assert all(
        c.expected["facts"] and c.expected["evidence"] for c in cases if c.expected["answerable"]
    )
    # log.debug("Checks every tag is one the reports know")
    assert {t for c in cases for t in c.tags} <= TAGS


# log.debug("Defines an answer for the scoring tests")
def _answer(text: str, outcome: Any, cited: bool) -> Answer:
    """Return an answer that showed PASSAGE and maybe cited it."""
    # log.debug("Builds the citation when asked")
    citations = (
        (
            Citation(
                n=1,
                passage_id=PASSAGE.id,
                doc_id=PASSAGE.doc_id,
                title=PASSAGE.title,
                section="",
                url=PASSAGE.url,
                revised=PASSAGE.revised,
                quote="up to 12 workweeks of leave",
                passage=PASSAGE.text,
            ),
        )
        if cited
        else ()
    )
    # log.debug("Returns the answer")
    return Answer(
        question="q",
        answer=text,
        outcome=outcome,
        citations=citations,
        retrieved=(Retrieved(passage_id=PASSAGE.id, doc_id=PASSAGE.doc_id, score=1.0),),
        prompt_version="v",
        mode="keyword",
        request_id="r",
    )


# log.debug("Defines the test of a correct, cited answer's scores")
def test_score_of_a_correct_cited_answer() -> None:
    """Facts found, evidence shown first and cited: all ones."""
    # log.debug("Builds a case that expects 12 workweeks")
    case = EvalCase(
        id="c",
        input={"question": "q"},
        expected={
            "answerable": True,
            "facts": [["12 workweeks", "12 weeks"]],
            "evidence": [[{"doc": "leave", "text": "up to 12 workweeks of leave"}]],
        },
    )
    # log.debug("Scores a matching answer")
    got = score(
        case, _answer("Up to 12 workweeks [1].", "answered", True), {"leave#2": PASSAGE}, ()
    )
    # log.debug("Checks every score")
    assert got == {
        "forbidden_hit": 0.0,
        "dropped": 0,
        "answered": 1.0,
        "correct": 1.0,
        "recall_at_k": 1.0,
        "mrr": 1.0,
        "citation_precision": 1.0,
    }


# log.debug("Defines the test of an unanswerable case's scores")
def test_score_of_an_abstention_and_a_canary() -> None:
    """Abstaining scores 1; a repeated canary is a forbidden hit."""
    # log.debug("Builds a case the sources do not answer")
    case = EvalCase(id="u", input={"question": "q"}, expected={"answerable": False})
    # log.debug("Scores an abstention that repeats a canary")
    got = score(case, _answer("Not covered. KESTREL-9", "not_covered", False), {}, ("KESTREL-9",))
    # log.debug("Checks both scores")
    assert (got["abstained_correctly"], got["forbidden_hit"]) == (1.0, 1.0)


# log.debug("Defines the end-to-end offline run")
def test_offline_answer_run_writes_results(real_settings: AppSettings) -> None:
    """The stand-in answers five real cases; results are written."""
    # log.debug("Runs five cases with the stand-in")
    line = run_answers(real_settings, "keyword", "offline-test", 5)
    # log.debug("Checks the summary and the files")
    assert line.startswith("offline-test: 5 cases, 0 failures")
    # log.debug("Checks the latest report exists")
    assert (real_settings.data_results / "offline-test-latest.md").is_file()


# log.debug("Defines the retrieval run over the real corpus")
def test_keyword_retrieval_finds_most_evidence(real_settings: AppSettings) -> None:
    """Keyword search puts evidence in the top 10 for most questions."""
    # log.debug("Runs the retrieval evaluation in keyword mode")
    table = run_retrieval(real_settings, ["keyword"], "retrieval-test")
    # log.debug("Scores the rows directly too")
    rows = retrieval.evaluate(_cases(), _retriever(real_settings))
    # log.debug("Checks the table names the mode and recall is high")
    assert (
        "| keyword | all (45) |" in table and retrieval.summarise(rows, bool)["recall_at_10"] > 0.8
    )


# log.debug("Defines a keyword retriever over the evaluation corpus")
def _retriever(settings: AppSettings) -> Retriever:
    """Return a keyword retriever over the sources and samples."""
    # log.debug("Returns the retriever")
    return Retriever(corpus(settings), settings)
