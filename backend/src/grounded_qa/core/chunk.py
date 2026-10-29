########################################################################
#                backend/src/grounded_qa/core/chunk.py                 #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

Splits each source into passages, the units retrieval finds and
answers cite. A passage is a run of whole paragraphs, lists and tables
under one heading, up to a word limit, so a quote never spans two
sections and a citation can name the section it came from. A block too
long for one passage is split between list items, then between
sentences.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Final

# Third-party
from kds.args import required
from kds.logs import get_logger
from pydantic import BaseModel

# Local
from grounded_qa.config import SETTINGS
from grounded_qa.core.sources import Source
from grounded_qa.core.text import word_count

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the text between the parts of a heading path, from the config")
PATH_SEP: Final = SETTINGS.retrieval_section_separator

########################################################################
#                           Local constants                            #
########################################################################
# log.debug("Matches a Markdown heading; captures its marks and text")
HEADING_RE = re.compile(r"^(?P<marks>#{1,6})\s+(?P<name>.+)$")
# log.debug("Matches the space between two sentences")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"(])")
# log.debug("Sets the text between blocks of a document")
BLOCK_SEP = "\n\n"
# log.debug("Sets the marker between a source id and a passage number")
ID_SEP = "#"


########################################################################
#                               Passages                               #
########################################################################
# log.debug("Defines one passage of a source")
class Passage(BaseModel, frozen=True):
    """A passage and where it came from."""

    # log.debug("Holds the passage id: source id, #, number from 1")
    id: str
    # log.debug("Holds the id of the source it came from")
    doc_id: str
    # log.debug("Holds the source's title")
    title: str
    # log.debug("Holds the heading path above it; empty for the opening")
    section: str
    # log.debug("Holds the passage's text, exactly as in the source")
    text: str
    # log.debug("Holds the source's URL")
    url: str
    # log.debug("Holds the source's revision date")
    revised: str

    # log.debug("Defines the text search reads: title, section, passage")
    @property
    def search_text(self) -> str:
        """Returns title, heading path and text, so headings count.

        Returns:
            The title, the heading path and the text, one per line.
        """
        # log.debug("Returns the three joined by newlines")
        return f"{self.title}\n{self.section}\n{self.text}"


# log.debug("Defines how a source becomes passages")
def split(source: Source | None = None, max_words: int | None = None) -> list[Passage]:
    """Splits a source into passages of at most `max_words` words.

    A single sentence longer than the limit stays whole, because a
    passage must hold text exactly as the source wrote it.

    Args:
        source: The source to split. Required.
        max_words: The most words in one passage. Required.

    Returns:
        The passages in reading order, numbered from 1.
    """
    # log.debug("Takes the source, which the caller must give")
    source = required(source=source)
    # log.debug("Takes the word limit, which the caller must give")
    max_words = required(max_words=max_words)
    # log.debug("Starts the list of passages")
    passages: list[Passage] = []
    # log.debug("Groups the source's blocks under their headings")
    for section, pieces in _sections(source.body, max_words):
        # log.debug("Packs each section's pieces into passages")
        for text in _pack(pieces, max_words):
            # log.debug("Adds the passage, numbered in reading order")
            passages.append(
                Passage(
                    id=f"{source.id}{ID_SEP}{len(passages) + 1}",
                    doc_id=source.id,
                    title=source.title,
                    section=section,
                    text=text,
                    url=source.source,
                    revised=source.revised,
                )
            )
    # log.debug("Returns every passage")
    return passages


# log.debug("Defines the passages of every source the guard passed")
def split_all(sources: list[Source] | None = None, max_words: int | None = None) -> list[Passage]:
    """Splits each source; holds back any the guard flagged.

    A flagged source stays listed, with its flagged lines, so an
    approver can see it, but none of its text reaches the model.

    Args:
        sources: The sources to split. Required.
        max_words: The most words in one passage. Required.

    Returns:
        The passages of every source the guard passed, in order.
    """
    # log.debug("Takes the sources, which the caller must give")
    sources = required(sources=sources)
    # log.debug("Takes the word limit, which the caller must give")
    max_words = required(max_words=max_words)
    # log.debug("Logs each held-back source by id")
    for source in (s for s in sources if s.flagged):
        # log.debug("Logs the source and how many lines were flagged")
        log.warning("held back %s: %d instruction-like lines", source.id, len(source.flagged))
    # log.debug("Returns the passages of every unflagged source")
    return [p for s in sources if not s.flagged for p in split(s, max_words)]


