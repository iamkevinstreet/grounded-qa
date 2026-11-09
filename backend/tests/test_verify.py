########################################################################
#                                                                      #
#                     backend/tests/test_verify.py                     #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-11-09

Tests the quote check, the removal of claims whose citations all
failed, and markers that number passages read as the citations they
mean.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

# Third-party
import pytest
from kds.logs import get_logger

# Local
from grounded_qa.core.verify import align, find_quote, marker_numbers, prune

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
# log.debug("Sets a passage written as a Markdown list with curly quotes")
PASSAGE = (
    "Eligible employees may take:\n\n"
    "- Up to 12 workweeks of leave in a 12-month period, and\n"
    "- Up to 26 workweeks of military caregiver leave.\n\n"
    "This term does not include parents \u201cin law.\u201d"
)
# log.debug("Sets the Nov 9 flight crew draft's citations: two from one passage, then another")
FLIGHT_CREW = [
    ("fs28i#14", "up to 72 days of FMLA leave in a 12-month period"),
    ("fs28i#14", "up to 156 days of military caregiver leave during a single 12-month period"),
    ("fs28#13", "Airline flight crew employees have special hours of service eligibility"),
]


########################################################################
#                                                                      #
#                          Quote check tests                           #
#                                                                      #
########################################################################
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
    """Case, quote marks, list marks and an ellipsis do not matter.

    Args:
        quote: A quote that is in PASSAGE.
    """
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
    """Changed words, short quotes and out-of-order parts fail.

    Args:
        quote: A quote that is not in PASSAGE, or too short.
        problem: What the check must report.
    """
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


# log.debug("Defines the test that markers numbering passages come to name citations")
def test_markers_that_number_passages_are_read_as_their_citations() -> None:
    """The Nov 9 draft: [2] meant the second passage, not quote 2."""
    # log.debug("Aligns the draft as the model wrote it")
    text, realigned = align(
        "Crews get up to 72 days in a 12-month period [1]. Military caregiver leave is up to "
        "156 days in a single 12-month period [1]. Flight crew employees have special hours "
        "of service eligibility requirements [2].",
        FLIGHT_CREW,
    )
    # log.debug("Checks each claim now names its own passage's citations")
    assert (realigned, text.count("[1, 2]"), text.endswith("requirements [3].")) == (True, 2, True)


# log.debug("Defines the test that markers numbering citations stay as they are")
def test_markers_that_number_citations_are_left_alone() -> None:
    """One number per quote, as the rules ask: nothing to rewrite."""
    # log.debug("Writes a draft that numbers each quote")
    draft = "Crews get 72 days [1]. Caregiver leave is 156 days [2]. Hours rules differ [3]."
    # log.debug("Checks it comes back unchanged")
    assert align(draft, FLIGHT_CREW) == (draft, False)


# log.debug("Defines the test that a rewrite never moves a claim to a worse-fitting quote")
def test_markers_stay_when_the_numbered_citations_fit_the_claims_better() -> None:
    """[1] and [2] could be passages; the claims say quotes 1 and 2."""
    # log.debug("Writes a draft whose second claim is quote 2's, with quote 3 left unused")
    draft = (
        "Crews get up to 72 days of FMLA leave in a 12-month period [1]. Military caregiver "
        "leave is up to 156 days during a single 12-month period [2]."
    )
    # log.debug("Checks it comes back unchanged, the second claim still on quote 2")
    assert align(draft, FLIGHT_CREW) == (draft, False)


# log.debug("Defines the test that the numbers a marker names are read")
def test_marker_numbers_reads_every_marker() -> None:
    """Single and joined markers both count, each number once."""
    # log.debug("Checks the numbers")
    assert marker_numbers("A [1]. B [1, 3]. C.") == {1, 3}
