########################################################################
#                                                                      #
#                backend/src/grounded_qa/core/verify.py                #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-11-09

Checks each quote is in the passage it cites, and removes the claims
whose citations all failed: the model must show its evidence, word for
word. A citation passes when its passage was shown to the model and
its quote appears in that passage, in order, after both are normalised
(case, quote marks, dashes, spacing and Markdown marks do not count).
An ellipsis may join parts of a quote; each part must be found, in
order.

Markers that number passages instead of citations are read as what
they mean before the check (see align): on Nov 9, 5 of 80 live answers
numbered them that way, and the judge marked 2 of them down for a claim
that pointed at the wrong source.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

import re

# Third-party
from kds.args import required
from kds.logs import get_logger

# Local
from grounded_qa.core.text import normalize, plain_map, terms, word_count

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
# log.debug("Describes a range of a passage: start and end characters")
Span = tuple[int, int]
# log.debug("Matches an ellipsis that joins parts of a quote")
ELLIPSIS_RE = re.compile(r"\.\.\.|\u2026")
# log.debug("Sets the characters trimmed from the ends of a quote part")
TRIM = " .,;:\"'"
# log.debug("Sets the fewest words in each part of a joined quote")
MIN_PART_WORDS = 3
# log.debug("Sets how a marker joins the numbers it names")
NUMBER_JOIN = ", "
# log.debug("Matches a citation marker such as [1] or [1, 2]")
MARKER_RE = re.compile(r"\s*\[(\d+(?:\s*,\s*\d+)*)\]")
# log.debug("Matches one claim: text up to its markers and punctuation")
CLAIM_RE = re.compile(r".*?\[\d+(?:\s*,\s*\d+)*\][.!?,;:]?", re.DOTALL)


########################################################################
#                                                                      #
#                             Quote check                              #
#                                                                      #
########################################################################
# log.debug("Defines the check of one quote against one passage")
def find_quote(
    quote: str | None = None, passage: str | None = None, min_words: int | None = None
) -> tuple[tuple[Span, ...], str | None]:
    """Returns where the quote is in the passage, or the problem.

    Args:
        quote: The quote the model gave. Required.
        passage: The text of the passage it cites. Required.
        min_words: The fewest words the whole quote may have.
            Required.

    Returns:
        The quote's ranges in the passage (one per part of a joined
        quote) and None; or no ranges and what was wrong.
    """
    # log.debug("Takes the quote, which the caller must give")
    quote = required(quote=quote)
    # log.debug("Takes the passage, which the caller must give")
    passage = required(passage=passage)
    # log.debug("Takes the shortest quote allowed, which the caller must give")
    min_words = required(min_words=min_words)
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
def prune(answer: str | None = None, renumber: dict[int, int] | None = None) -> str:
    """Renumbers the markers of kept citations; drops claims with none.

    Args:
        answer: The draft answer, with [n] markers. Required.
        renumber: Each kept citation's draft number and new number.
            Required.

    Returns:
        The answer without the claims whose citations all failed.
    """
    # log.debug("Takes the answer, which the caller must give")
    answer = required(answer=answer)
    # log.debug("Takes the number map, which the caller must give")
    renumber = required(renumber=renumber)
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
def _marker(match: re.Match[str] | None = None, renumber: dict[int, int] | None = None) -> str:
    """Returns the marker with kept numbers renumbered, or nothing.

    Args:
        match: A citation marker found in a claim. Required.
        renumber: Each kept citation's draft number and new number.
            Required.

    Returns:
        The marker with its kept numbers, or an empty string.
    """
    # log.debug("Takes the marker found, which the caller must give")
    match = required(match=match)
    # log.debug("Takes the number map, which the caller must give")
    renumber = required(renumber=renumber)
    # log.debug("Maps each number that was kept")
    numbers = [renumber[int(n)] for n in match[1].split(",") if int(n) in renumber]
    # log.debug("Returns the new marker, or nothing when none were kept")
    return f" [{NUMBER_JOIN.join(str(n) for n in numbers)}]" if numbers else ""


# log.debug("Defines the closing text after the last marker")
def _tail(rest: str | None = None, kept: list[str] | None = None) -> str:
    """Returns closing text with no marker, joined with one space.

    Args:
        rest: The answer's text after its last claim. Required.
        kept: The claims kept so far. Required.

    Returns:
        The closing text, after a space when claims were kept; empty
        when there is none.
    """
    # log.debug("Takes the closing text, which the caller must give")
    rest = required(rest=rest)
    # log.debug("Takes the claims kept, which the caller must give")
    kept = required(kept=kept)
    # log.debug("Returns nothing when there is no closing text")
    if not rest.strip():
        # log.debug("Returns an empty string")
        return ""
    # log.debug("Returns the text, spaced from the claims before it")
    return (" " if kept else "") + " ".join(rest.split())


