########################################################################
#                      backend/tests/test_text.py                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

Tests normalising for quote checks, the plural stemmer, and search
terms.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

# Third-party
import pytest
from kds.logs import get_logger

# Local
from grounded_qa.core.text import normalize, plain_map, stem, terms, word_count

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)


########################################################################
#                          Text helper tests                           #
########################################################################
# log.debug("Defines the test that formatting does not change the plain form")
def test_normalize_ignores_case_quotes_dashes_and_markup() -> None:
    """Curly quotes, dashes, list marks and spacing normalise away."""
    # log.debug("Normalises a curly, marked-up line")
    plain = normalize("- The employee\u2019s \u201cright\u201d \u2014 and  more |")
    # log.debug("Checks the plain form")
    assert plain == 'the employee\'s "right" - and more'


# log.debug("Defines the plural cases the stemmer must handle")
@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("policies", "policy"),
        ("leaves", "leave"),
        ("employees", "employee"),
        ("hours", "hour"),
        ("business", "business"),
        ("status", "status"),
        ("was", "was"),
    ],
)
def test_stem(word: str, expected: str) -> None:
    """Plurals become singular; -ss, -us and short words stay.

    Args:
        word: The word to stem.
        expected: Its stem.
    """
    # log.debug("Checks the stem")
    assert stem(word) == expected


# log.debug("Defines the test for search terms")
def test_terms_drop_stopwords_possessives_and_commas() -> None:
    """Terms are stemmed content words; numbers keep their digits."""
    # log.debug("Takes the terms of a sentence with each case in it")
    found = terms("The employee's 1,250 hours under 29 CFR 825.110 are counted")
    # log.debug("Checks the terms")
    assert found == ["employee", "1250", "hour", "29", "cfr", "825.110", "counted"]


# log.debug("Defines the test for word counts")
def test_word_count() -> None:
    """Words are counted by whitespace."""
    # log.debug("Checks a count")
    assert word_count("one two\nthree  four") == 4


# log.debug("Defines the test that the plain form maps back to the text")
def test_plain_map_points_each_character_at_its_source() -> None:
    """Every plain character comes from the original position given."""
    # log.debug("Maps a marked-up line")
    text = "- Up  To \u201c12\u201d"
    # log.debug("Builds the plain form and its map")
    plain, positions = plain_map(text)
    # log.debug("Checks the plain form")
    assert plain == 'up to "12"'
    # log.debug("Checks each letter maps back to the same letter")
    assert all(text[p].lower() == c for c, p in zip(plain, positions, strict=True) if c.isalnum())
