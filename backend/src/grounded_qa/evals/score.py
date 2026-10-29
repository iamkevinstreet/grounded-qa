########################################################################
#                backend/src/grounded_qa/evals/score.py                #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

Scores one answer against its case with fixed checks a reader can
repeat by hand: correct facts, evidence found and cited, abstentions.

For a question the sources answer:
- answered: 1 when the service answered rather than abstained.
- correct: 1 when it answered and the answer holds one accepted
  phrasing from every group in expected.facts.
- recall_at_k: the share of evidence groups with a span inside the
  passages the model was shown.
- mrr: 1 / the rank of the first shown passage holding evidence.
- citation_precision: the share of citations whose passage holds
  evidence (answered cases only).

For a question they do not answer, abstained_correctly is 1 when the
service abstained. Every case scores forbidden_hit: 1 when the answer
repeats a forbidden phrase or a canary planted in data/samples.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

from typing import Any, Final

# Third-party
from kds.args import required
from kds.evals import EvalCase
from kds.logs import get_logger

# Local
from grounded_qa.config import SETTINGS
from grounded_qa.core.chunk import Passage
from grounded_qa.core.models import Answer
from grounded_qa.core.text import normalize

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the field that says whether a case is answerable, from the config")
ANSWERABLE: Final = SETTINGS.eval_answerable_field


########################################################################
#                            Answer scores                             #
########################################################################
# log.debug("Defines the scores of one answer")
def score(
    case: EvalCase | None = None,
    answer: Answer | None = None,
    passages: dict[str, Passage] | None = None,
    canaries: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Returns the case's scores; see the module docstring for each.

    Args:
        case: The case, with its expected answer. Required.
        answer: The service's answer. Required.
        passages: Every passage the run searched, by id. Required.
        canaries: Phrases planted in data/samples that no answer may
            repeat. Required.

    Returns:
        The case's scores, named as above.
    """
    # log.debug("Takes the case, which the caller must give")
    case = required(case=case)
    # log.debug("Takes the answer, which the caller must give")
    answer = required(answer=answer)
    # log.debug("Takes the passages, which the caller must give")
    passages = required(passages=passages)
    # log.debug("Takes the canaries, which the caller must give")
    canaries = required(canaries=canaries)
    # log.debug("Puts the answer in plain form for phrase checks")
    text = normalize(answer.answer)
    # log.debug("Lists the phrases this answer must never contain")
    forbidden = [*case.expected.get("forbidden", []), *canaries]
    # log.debug("Scores whether a forbidden phrase got through")
    scores: dict[str, Any] = {
        "forbidden_hit": float(any(normalize(p) in text for p in forbidden)),
        "dropped": answer.dropped,
    }
    # log.debug("Scores an unanswerable case on its abstention alone")
    if not case.expected[ANSWERABLE]:
        # log.debug("Returns the scores with whether it abstained")
        return scores | {"abstained_correctly": float(answer.abstained)}
    # log.debug("Reads the evidence groups in plain form")
    groups = [[normalize(span["text"]) for span in group] for group in case.expected["evidence"]]
    # log.debug("Reads the passages the model was shown, in rank order")
    shown = [normalize(passages[r.passage_id].text) for r in answer.retrieved]
    # log.debug("Adds the answer, retrieval and citation scores")
    scores |= {
        "answered": float(not answer.abstained),
        "correct": float(not answer.abstained and has_facts(text, case.expected["facts"])),
        "recall_at_k": recall(groups, shown),
        "mrr": reciprocal_rank(groups, shown),
    }
    # log.debug("Adds citation precision when the service answered")
    if not answer.abstained and answer.citations:
        # log.debug("Scores the share of citations whose passage holds evidence")
        scores["citation_precision"] = sum(
            holds(groups, normalize(c.passage)) for c in answer.citations
        ) / len(answer.citations)
    # log.debug("Returns the scores")
    return scores


# log.debug("Defines the check that an answer states the expected facts")
def has_facts(text: str | None = None, facts: list[list[str]] | None = None) -> bool:
    """Returns True when every group has a phrasing found in the text.

    Args:
        text: The answer, in plain form. Required.
        facts: Groups of accepted phrasings. Required.

    Returns:
        True when the text holds one phrasing from every group.
    """
    # log.debug("Takes the text, which the caller must give")
    text = required(text=text)
    # log.debug("Takes the facts, which the caller must give")
    facts = required(facts=facts)
    # log.debug("Returns whether each group has a match")
    return all(any(normalize(phrase) in text for phrase in group) for group in facts)


# log.debug("Defines the check that a passage holds any evidence")
def holds(groups: list[list[str]] | None = None, passage: str | None = None) -> bool:
    """Returns True when the passage contains a span from any group.

    Args:
        groups: Evidence groups of spans, in plain form. Required.
        passage: A passage, in plain form. Required.

    Returns:
        True when any span is in the passage.
    """
    # log.debug("Takes the evidence groups, which the caller must give")
    groups = required(groups=groups)
    # log.debug("Takes the passage, which the caller must give")
    passage = required(passage=passage)
    # log.debug("Returns whether any span is in the passage")
    return any(span in passage for group in groups for span in group)


# log.debug("Defines retrieval recall")
def recall(groups: list[list[str]] | None = None, shown: list[str] | None = None) -> float:
    """Returns the share of groups with a span in any shown passage.

    Args:
        groups: Evidence groups of spans, in plain form. Required.
        shown: The passages the model was shown, in plain form.
            Required.

    Returns:
        The share of groups found, from 0 to 1; 0 when there are no
        groups.
    """
    # log.debug("Takes the evidence groups, which the caller must give")
    groups = required(groups=groups)
    # log.debug("Takes the passages shown, which the caller must give")
    shown = required(shown=shown)
    # log.debug("Returns zero for a case without evidence groups")
    if not groups:
        # log.debug("Returns zero")
        return 0.0
    # log.debug("Returns the share of groups found")
    return sum(any(span in p for span in group for p in shown) for group in groups) / len(groups)


# log.debug("Defines the reciprocal rank of the first evidence passage")
def reciprocal_rank(
    groups: list[list[str]] | None = None, shown: list[str] | None = None
) -> float:
    """Returns 1 / the rank of the first evidence passage, or 0.

    Args:
        groups: Evidence groups of spans, in plain form. Required.
        shown: The passages the model was shown, in plain form and
            rank order. Required.

    Returns:
        1 / the rank of the first passage holding evidence, or 0 when
        none does.
    """
    # log.debug("Takes the evidence groups, which the caller must give")
    groups = required(groups=groups)
    # log.debug("Takes the passages shown, which the caller must give")
    shown = required(shown=shown)
    # log.debug("Returns at the first passage that holds evidence")
    for rank, passage in enumerate(shown, start=1):
        # log.debug("Checks this passage")
        if holds(groups, passage):
            # log.debug("Returns one over its rank")
            return 1 / rank
    # log.debug("Returns zero when none does")
    return 0.0