# log.debug("Defines the citation numbers an answer's markers use")
def marker_numbers(answer: str | None = None) -> set[int]:
    """Returns every number the answer's [n] markers name.

    Args:
        answer: An answer with [n] markers. Required.

    Returns:
        The numbers, each once.
    """
    # log.debug("Takes the answer, which the caller must give")
    answer = required(answer=answer)
    # log.debug("Returns each number in each marker")
    return {int(n) for m in MARKER_RE.finditer(answer) for n in m[1].split(",")}


# log.debug("Defines how markers that number passages come to name citations")
def align(
    answer: str | None = None, cited: list[tuple[str, str]] | None = None
) -> tuple[str, bool]:
    """Returns the answer with markers that name its citations.

    The model is told to number its citations in the order it lists
    them, one number each. Sometimes it numbers passages instead: two
    quotes from one passage are both [1] and a quote from the next
    passage is [2], which as a citation number names the second quote.
    When the markers use exactly one number for each passage, in the
    order the passages are first cited, and the claims share at least
    as many terms with those passages' quotes as with the citations the
    numbers name, each marker is rewritten to name every citation of
    its passage: [1] becomes [1, 2], and [2] becomes [3].

    Args:
        answer: The draft answer, with [n] markers. Required.
        cited: Each draft citation's passage id and quote, in order.
            Required.

    Returns:
        The answer, and whether its markers were rewritten.
    """
    # log.debug("Takes the answer, which the caller must give")
    answer = required(answer=answer)
    # log.debug("Takes the citations, which the caller must give")
    cited = required(cited=cited)
    # log.debug("Reads the numbers the markers use")
    used = marker_numbers(answer)
    # log.debug("Numbers the passages in the order first cited, each with its citations")
    by_passage = {
        number: [i for i, (pid, _) in enumerate(cited, start=1) if pid == passage]
        for number, passage in enumerate(dict.fromkeys(pid for pid, _ in cited), start=1)
    }
    # log.debug("Leaves markers that number citations, or fit no other reading, as they are")
    if used == set(range(1, len(cited) + 1)) or used != set(by_passage):
        # log.debug("Returns the answer as it was")
        return answer, False
    # log.debug("Leaves them too when the claims fit the numbered citations better")
    if _fit(answer, cited, by_passage) < _fit(answer, cited, {n: [n] for n in used}):
        # log.debug("Returns the answer as it was")
        return answer, False
    # log.debug("Returns each marker naming every citation of its passage")
    return MARKER_RE.sub(lambda m: _named(m, by_passage), answer), True


# log.debug("Defines how well one reading of the markers fits the claims")
def _fit(
    answer: str | None = None,
    cited: list[tuple[str, str]] | None = None,
    reading: dict[int, list[int]] | None = None,
) -> int:
    """Returns how many terms the claims share with the quotes named.

    Args:
        answer: The draft answer, with [n] markers. Required.
        cited: Each draft citation's passage id and quote, in order.
            Required.
        reading: The citations, by place in the list, each marker
            number names. Required.

    Returns:
        For each number of each claim's markers, the most terms the
        claim shares with one quote the number names, summed.
    """
    # log.debug("Takes the answer, which the caller must give")
    answer = required(answer=answer)
    # log.debug("Takes the citations, which the caller must give")
    cited = required(cited=cited)
    # log.debug("Takes the reading, which the caller must give")
    reading = required(reading=reading)
    # log.debug("Reads each quote's terms once")
    quotes = [set(terms(quote)) for _, quote in cited]
    # log.debug("Starts the count")
    total = 0
    # log.debug("Walks each claim, a span ending in markers")
    for claim in CLAIM_RE.finditer(answer):
        # log.debug("Reads the claim's terms, without its markers")
        words = set(terms(MARKER_RE.sub("", claim[0])))
        # log.debug("Adds, for each number, the best overlap with a quote it names")
        total += sum(
            max((len(words & quotes[i - 1]) for i in reading.get(n, [])), default=0)
            for n in marker_numbers(claim[0])
        )
    # log.debug("Returns the count")
    return total


# log.debug("Defines one marker rewritten to name its passage's citations")
def _named(
    match: re.Match[str] | None = None, by_passage: dict[int, list[int]] | None = None
) -> str:
    """Returns the marker naming every citation of its passages.

    Args:
        match: A marker that numbers passages. Required.
        by_passage: Each passage number's citations. Required.

    Returns:
        The marker, naming citations instead of passages.
    """
    # log.debug("Takes the marker found, which the caller must give")
    match = required(match=match)
    # log.debug("Takes the passages' citations, which the caller must give")
    by_passage = required(by_passage=by_passage)
    # log.debug("Lists each citation once, in order")
    numbers = dict.fromkeys(i for n in match[1].split(",") for i in by_passage[int(n)])
    # log.debug("Returns the new marker")
    return f" [{NUMBER_JOIN.join(str(i) for i in numbers)}]"
