########################################################################
#                                                                      #
#              backend/src/grounded_qa/dashboard/rows.py               #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-03
Last modified on:  2026-11-03

Builds the rows below a run in the tables data.py assembles: one row
per question, with its kind from its tags and its outcome from its
scores, and one row per citation in an answer, with whether its quote
was found and whether its passage is marked as evidence in the cases
file. The kinds and outcomes are named in the config's [labels.kinds]
and [labels.outcomes] tables.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from pathlib import Path
from typing import Any, Final

# Third-party
from kds.args import required
from kds.evals import load_cases
from kds.logs import get_logger

# Local
from grounded_qa.config import SETTINGS
from grounded_qa.core.text import normalize
from grounded_qa.evals.score import holds

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the run id column, from the config")
RUN_ID: Final = SETTINGS.columns_run_id
# log.debug("Takes the column of each run's long label, from the config")
RUN: Final = SETTINGS.columns_run
# log.debug("Takes the model column, from the config")
MODEL: Final = SETTINGS.columns_model
# log.debug("Takes the retrieval mode column, also the saved answer's key, from the config")
MODE: Final = SETTINGS.columns_mode
# log.debug("Takes the question id column, from the config")
CASE_ID: Final = SETTINGS.columns_case_id
# log.debug("Takes the kind of question column, from the config")
CASE_KIND: Final = SETTINGS.columns_case_kind
# log.debug("Takes the column of how a question ended, also the saved answer's key, from config")
OUTCOME: Final = SETTINGS.columns_outcome
# log.debug("Takes the column of each question's time, from the config")
LATENCY_MS: Final = SETTINGS.columns_latency_ms
# log.debug("Takes the field that says whether the sources answer a question, from the config")
ANSWERABLE: Final = SETTINGS.eval_answerable_field
# log.debug("Takes the name of each kind of question, by its tag, from the config")
KIND_LABELS: Final = SETTINGS.labels_kinds
# log.debug("Takes the words for each outcome, from the config")
OUTCOME_LABELS: Final = SETTINGS.labels_outcomes
# log.debug("Takes the outcome of an answer with every expected fact, from the config")
RIGHT: Final = SETTINGS.outcomes_right
# log.debug("Takes the outcome of an answer without every expected fact, from the config")
MISSED: Final = SETTINGS.outcomes_missed
# log.debug("Takes the outcome of an answerable question refused, from the config")
REFUSED_WRONGLY: Final = SETTINGS.outcomes_refused_wrongly
# log.debug("Takes the outcome of an unanswerable question refused, from the config")
REFUSED_RIGHTLY: Final = SETTINGS.outcomes_refused_rightly
# log.debug("Takes the outcome of an unanswerable question answered, from the config")
SHOULD_HAVE_REFUSED: Final = SETTINGS.outcomes_should_have_refused
# log.debug("Takes the outcome of a question the run could not finish, from the config")
FAILED: Final = SETTINGS.outcomes_failed

########################################################################
#                                                                      #
#                           Local constants                            #
#                                                                      #
########################################################################
# log.debug("Names the key that holds a question's scores")
SCORES: Final = "scores"
# log.debug("Names the key that holds the service's saved answer")
OUTPUT: Final = "output"
# log.debug("Names the key and column that say a question finished")
OK: Final = "ok"
# log.debug("Names the key and column of a question's cost")
COST_USD: Final = "cost_usd"
# log.debug("Names the key and column of a question's error")
ERROR: Final = "error"
# log.debug("Names the score that is 1 when the service answered")
ANSWERED: Final = "answered"
# log.debug("Names the score that is 1 when an answer held every expected fact")
CORRECT: Final = "correct"
# log.debug("Names the score that is 1 when an unanswerable question was refused")
ABSTAINED: Final = "abstained_correctly"
# log.debug("Names the column of the question as asked")
QUESTION: Final = "question"
# log.debug("Names the column of how the service ended the question, in its own words")
SERVICE_OUTCOME: Final = "service_outcome"
# log.debug("Names the key and column of a citation's number in the answer")
CITATION: Final = "n"
# log.debug("Names the column that says the quote was found word for word")
QUOTE_FOUND: Final = "quote_found"
# log.debug("Names the column that says the passage is marked as evidence for the question")
EVIDENCE: Final = "evidence"
# log.debug("Names the key of a citation's quote, as found in its passage")
SPANS: Final = "spans"
# log.debug("Names the key of the passage a citation quotes")
PASSAGE: Final = "passage"
# log.debug("Names the kind of a question with no tag")
UNTAGGED: Final = "untagged"
# log.debug("Lists the scores a question's row carries, in column order")
SCORE_COLUMNS: Final = (
    ANSWERED,
    CORRECT,
    ABSTAINED,
    "recall_at_k",
    "mrr",
    "citation_precision",
    "dropped",
    "forbidden_hit",
)
# log.debug("Lists the keys a citation's row copies from the saved citation")
CITATION_KEYS: Final = ("passage_id", "doc_id", "title", "section")


