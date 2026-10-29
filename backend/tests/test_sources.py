########################################################################
#                    backend/tests/test_sources.py                     #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

Tests reading sources: front matter, the hash check, safe ids and paths,
and the real corpus.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

from pathlib import Path

# Third-party
import pytest
from kds.logs import get_logger

# Local
from grounded_qa.core import sources
from grounded_qa.core.sources import SourceError
from support import REPO, make_source, write_source

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)


########################################################################
#                             Source tests                             #
########################################################################
# log.debug("Defines the test that a document survives render and parse")
def test_render_then_parse_round_trips() -> None:
    """A rendered source parses back to the same source."""
    # log.debug("Builds a source")
    original = make_source("round-trip", "Some text.\n")
    # log.debug("Renders and parses it")
    parsed = sources.parse("round-trip", sources.render(original))
    # log.debug("Checks nothing changed")
    assert parsed == original


# log.debug("Defines the test that an edited text is refused")
def test_edited_text_fails_its_hash() -> None:
    """Changing one character of the text breaks the SHA-256 check."""
    # log.debug("Renders a source, then edits its text")
    text = sources.render(make_source("edited", "Leave is 12 workweeks.\n"))
    # log.debug("Expects the hash error")
    with pytest.raises(SourceError, match="does not match its sha256"):
        # log.debug("Parses the edited document")
        sources.parse("edited", text.replace("12", "26"))


# log.debug("Defines the bad documents the parser must refuse")
@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("no front matter\n", "starts with front matter"),
        ("---\ntitle: x\n---\n\nbody\n", "front matter lacks"),
    ],
)
def test_malformed_documents_are_refused(text: str, message: str) -> None:
    """A document without complete front matter is refused.

    Args:
        text: A document with missing or incomplete front matter.
        message: What the error must say.
    """
    # log.debug("Expects the error")
    with pytest.raises(SourceError, match=message):
        # log.debug("Parses the bad document")
        sources.parse("bad", text)


# log.debug("Defines the test that a non-HTTPS source is refused")
def test_source_must_be_https() -> None:
    """The source address must be HTTPS."""
    # log.debug("Renders a source, then swaps its address to plain HTTP")
    text = sources.render(make_source("plain", "Text.\n")).replace("https://", "http://")
    # log.debug("Expects a source error naming the field problem")
    with pytest.raises(SourceError):
        # log.debug("Parses it")
        sources.parse("plain", text)


# log.debug("Defines the ids that must be refused")
@pytest.mark.parametrize("bad", ["../secrets", "UPPER", "-dash-first", "has space", "a" * 65, ""])
def test_unsafe_ids_are_refused(bad: str) -> None:
    """Only lowercase letters, digits and inner dashes are allowed.

    Args:
        bad: An id that breaks the id rule.
    """
    # log.debug("Expects the id error")
    with pytest.raises(SourceError):
        # log.debug("Checks the id")
        sources.check_id(bad)


# log.debug("Defines the test that a path stays in its folder")
def test_path_for_stays_inside_the_folder(tmp_path: Path) -> None:
    """A good id maps to a file directly inside the folder.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Builds the path")
    path = sources.path_for(tmp_path, "fact-sheet-1")
    # log.debug("Checks it is a direct child of the folder")
    assert path.parent == tmp_path.resolve() and path.name == "fact-sheet-1.md"


# log.debug("Defines the test that the folder README is not a source")
def test_load_dir_skips_readme(tmp_path: Path) -> None:
    """README.md describes the folder and is not loaded as a source.

    Args:
        tmp_path: A temporary folder pytest makes for this test.
    """
    # log.debug("Writes a source and a README")
    write_source(tmp_path, make_source("one", "Text.\n"))
    # log.debug("Writes the README")
    (tmp_path / "README.md").write_text("# Sources\n", encoding="utf-8")
    # log.debug("Checks only the source loads")
    assert [s.id for s in sources.load_dir(tmp_path)] == ["one"]


# log.debug("Defines the test that the real corpus is intact")
def test_every_approved_source_verifies() -> None:
    """All 22 fact sheets parse, match their hashes, are unflagged."""
    # log.debug("Loads the repository's approved sources")
    corpus = sources.load_dir(REPO / "data" / "sources")
    # log.debug("Checks the count")
    assert len(corpus) == 22
    # log.debug("Checks each is a DOL page over HTTPS with no flagged lines")
    assert all(s.source.startswith("https://www.dol.gov/") and not s.flagged for s in corpus)
