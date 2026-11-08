########################################################################
#                                                                      #
#                     backend/tests/test_evals.py                      #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-11-08

Tests the gold cases are sound, and that the scorers and both kinds of
run work end to end, offline.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from typing import Any

# Third-party
from kds.args import required
from kds.evals import EvalCase, load_cases
from kds.llm import ModelAdapter
from kds.llm.fake import FakeProvider
from kds.logs import get_logger

# Local
from grounded_qa.config import AppSettings
from grounded_qa.core.chunk import Passage
from grounded_qa.core.models import Answer, Citation, Retrieved
from grounded_qa.core.retrieve import Retriever
from grounded_qa.core.sources import load_dir
from grounded_qa.core.text import normalize
from grounded_qa.evals import retrieval
from grounded_qa.evals.judging import Scorer, reference, with_judge
from grounded_qa.evals.run import corpus, run_answers, run_retrieval, scorer_for
from grounded_qa.evals.score import score
from support import REPO

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


########################################################################
#                                                                      #
#                           Evaluation tests                           #
#                                                                      #
########################################################################
# log.debug("Defines the cases every test here reads")
def _cases() -> list[EvalCase]:
    """Returns the repository's gold cases.

    Returns:
        The cases in data/evals/cases.jsonl, in order.
    """
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
def _answer(text: str | None = None, outcome: Any = None, cited: bool | None = None) -> Answer:
    """Returns an answer that showed PASSAGE and maybe cited it.

    Args:
        text: The answer's text. Required.
        outcome: How the question ended, as Answer names it.
            Required.
        cited: Whether the answer cites PASSAGE. Required.

    Returns:
        The answer, with PASSAGE the one passage shown.
    """
    # log.debug("Takes the text, which the caller must give")
    text = required(text=text)
    # log.debug("Takes the outcome, which the caller must give")
    outcome = required(outcome=outcome)
    # log.debug("Takes whether to cite, which the caller must give")
    cited = required(cited=cited)
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


# log.debug("Defines the case every judging test scores")
def _leave_case() -> EvalCase:
    """Returns an answerable case that expects 12 workweeks.

    Returns:
        The case, with one evidence span.
    """
    # log.debug("Returns the case")
    return EvalCase(
        id="c",
        input={"question": "q"},
        expected={
            "answerable": True,
            "facts": [["12 workweeks", "12 weeks"]],
            "evidence": [[{"doc": "leave", "text": "up to 12 workweeks of leave"}]],
        },
    )


# log.debug("Defines a judge that gives the scripted grades in turn")
def _judge(*grades: int) -> ModelAdapter:
    """Returns an adapter whose model answers each grade, in order.

    Args:
        *grades: The judge's grades, one a call.

    Returns:
        The adapter, which never sleeps.
    """
    # log.debug("Returns an adapter over the scripted verdicts")
    return ModelAdapter(
        FakeProvider([f'{{"score": {g}, "reason": "as scripted"}}' for g in grades]),
        model="fake-judge",
        sleep=lambda _: None,
    )


# log.debug("Defines the test that the judge grades an answered case beside the fixed check")
def test_the_judge_agrees_or_not_with_the_fixed_check() -> None:
    """A full grade agrees with a right answer; a partial one not."""
    # log.debug("Builds the fixed checks over the cited passage")
    fixed = _fixed_checks()
    # log.debug("Builds a correct, cited answer")
    answer = _answer("Up to 12 workweeks [1].", "answered", True)
    # log.debug("Scores it twice, with a judge that gives 2, then 1")
    scored = with_judge(fixed, _judge(2, 1))
    # log.debug("Takes both rounds of scores")
    first, second = scored(_leave_case(), answer), scored(_leave_case(), answer)
    # log.debug("Checks the full grade agrees with the fixed check")
    assert (first["judge_score"], first["judge_correct"], first["judge_agrees"]) == (2.0, 1.0, 1.0)
    # log.debug("Checks the partial grade does not")
    assert (second["judge_correct"], second["judge_agrees"]) == (0.0, 0.0)