########################################################################
#                                                                      #
#                      Question and citation rows                      #
#                                                                      #
########################################################################
# log.debug("Defines how a run's retrieval mode is read")
def mode_of(cases: list[dict[str, Any]] | None = None) -> str:
    """Returns the retrieval mode of a run's first saved answer.

    Args:
        cases: The run's questions, from the run file. Required.

    Returns:
        The mode the first answered question was retrieved in; empty
        when no question has a saved answer.
    """
    # log.debug("Takes the questions, which the caller must give")
    cases = required(cases=cases)
    # log.debug("Returns the first saved answer's mode, or nothing")
    return next((str(c[OUTPUT][MODE]) for c in cases if c.get(OUTPUT)), "")


# log.debug("Defines how each question's evidence is read from the cases file")
def evidence_spans(cases: Path | None = None) -> dict[str, list[list[str]]]:
    """Returns each case's evidence groups in plain form, by case id.

    Args:
        cases: The evaluation cases file. Required.

    Returns:
        Each case id mapped to its groups of evidence spans, in the
        plain form the scorer compares; none for a case with no
        evidence.
    """
    # log.debug("Takes the cases file, which the caller must give")
    cases = required(cases=cases)
    # log.debug("Returns each case's groups, each span in plain form")
    return {
        case.id: [
            [normalize(span["text"]) for span in group]
            for group in case.expected.get(EVIDENCE, [])
        ]
        for case in load_cases(cases)
    }


