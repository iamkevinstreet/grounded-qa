########################################################################
#                backend/src/grounded_qa/core/models.py                #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           The shapes answers take: the model's draft, and  #
#                     the checked answer the service returns.          #
########################################################################
"""Answer shapes: what the model must return, and what we return.

The model's output is parsed into `Draft` before anything uses it.
`Answer` is what the API and the evaluation see: only checked
citations, with the outcome named.
"""

from __future__ import annotations

from typing import Literal

from kds.logs import get_logger
from pydantic import BaseModel, Field

# Module constants
log = get_logger(__name__)
# log.debug("Lists the ways a question can end")
Outcome = Literal["answered", "not_covered", "unverified", "no_passages"]


# log.debug("Defines one citation as the model writes it")
class DraftCitation(BaseModel):
    """A passage id and a quote the model says is in that passage."""

    # log.debug("Holds the id of the passage cited")
    passage_id: str = Field(description="The id attribute of the passage quoted")
    # log.debug("Holds the quote, which must be copied exactly")
    quote: str = Field(description="Words copied exactly from that passage")


# log.debug("Defines the model's whole draft")
class Draft(BaseModel):
    """The model's answer before any check."""

    # log.debug("Holds the answer text, with [n] citation markers")
    answer: str = Field(description="The answer, with [n] after each supported sentence")
    # log.debug("Holds the citations in [n] order")
    citations: list[DraftCitation] = Field(default_factory=list)
    # log.debug("Holds whether the passages fail to answer")
    abstain: bool = Field(description="True when the passages do not answer the question")


# log.debug("Defines one checked citation as the service returns it")
class Citation(BaseModel, frozen=True):
    """A quote checked against its passage, with where it came from."""

    # log.debug("Holds the marker number used in the answer text")
    n: int
    # log.debug("Holds the id of the passage quoted")
    passage_id: str
    # log.debug("Holds the id of the source document")
    doc_id: str
    # log.debug("Holds the source's title")
    title: str
    # log.debug("Holds the heading path of the passage")
    section: str
    # log.debug("Holds the source's URL")
    url: str
    # log.debug("Holds the source's revision date")
    revised: str
    # log.debug("Holds the quote, found word for word in the passage")
    quote: str
    # log.debug("Holds the whole passage, for the reader to check")
    passage: str
    # log.debug("Holds where the quote is in the passage, as character ranges")
    spans: tuple[tuple[int, int], ...] = ()


# log.debug("Defines a passage shown to the model, for the record")
class Retrieved(BaseModel, frozen=True):
    """A passage the model was shown, and its retrieval score."""

    # log.debug("Holds the passage id")
    passage_id: str
    # log.debug("Holds the source id")
    doc_id: str
    # log.debug("Holds the retrieval score")
    score: float


# log.debug("Defines the answer the service returns")
class Answer(BaseModel, frozen=True):
    """A checked answer, or an abstention that says why."""

    # log.debug("Holds the question as asked")
    question: str
    # log.debug("Holds the answer, or why there is none")
    answer: str
    # log.debug("Holds how the question ended")
    outcome: Outcome
    # log.debug("Holds the citations that passed the quote check")
    citations: tuple[Citation, ...] = ()
    # log.debug("Holds how many citations failed the check and were dropped")
    dropped: int = 0
    # log.debug("Holds the passages the model was shown")
    retrieved: tuple[Retrieved, ...] = ()
    # log.debug("Holds the model that drafted it, or none")
    model: str | None = None
    # log.debug("Holds the prompt version")
    prompt_version: str
    # log.debug("Holds the retrieval mode")
    mode: str
    # log.debug("Holds the request id that ties it to the logs")
    request_id: str

    # log.debug("Defines whether this is an abstention")
    @property
    def abstained(self) -> bool:
        """Return True for every outcome but answered."""
        # log.debug("Returns whether it was not answered")
        return self.outcome != "answered"
