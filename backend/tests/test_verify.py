########################################################################
#                     backend/tests/test_verify.py                     #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Tests the quote check and the removal of claims  #
#                     whose citations all failed.                      #
########################################################################
"""Tests for grounded_qa.core.verify."""

from __future__ import annotations

import pytest
from kds.logs import get_logger

from grounded_qa.core.verify import find_quote, prune

# Module constants
log = get_logger(__name__)
# log.debug("Sets a passage written as a Markdown list with curly quotes")
PASSAGE = (
    "Eligible employees may take:\n\n"
    "- Up to 12 workweeks of leave in a 12-month period, and\n"
    "- Up to 26 workweeks of military caregiver leave.\n\n"
    "This term does not include parents \u201cin law.\u201d"
)


# log.debug("Defines quotes that must pass")
@pytest.mark.parametrize(
    "quote",
    [
        "Up to 12 workweeks of leave in a 12-month period",
        "up to 12 WORKWEEKS of leave in a 12-month period.",
        'This term does not include parents "in law."',
        "of leave in a 12-month period, and Up to 26 workweeks",
        "Eligible employees may take ... Up to 26 workweeks of military caregiver leave",
    ],
)
def test_quotes_found_in_the_passage_pass(quote: str) -> None:
    """Case, quote marks, list marks and an ellipsis do not matter."""
    # log.debug("Checks the quote passes")
    assert find_quote(quote, PASSAGE, min_words=4)[1] is None


# log.debug("Defines quotes that must fail, with their problem")
@pytest.mark.parametrize(
    ("quote", "problem"),
    [
        ("Up to 16 workweeks of leave in a 12-month period", "not in the passage"),
        ("12 workweeks", "shorter than 4 words"),
        ("Up to 26 workweeks ... Eligible employees may take", "not in the passage"),
        ("Eligible employees may ... leave", "each part of a joined quote"),
    ],
)
def test_quotes_not_in_the_passage_fail(quote: str, problem: str) -> None:
    """Changed words, short quotes and out-of-order parts fail."""
    # log.debug("Checks the quote fails with the expected problem")
    assert problem in (find_quote(quote, PASSAGE, min_words=4)[1] or "")


# log.debug("Defines the test that ranges point at the original text")
def test_spans_cover_the_quote_in_the_original_passage() -> None:
    """Each range covers the quoted words as the passage writes them."""
    # log.debug("Finds a quote with straight quotes in a curly passage")
    spans, _ = find_quote('does not include parents "in law."', PASSAGE, min_words=4)
    # log.debug("Checks the range covers the curly original, edge marks trimmed")
    assert [PASSAGE[a:b] for a, b in spans] == ["does not include parents \u201cin law"]


# log.debug("Defines the test that a joined quote gets one range per part")
def test_joined_quote_has_a_range_per_part() -> None:
    """An ellipsis quote is shown as two highlighted parts, in order."""
    # log.debug("Finds a quote joined across the list")
    spans, _ = find_quote("Eligible employees may take ... 26 workweeks of military", PASSAGE, 4)
    # log.debug("Checks both parts, the list mark left out")
    assert [PASSAGE[a:b] for a, b in spans] == [
        "Eligible employees may take",
        "26 workweeks of military",
    ]


# log.debug("Defines the test that kept markers are renumbered")
def test_prune_renumbers_kept_and_removes_failed_claims() -> None:
    """A claim whose one citation failed goes; others renumber."""
    # log.debug("Prunes an answer where citation 1 failed and 2 passed")
    text = prune("Leave is 16 weeks [1]. Leave is unpaid [2]. Ask HR.", {2: 1})
    # log.debug("Checks the failed claim is gone and the marker renumbered")
    assert text == "Leave is unpaid [1]. Ask HR."


# log.debug("Defines the test that a claim with one good citation stays")
def test_prune_keeps_a_claim_with_any_passing_citation() -> None:
    """A claim citing [1, 2] stays when either citation passed."""
    # log.debug("Prunes an answer citing two passages at once")
    text = prune("Leave is unpaid [1, 2].", {2: 1})
    # log.debug("Checks only the kept number remains")
    assert text == "Leave is unpaid [1]."


# log.debug("Defines the test that an abstention's text survives")
def test_prune_keeps_text_without_markers() -> None:
    """Text with no markers at all, such as an abstention, is kept."""
    # log.debug("Checks the text comes back unchanged")
    assert prune("The passages do not cover this.", {}) == "The passages do not cover this."
