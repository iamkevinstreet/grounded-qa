########################################################################
#                  backend/grounded_qa/core/verify.py                  #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Checks each quote is in the passage it cites,    #
#                     and removes claims whose citations all failed.   #
########################################################################
"""The quote check: the model must show its evidence, word for word.

A citation passes when its passage was shown to the model and its
quote appears in that passage, in order, after both are normalised
(case, quote marks, dashes, spacing and Markdown marks do not count).
An ellipsis may join parts of a quote; each part must be found, in
order. A claim in the answer whose citations all fail is removed.
"""

from __future__ import annotations

import re

from kds.logs import get_logger

from grounded_qa.core.text import normalize, plain_map, word_count

# Module constants
log = get_logger(__name__)
# log.debug("Describes a range of a passage: start and end characters")
Span = tuple[int, int]
# log.debug("Matches an ellipsis that joins parts of a quote")
ELLIPSIS_RE = re.compile(r"\.\.\.|\u2026")
# log.debug("Sets the characters trimmed from the ends of a quote part")
TRIM = " .,;:\"'"
# log.debug("Sets the fewest words in each part of a joined quote")
MIN_PART_WORDS = 3
# log.debug("Matches a citation marker such as [1] or [1, 2]")
MARKER_RE = re.compile(r"\s*\[(\d+(?:\s*,\s*\d+)*)\]")
# log.debug("Matches one claim: text up to its markers and punctuation")
CLAIM_RE = re.compile(r".*?\[\d+(?:\s*,\s*\d+)*\][.!?,;:]?", re.DOTALL)


# log.debug("Defines the check of one quote against one passage")
def find_quote(quote: str, passage: str, min_words: int) -> tuple[tuple[Span, ...], str | None]:
    """Return where the quote is in the passage, or the problem.

    Returns:
        The quote's ranges in the passage (one per part of a joined
        quote) and None; or no ranges and what was wrong.
    """
    # log.debug("Splits the quote at any ellipsis and normalises each part")
    parts = [p for p in (normalize(part).strip(TRIM) for part in ELLIPSIS_RE.split(quote)) if p]
    # log.debug("Refuses a quote too short to show anything")
    if sum(word_count(p) for p in parts) < min_words:
        # log.debug("Returns the length problem")
        return (), f"quote is shorter than {min_words} words"
    # log.debug("Refuses a joined quote with a part too short to place")
    if len(parts) > 1 and min(word_count(p) for p in parts) < MIN_PART_WORDS:
        # log.debug("Returns the part-length problem")
        return (), f"each part of a joined quote needs {MIN_PART_WORDS} words"
    # log.debug("Puts the passage in the same plain form, with its map")
    text, positions = plain_map(passage)
    # log.debug("Starts the found ranges")
    spans: list[Span] = []
    # log.debug("Starts the search at the passage's beginning")
    start = 0
    # log.debug("Finds each part after the one before it")
    for part in parts:
        # log.debug("Looks for the part from where the last one ended")
        found = text.find(part, start)
        # log.debug("Refuses a part that is not there")
        if found < 0:
            # log.debug("Returns the not-found problem")
            return (), "quote is not in the passage"
        # log.debug("Maps the part back to a range of the original passage")
        spans.append((positions[found], positions[found + len(part) - 1] + 1))
        # log.debug("Moves past the part just found")
        start = found + len(part)
    # log.debug("Returns the ranges and no problem")
    return tuple(spans), None


# log.debug("Defines how an answer keeps only checked claims")
def prune(answer: str, renumber: dict[int, int]) -> str:
    """Renumber markers of kept citations; remove claims with none.

    Args:
        answer: The draft answer, with [n] markers.
        renumber: Each kept citation's draft number and new number.

    Returns:
        The answer without the claims whose citations all failed.
    """
    # log.debug("Starts the kept text")
    kept: list[str] = []
    # log.debug("Remembers where the last claim ended")
    end = 0
    # log.debug("Walks each claim, a span ending in markers")
    for claim in CLAIM_RE.finditer(answer):
        # log.debug("Reads the claim's draft citation numbers")
        numbers = [int(n) for m in MARKER_RE.finditer(claim[0]) for n in m[1].split(",")]
        # log.debug("Keeps the claim when any of its citations passed")
        if any(n in renumber for n in numbers):
            # log.debug("Adds the claim with its markers renumbered")
            kept.append(MARKER_RE.sub(lambda m: _marker(m, renumber), claim[0]))
        # log.debug("Notes where this claim ended")
        end = claim.end()
    # log.debug("Returns the kept claims and any unmarked closing text")
    return " ".join(" ".join(kept).split()) + _tail(answer[end:], kept)


# log.debug("Defines the new form of one marker")
def _marker(match: re.Match[str], renumber: dict[int, int]) -> str:
    """Return the marker with kept numbers renumbered, or nothing."""
    # log.debug("Maps each number that was kept")
    numbers = [renumber[int(n)] for n in match[1].split(",") if int(n) in renumber]
    # log.debug("Returns the new marker, or nothing when none were kept")
    return f" [{', '.join(str(n) for n in numbers)}]" if numbers else ""


# log.debug("Defines the closing text after the last marker")
def _tail(rest: str, kept: list[str]) -> str:
    """Return closing text with no marker, joined with one space."""
    # log.debug("Returns nothing when there is no closing text")
    if not rest.strip():
        # log.debug("Returns an empty string")
        return ""
    # log.debug("Returns the text, spaced from the claims before it")
    return (" " if kept else "") + " ".join(rest.split())
