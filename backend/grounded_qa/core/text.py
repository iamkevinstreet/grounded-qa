########################################################################
#                   backend/grounded_qa/core/text.py                   #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Text helpers shared by search and checks: plain  #
#                     forms for comparing quotes, and search terms.    #
########################################################################
"""Text helpers: normalising for quote checks, terms for search."""

from __future__ import annotations

import re

from kds.logs import get_logger

# Module constants
log = get_logger(__name__)
# log.debug("Maps curly quotes, dashes and odd spaces to plain ones")
PLAIN = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
        "\u202f": " ",
    }
)
# log.debug("Matches Markdown list markers, heading marks and table bars")
MARKUP_RE = re.compile(r"(?m)^\s*(?:[-*]|#{1,6})\s+|\|")
# log.debug("Matches a possessive 's, which search ignores")
POSSESSIVE_RE = re.compile(r"'s\b")
# log.debug("Matches a thousands comma inside a number, as in 1,250")
THOUSANDS_RE = re.compile(r"(?<=\d),(?=\d{3})")
# log.debug("Matches one search term: letters and digits, and decimals")
TERM_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)*")
# log.debug("Lists common words that carry no meaning for search")
STOPWORDS = frozenset(
    "a about above after again against all am an and any are as at be because been before being"
    " below between both but by can could did do does doing down during each few for from"
    " further had has have having he her here hers herself him himself his how i if in into"
    " is it its itself just me more most my myself nor of off on once only or other our ours"
    " ourselves out over own same she should so some such than that the their theirs them"
    " themselves then there these they this those through to too under until up very was we"
    " were what when where which while who whom why will with would you your yours yourself"
    " yourselves".split()
)
# log.debug("Sets the shortest word the plural rules may change")
MIN_STEM = 4


# log.debug("Defines the plain form two texts are compared in")
def normalize(text: str) -> str:
    """Return text lowercased, with plain quotes and no Markdown marks.

    Two texts that say the same words in the same order normalise to
    the same string, however they were typed or formatted.
    """
    # log.debug("Returns the plain form without its position map")
    return plain_map(text)[0]


# log.debug("Defines the plain form with a map back to the original")
def plain_map(text: str) -> tuple[str, list[int]]:
    """Return the plain form, and each plain character's index in text.

    The map turns a match found in the plain form into a range of the
    original text, which is how a checked quote is highlighted.
    """
    # log.debug("Finds every character inside a Markdown mark")
    marks = {i for match in MARKUP_RE.finditer(text) for i in range(*match.span())}
    # log.debug("Starts the plain characters")
    chars: list[str] = []
    # log.debug("Starts their positions in the original text")
    positions: list[int] = []
    # log.debug("Walks the text with plain quotes and dashes, one for one")
    for index, char in enumerate(text.translate(PLAIN)):
        # log.debug("Reads marks and whitespace as one gap")
        if index in marks or char.isspace():
            # log.debug("Adds one space after a word, never two or a leading one")
            if chars and chars[-1] != " ":
                # log.debug("Adds the space")
                chars.append(" ")
                # log.debug("Maps it to where the gap starts")
                positions.append(index)
            # log.debug("Moves to the next character")
            continue
        # log.debug("Adds the character lowercased, mapped to its position")
        for lower in char.lower():
            # log.debug("Adds the lowercase character")
            chars.append(lower)
            # log.debug("Maps it")
            positions.append(index)
    # log.debug("Drops a trailing space")
    if chars and chars[-1] == " ":
        # log.debug("Drops the space")
        chars.pop()
        # log.debug("Drops its position")
        positions.pop()
    # log.debug("Returns the plain form and the map")
    return "".join(chars), positions


# log.debug("Defines how many words a text has")
def word_count(text: str) -> int:
    """Return the number of whitespace-separated words."""
    # log.debug("Returns the count of words")
    return len(text.split())


# log.debug("Defines the plural rules of Harman's S-stemmer")
def stem(word: str) -> str:
    """Return the singular of a plural English word, conservatively.

    Harman's S-stemmer (1991): "policies" -> "policy", "leaves" ->
    "leave", "hours" -> "hour"; "business" and "status" stay.
    """
    # log.debug("Leaves short words alone")
    if len(word) < MIN_STEM:
        # log.debug("Returns the word unchanged")
        return word
    # log.debug("Turns -ies into -y, as in policies")
    if word.endswith("ies") and not word.endswith(("eies", "aies")):
        # log.debug("Returns the -y form")
        return word[:-3] + "y"
    # log.debug("Turns -es into -e, as in leaves")
    if word.endswith("es") and not word.endswith(("aes", "ees", "oes")):
        # log.debug("Returns the -e form")
        return word[:-1]
    # log.debug("Drops a final -s, except in -us and -ss")
    if word.endswith("s") and not word.endswith(("us", "ss")):
        # log.debug("Returns the word without its -s")
        return word[:-1]
    # log.debug("Returns the word unchanged")
    return word


# log.debug("Defines the search terms of a text")
def terms(text: str) -> list[str]:
    """Return the text's search terms: stemmed, without stopwords."""
    # log.debug("Puts the text in plain lowercase form")
    plain = normalize(text)
    # log.debug("Removes possessives and thousands commas")
    plain = THOUSANDS_RE.sub("", POSSESSIVE_RE.sub("", plain)).replace("'", "")
    # log.debug("Returns each meaningful term, stemmed")
    return [
        stem(term)
        for term in TERM_RE.findall(plain)
        if term not in STOPWORDS and (len(term) > 1 or term.isdigit())
    ]