# log.debug("Defines how a text is grouped under its headings")
def _sections(
    body: str | None = None, max_words: int | None = None
) -> Iterator[tuple[str, list[str]]]:
    """Yields (heading path, pieces) for each run of text.

    Args:
        body: The source's text, as Markdown. Required.
        max_words: The most words in one passage, for cutting long
            blocks. Required.

    Yields:
        Each section's joined heading path, with its pieces.
    """
    # log.debug("Takes the body, which the caller must give")
    body = required(body=body)
    # log.debug("Takes the word limit, which the caller must give")
    max_words = required(max_words=max_words)
    # log.debug("Starts with no headings above the text")
    path: list[tuple[int, str]] = []
    # log.debug("Starts the current section's pieces")
    pieces: list[str] = []
    # log.debug("Walks the text's blocks in order")
    for block in (b.strip() for b in body.split(BLOCK_SEP) if b.strip()):
        # log.debug("Checks whether the block is a heading")
        heading = HEADING_RE.match(block)
        # log.debug("Adds a plain block's pieces to the current section")
        if heading is None:
            # log.debug("Adds the block, split if it is too long")
            pieces += _fit(block, max_words)
            # log.debug("Moves to the next block")
            continue
        # log.debug("Ends the current section before a heading")
        if pieces:
            # log.debug("Yields the section with its heading path")
            yield PATH_SEP.join(name for _, name in path), pieces
        # log.debug("Starts the next section empty")
        pieces = []
        # log.debug("Reads the heading's level from its marks")
        level = len(heading["marks"])
        # log.debug("Keeps the headings above this one, then adds it")
        path = [*[(lvl, name) for lvl, name in path if lvl < level], (level, heading["name"])]
    # log.debug("Yields the last section when it has text")
    if pieces:
        # log.debug("Yields it")
        yield PATH_SEP.join(name for _, name in path), pieces


# log.debug("Defines how a block is cut to fit a passage")
def _fit(block: str | None = None, max_words: int | None = None) -> list[str]:
    """Returns the block whole, or cut between lines, then sentences.

    Args:
        block: One block of the text: a paragraph, list or table.
            Required.
        max_words: The most words in one piece. Required.

    Returns:
        The block's pieces, each within the limit unless a single
        sentence is longer.
    """
    # log.debug("Takes the block, which the caller must give")
    block = required(block=block)
    # log.debug("Takes the word limit, which the caller must give")
    max_words = required(max_words=max_words)
    # log.debug("Keeps a block that fits")
    if word_count(block) <= max_words:
        # log.debug("Returns it whole")
        return [block]
    # log.debug("Cuts between list items or table rows first")
    lines = block.splitlines()
    # log.debug("Cuts a single long paragraph between sentences instead")
    if len(lines) == 1:
        # log.debug("Packs the sentences into pieces that fit")
        return list(_pack(SENTENCE_RE.split(block), max_words, sep=" "))
    # log.debug("Packs the lines, each cut further if needed")
    return list(_pack([p for line in lines for p in _fit(line, max_words)], max_words, sep="\n"))


# log.debug("Defines how pieces are packed into passages")
def _pack(
    pieces: list[str] | None = None, max_words: int | None = None, sep: str = BLOCK_SEP
) -> Iterator[str]:
    """Yields runs of pieces joined by `sep`, each within the limit.

    Args:
        pieces: The pieces to join, in order. Required.
        max_words: The most words in one run. Required.
        sep: The text that joins two pieces.

    Yields:
        Each run of pieces, joined.
    """
    # log.debug("Takes the pieces, which the caller must give")
    pieces = required(pieces=pieces)
    # log.debug("Takes the word limit, which the caller must give")
    max_words = required(max_words=max_words)
    # log.debug("Starts the current run")
    run: list[str] = []
    # log.debug("Walks the pieces in order")
    for piece in pieces:
        # log.debug("Ends the run when this piece would overflow it")
        if run and word_count(sep.join([*run, piece])) > max_words:
            # log.debug("Yields the full run")
            yield sep.join(run)
            # log.debug("Starts a new run")
            run = []
        # log.debug("Adds the piece to the run")
        run.append(piece)
    # log.debug("Yields the last run when it has pieces")
    if run:
        # log.debug("Yields it")
        yield sep.join(run)
