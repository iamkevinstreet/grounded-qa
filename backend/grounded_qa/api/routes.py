########################################################################
#                  backend/grounded_qa/api/routes.py                   #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           The open routes: ask a question, list and read   #
#                     the approved sources, and check health.          #
########################################################################
"""Open routes under /api/v1: health, ask, sources."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from kds.logs import get_logger

from grounded_qa import __version__
from grounded_qa.api.schemas import AskRequest, Health, SourceDetail, SourceSummary
from grounded_qa.api.state import PREFIX, Services, services
from grounded_qa.core.models import Answer
from grounded_qa.core.sources import ID_RE

# Module constants
log = get_logger(__name__)
# log.debug("Creates the router for the open routes")
router = APIRouter(prefix=PREFIX)
# log.debug("Describes the services dependency once, for every route")
Svc = Annotated[Services, Depends(services)]
# log.debug("Describes a source id in a path, checked against the id rule")
SourceId = Annotated[str, Path(pattern=ID_RE.pattern)]
# log.debug("Sets how long a client is told to wait when over the limit")
RETRY_AFTER_S = "60"


# log.debug("Defines the health check")
@router.get("/health")
def health(svc: Svc) -> Health:
    """Report the version, sources, mode and model in use."""
    # log.debug("Takes the approved sources")
    approved = svc.library.approved()
    # log.debug("Returns the health report")
    return Health(
        version=__version__,
        sources=len(approved),
        held_back=sum(bool(s.flagged) for s in approved),
        passages=svc.library.passages,
        mode=svc.library.mode,
        provider=svc.adapter.provider.name,
        model=svc.adapter.model,
        admin=svc.settings.approver_token is not None,
    )


# log.debug("Defines the question route")
@router.post("/ask")
def ask(body: AskRequest, request: Request, svc: Svc) -> Answer:
    """Answer a question from the approved sources, or abstain.

    Raises:
        HTTPException: 422 for a question outside the length limits,
            429 when this client has asked too often.
    """
    # log.debug("Drops control characters and collapses the spacing")
    question = " ".join(
        "".join(c for c in body.question if c.isprintable() or c.isspace()).split()
    )
    # log.debug("Reads the length limits")
    shortest, longest = svc.settings.api_min_question_chars, svc.settings.api_max_question_chars
    # log.debug("Refuses a question outside the limits")
    if not shortest <= len(question) <= longest:
        # log.debug("Raises 422 with the limits")
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"a question is {shortest} to {longest} characters",
        )
    # log.debug("Refuses a client over its per-minute limit")
    if not svc.limiter.allow(request.client.host if request.client else "unknown"):
        # log.debug("Raises 429 with when to retry")
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "too many questions; wait a minute",
            {"Retry-After": RETRY_AFTER_S},
        )
    # log.debug("Returns the checked answer")
    return svc.answerer.ask(question)


# log.debug("Defines the list of sources")
@router.get("/sources")
def list_sources(svc: Svc) -> list[SourceSummary]:
    """List every approved source with its provenance."""
    # log.debug("Returns each source's summary")
    return [SourceSummary.of(s) for s in svc.library.approved()]


# log.debug("Defines one source with its text")
@router.get("/sources/{source_id}")
def get_source(source_id: SourceId, svc: Svc) -> SourceDetail:
    """Return one source with its full text.

    Raises:
        HTTPException: 404 when no source has this id.
    """
    # log.debug("Looks the source up")
    try:
        # log.debug("Returns its detail")
        return SourceDetail.of(svc.library.get(source_id))
    except KeyError:
        # log.debug("Raises 404 for an unknown id")
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no source with that id") from None
