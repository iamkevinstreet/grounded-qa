########################################################################
#                 backend/src/grounded_qa/api/admin.py                 #
########################################################################
"""
Author:            Kevin Street
Created on:        2026-10-29
Last modified on:  2026-10-29

The approver's routes: add or remove a source, and read the audit log
of every change. Every route on this router needs the approver's
token, which the approver check reads first.
"""

########################################################################
#                               Imports                                #
########################################################################
# Standard library
from __future__ import annotations

from typing import Annotated, Final

# Third-party
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from kds.logs import current_request_id, get_logger

# Local
from grounded_qa.api.auth import require_approver
from grounded_qa.api.routes import SourceId, Svc
from grounded_qa.api.schemas import SourceSummary
from grounded_qa.config import SETTINGS
from grounded_qa.core.audit import AuditEntry
from grounded_qa.core.library import NewSource, SourceExistsError
from grounded_qa.core.sources import SourceError

########################################################################
#                           Global constants                           #
########################################################################
log = get_logger(__name__)
# log.debug("Takes the API's path prefix from the config")
PREFIX: Final = SETTINGS.api_prefix
# log.debug("Takes the encoding that turns text into bytes, from the config")
ENCODING: Final = SETTINGS.text_encoding


########################################################################
#                           Approver routes                            #
########################################################################
# log.debug("Creates the router; every route on it needs the approver")
router = APIRouter(prefix=f"{PREFIX}/admin", dependencies=[Depends(require_approver)])


# log.debug("Defines adding a source")
@router.post("/sources", status_code=status.HTTP_201_CREATED)
def add_source(new: NewSource, svc: Svc) -> SourceSummary:
    """Adds a source: checked, guarded, stored, audited and indexed.

    Args:
        new: The source as the approver submitted it.
        svc: The services the app built at startup, from FastAPI.

    Returns:
        The stored source's summary, with its hash and dates.

    Raises:
        HTTPException: 413 when it is too large, 409 when the id is
            taken, 422 when it fails a check or has flagged lines.
    """
    # log.debug("Refuses a document over the size limit")
    if len(new.body.encode(ENCODING)) > svc.settings.api_max_source_bytes:
        # log.debug("Raises 413 with the limit")
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"a source may be at most {svc.settings.api_max_source_bytes} bytes",
        )
    # log.debug("Adds it through the library, which checks everything else")
    try:
        # log.debug("Returns the stored source's summary")
        return SourceSummary.of(svc.library.add(new, current_request_id()))
    except SourceExistsError as error:
        # log.debug("Raises 409 for an id already in use")
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except SourceError as error:
        # log.debug("Raises 422 with what the check found")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error


# log.debug("Defines removing a source")
@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_source(source_id: SourceId, svc: Svc) -> Response:
    """Removes a source: deleted, audited and dropped from the index.

    Args:
        source_id: The id of the source to remove.
        svc: The services the app built at startup, from FastAPI.

    Returns:
        An empty 204 response.

    Raises:
        HTTPException: 404 when no source has this id.
    """
    # log.debug("Removes it through the library")
    try:
        # log.debug("Deletes, audits and reindexes")
        svc.library.remove(source_id, current_request_id())
    except KeyError:
        # log.debug("Raises 404 for an unknown id")
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no source with that id") from None
    # log.debug("Returns an empty 204")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# log.debug("Defines reading the audit log")
@router.get("/audit")
def audit(svc: Svc, limit: Annotated[int, Query(ge=1, le=500)] = 100) -> list[AuditEntry]:
    """Returns the latest changes to the sources, newest first.

    Args:
        svc: The services the app built at startup, from FastAPI.
        limit: The most changes to return, 1 to 500.

    Returns:
        The changes, newest first.
    """
    # log.debug("Returns the entries from the audit log")
    return svc.library.audit.entries(limit)