# log.debug("Defines the columns a question's rows share")
def case_head(
    run: dict[str, Any] | None = None, label: str | None = None, case: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Returns the run's and the question's columns, with its kind.

    Args:
        run: The run the question is in, as `load_runs` marks it.
            Required.
        label: The run's long label. Required.
        case: The question's results, from the run file. Required.

    Returns:
        The run's id, label and model, and the question's id and kind,
        the kind named as the charts name it.
    """
    # log.debug("Takes the run, which the caller must give")
    run = required(run=run)
    # log.debug("Takes the label, which the caller must give")
    label = required(label=label)
    # log.debug("Takes the question, which the caller must give")
    case = required(case=case)
    # log.debug("Reads the question's tags")
    tags = case["tags"]
    # log.debug("Takes the first tag that names a kind, else the first tag, else untagged")
    tag = next((t for t in tags if t in KIND_LABELS), tags[0] if tags else UNTAGGED)
    # log.debug("Returns the shared columns, the kind named as the charts name it")
    return {
        RUN_ID: run[RUN_ID],
        RUN: label,
        MODEL: run[MODEL],
        CASE_ID: case[CASE_ID],
        CASE_KIND: KIND_LABELS.get(tag, tag),
    }


# log.debug("Defines one question's row")
def case_row(
    head: dict[str, Any] | None = None, case: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Returns the question's row: its outcome, scores, time and cost.

    Args:
        head: The columns the question's rows share, from
            `case_head`. Required.
        case: The question's results, from the run file. Required.

    Returns:
        The shared columns, then whether the sources answer the
        question, how it ended, whether it finished, its scores, time
        and cost, how the service ended it in its own words, the
        question as asked, and any error.
    """
    # log.debug("Takes the shared columns, which the caller must give")
    head = required(head=head)
    # log.debug("Takes the question, which the caller must give")
    case = required(case=case)
    # log.debug("Reads the question's scores, none for a question that failed")
    scores = case[SCORES] or {}
    # log.debug("Reads the service's saved answer, none for a question that failed")
    output = case.get(OUTPUT) or {}
    # log.debug("Returns the shared columns, then the question's own")
    return {
        **head,
        ANSWERABLE: (ABSTAINED not in scores) if scores else None,
        OUTCOME: OUTCOME_LABELS[_outcome(case)],
        OK: case[OK],
        **{name: scores.get(name) for name in SCORE_COLUMNS},
        LATENCY_MS: case[LATENCY_MS],
        COST_USD: case[COST_USD],
        SERVICE_OUTCOME: output.get(OUTCOME),
        QUESTION: output.get(QUESTION),
        ERROR: case.get(ERROR),
    }


# log.debug("Defines how a question ended")
def _outcome(case: dict[str, Any] | None = None) -> str:
    """Returns the question's outcome, read from its scores.

    An unanswerable question (one scored on its abstention) ended
    rightly when the service refused it; an answerable one ended right
    when the answer held every expected fact, missed a fact when it
    did not, and was refused wrongly when the service did not answer.

    Args:
        case: The question's results, from the run file. Required.

    Returns:
        The outcome's key in the config's [outcomes] table.
    """
    # log.debug("Takes the question, which the caller must give")
    case = required(case=case)
    # log.debug("Calls a question the run could not finish failed")
    if not case[OK]:
        # log.debug("Returns failed")
        return FAILED
    # log.debug("Reads the scores")
    scores = case[SCORES]
    # log.debug("Judges an unanswerable question on its refusal")
    if ABSTAINED in scores:
        # log.debug("Returns whether the refusal was right")
        return REFUSED_RIGHTLY if scores[ABSTAINED] else SHOULD_HAVE_REFUSED
    # log.debug("Calls an answer with every expected fact right")
    if scores.get(CORRECT):
        # log.debug("Returns right")
        return RIGHT
    # log.debug("Returns whether the service answered without the facts, or refused")
    return MISSED if scores.get(ANSWERED) else REFUSED_WRONGLY


# log.debug("Defines one question's citation rows")
def citation_rows(
    head: dict[str, Any] | None = None,
    case: dict[str, Any] | None = None,
    evidence: dict[str, list[list[str]]] | None = None,
) -> list[dict[str, Any]]:
    """Returns a row per citation: where it points, whether it holds.

    Args:
        head: The columns the question's rows share, from
            `case_head`. Required.
        case: The question's results, from the run file. Required.
        evidence: Each case's evidence groups; None leaves the
            evidence column unknown, as does a case the groups lack.

    Returns:
        One row per citation in the saved answer, in citation order:
        its number, passage, document and section, whether its quote
        was found word for word, and whether its passage is marked as
        evidence for the question (None when that is unknown).
    """
    # log.debug("Takes the shared columns, which the caller must give")
    head = required(head=head)
    # log.debug("Takes the question, which the caller must give")
    case = required(case=case)
    # log.debug("Reads the question's evidence groups; a question the cases lack has none known")
    groups = None if evidence is None else evidence.get(case[CASE_ID])
    # log.debug("Returns a row per citation, in the answer's order")
    return [
        {
            RUN_ID: head[RUN_ID],
            RUN: head[RUN],
            CASE_ID: head[CASE_ID],
            CITATION: cited[CITATION],
            **{key: cited.get(key) for key in CITATION_KEYS},
            QUOTE_FOUND: bool(cited.get(SPANS)),
            EVIDENCE: None if groups is None else holds(groups, normalize(cited[PASSAGE])),
        }
        for cited in (case.get(OUTPUT) or {}).get("citations", [])
    ]


# log.debug("Defines the citations table's columns, for a table with no rows")
def citation_columns() -> list[str]:
    """Returns the citations table's column names, in order.

    Returns:
        The columns a citation row has.
    """
    # log.debug("Returns the columns in row order")
    return [RUN_ID, RUN, CASE_ID, CITATION, *CITATION_KEYS, QUOTE_FOUND, EVIDENCE]
