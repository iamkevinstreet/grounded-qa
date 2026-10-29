########################################################################
#                   backend/grounded_qa/api/auth.py                    #
########################################################################
#  Author:            Kevin Street                                     #
#  Created on:        2026-10-29                                       #
#  Last modified on:  2026-10-29                                       #
#  Purpose:           Lets only the approver change sources: a bearer  #
#                     token from .env, compared in constant time.      #
########################################################################
"""The approver check for the routes that change sources.

The token lives in .env as APPROVER_TOKEN (at least 32 characters).
When it is unset the approver routes answer 503, so a fresh clone has
no admin surface at all. The comparison takes the same time however
much of a guess is right, and failures are logged without the token.
"""

from __future__ import annotations

import hmac
import logging
from typing import Annotated

from fastapi import Header, HTTPException, Request, status
from kds.logs import get_logger, log_event

from grounded_qa.config import AppSettings

# Module constants
log = get_logger(__name__)
# log.debug("Sets the scheme an Authorization header must use")
SCHEME = "Bearer "
# log.debug("Sets the header that tells a client how to authenticate")
CHALLENGE = {"WWW-Authenticate": "Bearer"}
# log.debug("Sets the encoding tokens are compared in")
ENCODING = "utf-8"


# log.debug("Defines the dependency every approver route declares")
def require_approver(
    request: Request, authorization: Annotated[str | None, Header()] = None
) -> None:
    """Pass when the request carries the approver's token.

    Raises:
        HTTPException: 503 when admin is off, 401 without a bearer
            token, 403 with the wrong one.
    """
    # log.debug("Reads the settings the app was built with")
    settings: AppSettings = request.app.state.settings
    # log.debug("Refuses every approver route while no token is set")
    if settings.approver_token is None:
        # log.debug("Raises 503: admin is off")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "admin is off: no APPROVER_TOKEN")
    # log.debug("Refuses a request without a bearer token")
    if authorization is None or not authorization.startswith(SCHEME):
        # log.debug("Raises 401 with the challenge header")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "approver token required", CHALLENGE)
    # log.debug("Compares the tokens in constant time")
    if not hmac.compare_digest(
        authorization[len(SCHEME) :].encode(ENCODING),
        settings.approver_token.get_secret_value().encode(ENCODING),
    ):
        # log.debug("Logs the failure, never the token")
        log_event(log, "auth.denied", logging.WARNING, path=request.url.path)
        # log.debug("Raises 403")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "wrong approver token")
