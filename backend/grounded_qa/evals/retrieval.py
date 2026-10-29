########################################################################
#                backend/grounded_qa/evals/retrieval.py                #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Measures retrieval alone, no model needed:       #
#                     recall at 1, 3, 6 and 10, and mean reciprocal    #
#                     rank.                                            #
########################################################################
"""The retrieval evaluation: does search find the evidence?

For each answerable case, search returns the top 10 passages; recall
at k is the share of evidence groups with a span in the top k, and the
reciprocal rank is 1 / the rank of the first passage holding evidence.
It needs no model, so it compares keyword, semantic and hybrid search
for free, overall and for paraphrased questions on their own.
"""

from __future__ import annotations

from collections.abc import Callable
from statistics import fmean
from typing import Any

from kds.evals import EvalCase
from kds.logs import get_logger

from grounded_qa.core.retrieve import Retriever
from grounded_qa.core.text import normalize
from grounded_qa.evals.score import ANSWERABLE, recall, reciprocal_rank

# Module constants
log = get_logger(__name__)
# log.debug("Lists the cut-offs recall is reported at")
CUTOFFS = (1, 3, 6, 10)
# log.debug("Names the score for mean reciprocal rank")
MRR = "mrr"
# log.debug("Names the tag of questions worded unlike the sources")
PARAPHRASED = "paraphrased"
# log.debug("Sets the decimal places scores are rounded to")
PLACES = 3
# log.debug("Names the count of cases in a summary")
CASES = "cases"
# log.debug("Names a row's tags")
TAGS = "tags"


# log.debug("Defines the retrieval scores of every answerable case")
def evaluate(cases: list[EvalCase], retriever: Retriever) -> list[dict[str, Any]]:
    """Return one row per answerable case: id, tags, recall@k, MRR."""
    # log.debug("Starts the rows")
    rows: list[dict[str, Any]] = []
    # log.debug("Walks the cases the sources answer")
    for case in (c for c in cases if c.expected[ANSWERABLE]):
        # log.debug("Searches once, deep enough for the largest cut-off")
        hits = retriever.search(case.input["question"], k=max(CUTOFFS))
        # log.debug("Puts the passages in plain form, in rank order")
        shown = [normalize(h.passage.text) for h in hits]
        # log.debug("Puts the evidence groups in plain form")
        groups = [[normalize(s["text"]) for s in group] for group in case.expected["evidence"]]
        # log.debug("Adds the case's recall at each cut-off and its MRR")
        rows.append(
            {
                "id": case.id,
                TAGS: case.tags,
                **{f"recall_at_{k}": recall(groups, shown[:k]) for k in CUTOFFS},
                MRR: reciprocal_rank(groups, shown),
            }
        )
    # log.debug("Returns the rows")
    return rows


# log.debug("Defines the averages over a set of rows")
def summarise(
    rows: list[dict[str, Any]], keep: Callable[[dict[str, Any]], bool]
) -> dict[str, Any]:
    """Return the mean of each score over the rows `keep` accepts."""
    # log.debug("Keeps the rows asked for")
    chosen = [row for row in rows if keep(row)]
    # log.debug("Lists the score names in report order")
    names = [*(f"recall_at_{k}" for k in CUTOFFS), MRR]
    # log.debug("Returns the case count and each mean")
    return {CASES: len(chosen)} | {
        name: round(fmean(row[name] for row in chosen), PLACES) if chosen else 0.0
        for name in names
    }


# log.debug("Defines the summary table for several modes")
def to_markdown(results: dict[str, list[dict[str, Any]]]) -> str:
    """Return a Markdown table: each mode, all cases and paraphrased."""
    # log.debug("Writes the table header")
    lines = [
        "| Mode | Questions | Recall@1 | Recall@3 | Recall@6 | Recall@10 | MRR |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    # log.debug("Writes a row for all questions and one for paraphrased")
    for mode, rows in results.items():
        # log.debug("Walks the two slices")
        for label, keep in (("all", _all), (PARAPHRASED, _paraphrased)):
            # log.debug("Averages the slice")
            s = summarise(rows, keep)
            # log.debug("Adds its row")
            lines.append(
                f"| {mode} | {label} ({s[CASES]}) | "
                + " | ".join(f"{s[name]:.3f}" for name in list(s)[1:])
                + " |"
            )
    # log.debug("Returns the table")
    return "\n".join(lines) + "\n"


# log.debug("Defines the filter that keeps every row")
def _all(row: dict[str, Any]) -> bool:
    """Return True for every row."""
    # log.debug("Keeps the row")
    return bool(row)


# log.debug("Defines the filter that keeps paraphrased questions")
def _paraphrased(row: dict[str, Any]) -> bool:
    """Return True for questions worded unlike the sources."""
    # log.debug("Keeps the row when it is tagged paraphrased")
    return PARAPHRASED in row[TAGS]