# log.debug("Defines the test of what the judge reads the answer against")
def test_the_judge_reads_each_part_and_each_cited_passage_under_all_its_numbers() -> None:
    """Alternatives as one part; a passage cited twice shown once."""
    # log.debug("Gives the case's one part a second source's wording")
    case = EvalCase(
        id="c",
        input={"question": "q"},
        expected={
            "answerable": True,
            "facts": [["12 workweeks"]],
            "evidence": [
                [
                    {"doc": "leave", "text": "up to 12 workweeks of leave"},
                    {"doc": "rights", "text": "12 workweeks of job-protected leave"},
                ]
            ],
        },
    )
    # log.debug("Builds an answer that cites the passage")
    answer = _answer("Up to 12 workweeks [1], for eligible employees [2].", "answered", True)
    # log.debug("Cites the same passage again, as [2]")
    again = answer.citations[0].model_copy(update={"n": 2})
    # log.debug("Writes the reference for the answer citing it twice")
    text = reference(case, answer.model_copy(update={"citations": (*answer.citations, again)}))
    # log.debug("Checks the one part with its alternative, then the passage once under both")
    assert (
        "1. up to 12 workweeks of leave\n   or: 12 workweeks of job-protected leave" in text,
        text.count(PASSAGE.text),
        f"[1][2] {PASSAGE.title}," in text,
        text.index("job-protected") < text.index(PASSAGE.text),
    ) == (True, 1, True, True)


# log.debug("Defines the test that cases the service did not answer are not judged")
def test_unanswered_and_unanswerable_cases_are_not_judged() -> None:
    """No grade or judge call for a refusal or an unanswerable case."""
    # log.debug("Builds a judge, which must not be called")
    judge = _judge()
    # log.debug("Builds the scorer with it")
    scored = with_judge(_fixed_checks(), judge)
    # log.debug("Scores a refusal of the answerable case")
    refused = scored(_leave_case(), _answer("Not covered.", "not_covered", False))
    # log.debug("Scores an unanswerable case")
    unanswerable = scored(
        EvalCase(id="u", input={"question": "q"}, expected={"answerable": False}),
        _answer("Not covered.", "not_covered", False),
    )
    # log.debug("Checks neither has a grade and the judge was never called")
    assert not any("judge_score" in s for s in (refused, unanswerable)) and not judge.calls


# log.debug("Defines the test that an offline run skips the judge")
def test_an_offline_run_skips_the_judge(real_settings: AppSettings) -> None:
    """With the judge on and the stand-in answering, only fixed checks.

    Args:
        real_settings: Settings over the real sources, from conftest.
    """
    # log.debug("Turns the judge on, offline")
    settings = real_settings.model_copy(update={"eval_judge": True})
    # log.debug("Scores a correct answer with the scorer the run would use")
    got = scorer_for(settings, {PASSAGE.id: PASSAGE})(
        _leave_case(), _answer("Up to 12 workweeks [1].", "answered", True)
    )
    # log.debug("Checks no judge score was added")
    assert "judge_score" not in got and got["correct"] == 1.0


# log.debug("Defines the fixed checks the judging tests start from")
def _fixed_checks() -> Scorer:
    """Returns the fixed checks, bound to the cited passage.

    Returns:
        The scorer, taking a case and an answer.
    """
    # log.debug("Returns the scorer, with no canaries")
    return lambda case, answer: score(case, answer, {PASSAGE.id: PASSAGE}, ())


# log.debug("Defines the end-to-end offline run")
def test_offline_answer_run_writes_results(real_settings: AppSettings) -> None:
    """The stand-in answers five real cases; results are written.

    Args:
        real_settings: Settings over the repository's data.
    """
    # log.debug("Runs five cases with the stand-in")
    line = run_answers(real_settings, "keyword", "offline-test", 5)
    # log.debug("Checks the summary and the files")
    assert line.startswith("offline-test: 5 cases, 0 failures")
    # log.debug("Checks the latest report exists")
    assert (real_settings.data_results / "offline-test-latest.md").is_file()


# log.debug("Defines the retrieval run over the real corpus")
def test_keyword_retrieval_finds_most_evidence(real_settings: AppSettings) -> None:
    """Keyword search puts evidence in the top 10 for most questions.

    Args:
        real_settings: Settings over the repository's data.
    """
    # log.debug("Runs the retrieval evaluation in keyword mode")
    table = run_retrieval(real_settings, ["keyword"], "retrieval-test")
    # log.debug("Scores the rows directly too")
    rows = retrieval.evaluate(_cases(), _retriever(real_settings))
    # log.debug("Checks the table names the mode and recall is high")
    assert (
        "| keyword | all (45) |" in table and retrieval.summarise(rows, bool)["recall_at_10"] > 0.8
    )


# log.debug("Defines a keyword retriever over the evaluation corpus")
def _retriever(settings: AppSettings | None = None) -> Retriever:
    """Returns a keyword retriever over the sources and samples.

    Args:
        settings: The settings that name the data and the mode.
            Required.

    Returns:
        A retriever over every passage the evaluation searches.
    """
    # log.debug("Takes the settings, which the caller must give")
    settings = required(settings=settings)
    # log.debug("Returns the retriever")
    return Retriever(corpus(settings), settings)
