########################################################################
#                                                                      #
#               backend/src/grounded_qa/evals/judging.py               #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-07
Last modified on:  2026-11-07

Grades each answered case with a model judge, beside the fixed checks,
so a run says how often the two agree.

The fixed check, `correct`, looks for one accepted phrasing of every
expected fact. It is repeatable by hand, but it can miss a right answer
worded another way, and pass an answer that names the fact and gets the
rest wrong. The judge reads the answer against the case's evidence and
grades it 0, 1 or 2 by the rubric below:

- judge_score: the judge's grade.
- judge_correct: 1 when the grade is 2, a full answer.
- judge_agrees: 1 when judge_correct equals the fixed check's correct.

Only cases the service answered are judged: a refusal of an answerable
case is wrong to both, which says nothing about the judge. A judge is
itself a model, so its agreement with the fixed check is reported, never
its grade alone.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

from collections.abc import Callable
from typing import Any, Final

# Third-party
from kds.args import required
from kds.evals import EvalCase
from kds.evals.judge import judge
from kds.llm import ModelAdapter
from kds.logs import get_logger

# Local
from grounded_qa.config import SETTINGS
from grounded_qa.core.models import Answer

########################################################################
#                                                                      #
#                           Global constants                           #
#                                                                      #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the field that says whether a case is answerable, from the config")
ANSWERABLE: Final = SETTINGS.eval_answerable_field

########################################################################
#                                                                      #
#                           Local constants                            #
#                                                                      #
########################################################################
# log.debug("Sets what a full, a partial and a wrong answer are, for the judge")
RUBRIC = (
    "Score 2 when the answer gives what the reference material says in answer to the "
    "question and claims nothing the reference does not support. Score 1 when it gives part "
    "of it, or adds a claim the reference does not support. Score 0 when it is wrong, or "
    "declines a question the reference answers."
)
# log.debug("Sets the grade that counts as a full answer")
FULL = 2
# log.debug("Types a scorer: a case and its answer in, the scores out")
Scorer = Callable[[EvalCase, Answer], dict[str, Any]]


########################################################################
#                                                                      #
#                             Model judge                              #
#                                                                      #
########################################################################
# log.debug("Defines a scorer that adds the judge's grade to the fixed checks")
def with_judge(scorer: Scorer | None = None, adapter: ModelAdapter | None = None) -> Scorer:
    """Returns a scorer that also judges every answered case.

    Args:
        scorer: The fixed checks. Required.
        adapter: The adapter the judge runs on; its judge model comes
            from its settings. Required.

    Returns:
        The fixed checks' scores, and the judge's on answered cases.
    """
    # log.debug("Takes the fixed checks, which the caller must give")
    scorer = required(scorer=scorer)
    # log.debug("Takes the judge's adapter, which the caller must give")
    adapter = required(adapter=adapter)

    # log.debug("Defines the combined scorer")
    def scored(case: EvalCase | None = None, answer: Answer | None = None) -> dict[str, Any]:
        """Returns the fixed scores, and the judge's when it answered.

        Args:
            case: The case, with its expected answer. Required.
            answer: The service's answer. Required.

        Returns:
            The scores.
        """
        # log.debug("Takes the case, which the caller must give")
        case = required(case=case)
        # log.debug("Takes the answer, which the caller must give")
        answer = required(answer=answer)
        # log.debug("Runs the fixed checks")
        scores = scorer(case, answer)
        # log.debug("Returns them alone unless an answerable case was answered")
        if not (case.expected[ANSWERABLE] and scores.get("answered")):
            # log.debug("Returns the fixed scores")
            return scores
        # log.debug("Returns them with the judge's")
        return scores | judged(case, answer, adapter, fixed=scores["correct"])

    # log.debug("Returns it")
    return scored


# log.debug("Defines the judge's grade of one answer")
def judged(
    case: EvalCase | None = None,
    answer: Answer | None = None,
    adapter: ModelAdapter | None = None,
    *,
    fixed: float | None = None,
) -> dict[str, float]:
    """Returns the judge's grade and whether it agrees with `fixed`.

    Args:
        case: The case, whose evidence is the reference. Required.
        answer: The service's answer. Required.
        adapter: The adapter the judge runs on. Required.
        fixed: The fixed check's correct, 1 or 0. Required.

    Returns:
        judge_score, judge_correct and judge_agrees.
    """
    # log.debug("Takes the case, which the caller must give")
    case = required(case=case)
    # log.debug("Takes the answer, which the caller must give")
    answer = required(answer=answer)
    # log.debug("Takes the adapter, which the caller must give")
    adapter = required(adapter=adapter)
    # log.debug("Takes the fixed check's verdict, which the caller must give")
    fixed = required(fixed=fixed)
    # log.debug("Gives the judge the case's evidence as the reference, one span a line")
    reference = "\n".join(span["text"] for group in case.expected["evidence"] for span in group)
    # log.debug("Asks the judge")
    verdict = judge(
        adapter,
        {"question": answer.question, "answer": answer.answer, "reference": reference},
        RUBRIC,
    )
    # log.debug("Counts a full grade as correct")
    correct = float(verdict.score == FULL)
    # log.debug("Returns the grade, its verdict and whether the two checks agree")
    return {
        "judge_score": float(verdict.score),
        "judge_correct": correct,
        "judge_agrees": float(correct == fixed),
    }
