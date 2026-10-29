########################################################################
#                backend/src/grounded_qa/api/schemas.py                #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

The shapes of the API's requests and responses, validated at the edge
before the logic sees them.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

from typing import Literal

# Third-party
from kds.args import required
from kds.logs import get_logger
from pydantic import BaseModel, Field

# Local
from grounded_qa.core.sources import Source

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)

########################################################################
#                           Local constants                            #
########################################################################
# log.debug("Sets a hard ceiling on a question before settings apply")
CEILING_CHARS = 10_000
# log.debug("Lists the one status a running service reports")
Status = Literal["ok"]


########################################################################
#                     Request and response bodies                      #
########################################################################
# log.debug("Defines the body of a question")
class AskRequest(BaseModel):
    """A question; the configured length limits are checked on top."""

    # log.debug("Holds the question")
    question: str = Field(min_length=1, max_length=CEILING_CHARS)


# log.debug("Defines a source as the list shows it")
class SourceSummary(BaseModel):
    """A source's provenance and status, without its text."""

    # log.debug("Holds the id")
    id: str
    # log.debug("Holds the title")
    title: str
    # log.debug("Holds the publisher")
    publisher: str
    # log.debug("Holds the address it was published at")
    source: str
    # log.debug("Holds the revision date the publisher states")
    revised: str
    # log.debug("Holds the day it was copied")
    retrieved: str
    # log.debug("Holds the SHA-256 of its text")
    sha256: str
    # log.debug("Holds its length in words")
    words: int
    # log.debug("Holds whether the guard held it back from answers")
    held_back: bool
    # log.debug("Holds the lines that made the guard hold it back")
    flagged: list[str]

    # log.debug("Defines the summary of a stored source")
    @classmethod
    def of(cls, source: Source | None = None) -> SourceSummary:
        """Returns the summary of `source`.

        Args:
            source: The stored source. Required.

        Returns:
            Its provenance and status, without its text.
        """
        # log.debug("Takes the source, which the caller must give")
        source = required(source=source)
        # log.debug("Returns the fields the list shows")
        return cls(
            id=source.id,
            title=source.title,
            publisher=source.publisher,
            source=source.source,
            revised=source.revised,
            retrieved=source.retrieved,
            sha256=source.sha256,
            words=source.words,
            held_back=bool(source.flagged),
            flagged=list(source.flagged),
        )


# log.debug("Defines a source with its text")
class SourceDetail(SourceSummary):
    """A source's provenance, status and full text."""

    # log.debug("Holds the text, as Markdown")
    body: str

    # log.debug("Defines the detail of a stored source")
    @classmethod
    def of(cls, source: Source | None = None) -> SourceDetail:
        """Returns the detail of `source`.

        Args:
            source: The stored source. Required.

        Returns:
            Its provenance, status and full text.
        """
        # log.debug("Takes the source, which the caller must give")
        source = required(source=source)
        # log.debug("Returns the summary fields plus the text")
        return cls(**SourceSummary.of(source).model_dump(), body=source.body)


# log.debug("Defines the health report")
class Health(BaseModel):
    """What the service is running with, for operators and the UI."""

    # log.debug("Holds the status, ok when the service answers")
    status: Status = "ok"
    # log.debug("Holds the service version")
    version: str
    # log.debug("Holds how many sources are approved")
    sources: int
    # log.debug("Holds how many of them the guard held back")
    held_back: int
    # log.debug("Holds how many passages can be searched")
    passages: int
    # log.debug("Holds the retrieval mode")
    mode: str
    # log.debug("Holds the model provider; fake means the offline stand-in")
    provider: str
    # log.debug("Holds the model name")
    model: str
    # log.debug("Holds whether the approver routes are on")
    admin: bool
