########################################################################
#                                                                      #
#             backend/src/grounded_qa/mcp_server/models.py             #
#                                                                      #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-11-07
Last modified on:  2026-11-07

What the MCP server's tools return: passages and source listings, and a
source as one Markdown page. A held-back source is listed by how many
of its lines the guard flagged, never by the lines themselves, since
they read like orders to a model.
"""

########################################################################
#                                                                      #
#                               Imports                                #
#                                                                      #
########################################################################
# Standard library
from __future__ import annotations

# Third-party
from kds.args import required
from kds.logs import get_logger
from pydantic import BaseModel

# Local
from grounded_qa.core.chunk import Passage
from grounded_qa.core.sources import Source

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
# log.debug("Sets what a held-back source's page says instead of its text")
HELD_BACK = (
    "Held back: the guard flagged {count} of its lines as reading like orders to an AI model, "
    "so its text is not shown and no answer draws on it."
)


########################################################################
#                                                                      #
#                             Tool results                             #
#                                                                      #
########################################################################
# log.debug("Defines a passage as a tool returns it")
class FoundPassage(BaseModel):
    """A passage of an approved source, and how well it matched."""

    # log.debug("Holds the passage's id: its source's id and number")
    id: str
    # log.debug("Holds the id of the source it comes from")
    source_id: str
    # log.debug("Holds the source's title")
    title: str
    # log.debug("Holds the headings the passage sits under")
    section: str
    # log.debug("Holds the passage's text")
    text: str
    # log.debug("Holds the address the source was copied from")
    url: str
    # log.debug("Holds when the publisher last revised the source")
    revised: str
    # log.debug("Holds the search score, when a search found it")
    score: float | None = None

    # log.debug("Defines a passage built from the index")
    @classmethod
    def of(cls, passage: Passage | None = None, score: float | None = None) -> FoundPassage:
        """Returns the passage as a tool returns it.

        Args:
            passage: The indexed passage. Required.
            score: The search score, when a search found it.

        Returns:
            The passage with its source's details.
        """
        # log.debug("Takes the passage, which the caller must give")
        passage = required(passage=passage)
        # log.debug("Returns the passage and its score")
        return cls(
            id=passage.id,
            source_id=passage.doc_id,
            title=passage.title,
            section=passage.section,
            text=passage.text,
            url=passage.url,
            revised=passage.revised,
            score=score,
        )


# log.debug("Defines a source as the listing shows it")
class Listed(BaseModel):
    """An approved source's provenance and status, without its text."""

    # log.debug("Holds the source's id")
    id: str
    # log.debug("Holds the source's title")
    title: str
    # log.debug("Holds who published it")
    publisher: str
    # log.debug("Holds the address it was copied from")
    url: str
    # log.debug("Holds when the publisher last revised it")
    revised: str
    # log.debug("Holds when it was copied")
    retrieved: str
    # log.debug("Holds the SHA-256 of its text, checked at every start")
    sha256: str
    # log.debug("Holds its length in words")
    words: int
    # log.debug("Holds whether the guard held it back from answers")
    held_back: bool
    # log.debug("Holds how many of its lines the guard flagged")
    flagged_lines: int

    # log.debug("Defines a listing built from a stored source")
    @classmethod
    def of(cls, source: Source | None = None) -> Listed:
        """Returns the source's listing.

        Args:
            source: The stored source. Required.

        Returns:
            Its provenance and status, and only the count of any
            flagged lines.
        """
        # log.debug("Takes the source, which the caller must give")
        source = required(source=source)
        # log.debug("Returns the listing")
        return cls(
            id=source.id,
            title=source.title,
            publisher=source.publisher,
            url=source.source,
            revised=source.revised,
            retrieved=source.retrieved,
            sha256=source.sha256,
            words=source.words,
            held_back=bool(source.flagged),
            flagged_lines=len(source.flagged),
        )


# log.debug("Defines a source as one Markdown page")
def page(source: Source | None = None) -> str:
    """Returns the source as Markdown: provenance, then its text.

    A held-back source's page says so in place of its text.

    Args:
        source: The stored source. Required.

    Returns:
        The page.
    """
    # log.debug("Takes the source, which the caller must give")
    source = required(source=source)
    # log.debug("Writes the title and the provenance")
    head = (
        f"# {source.title}\n\n"
        f"Publisher: {source.publisher}  \nSource: {source.source}  \n"
        f"Revised: {source.revised}  \nRetrieved: {source.retrieved}  \n"
        f"SHA-256: {source.sha256}\n\n"
    )
    # log.debug("Ends with the text, or the note that it is held back")
    return head + (HELD_BACK.format(count=len(source.flagged)) if source.flagged else source.body)
